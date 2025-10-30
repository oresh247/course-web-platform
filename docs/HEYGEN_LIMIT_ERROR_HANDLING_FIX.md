# Исправление обработки ошибок лимита HeyGen API

## Проблема

Система показывала общую ошибку `"Ошибка генерации: HeyGen generation failed: Неизвестная ошибка генерации (code: unknown)"` вместо конкретного сообщения о превышении лимита, и не останавливала генерацию.

### Причина проблемы:
1. **Неправильный порядок обработки исключений** - HTTP ошибки обрабатывались как общие RequestException
2. **Отсутствие проверки HTTP статуса** перед парсингом JSON
3. **Недостаточная обработка ошибок** на фронтенде

## Диагностика

### Тест обработки ошибок:
```bash
cd backend
python test_error_handling.py
```

**Результат:**
```
HTTP Status Code: 429
Response Text: {"data":null,"error":{"code":"trial_video_limit_exceeded","message":"It seems you've reached your daily api trial limit 5."}}

Ошибка лимита обработана корректно:
   Сообщение: It seems you've reached your daily api trial limit 5.
   Код: trial_video_limit_exceeded

Наш сервис должен вернуть:
   Exception: HeyGen API limit exceeded: It seems you've reached your daily api trial limit 5. (code: trial_video_limit_exceeded)
   HTTP Status: 429
   Message: Превышен лимит HeyGen API (5 видео в день). Попробуйте завтра.
```

## Решение ✅

### 1. **Исправлена обработка HTTP ошибок в HeyGenService**

**heygen_service.py:**
```python
try:
    logger.info(f"Создание видео с аватаром {avatar_id} и голосом {voice_id}")
    response = requests.post(
        f"{self.base_url}/v2/video/generate",
        headers=self.headers,
        json=payload,
        timeout=30,
        verify=False
    )
    
    # Логируем статус ответа для диагностики
    logger.info(f"HTTP статус ответа HeyGen: {response.status_code}")
    
    # Проверяем HTTP статус перед парсингом JSON
    if response.status_code == 429:
        try:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'Превышен лимит запросов')
            error_code = error_data.get('error', {}).get('code', '429')
        except:
            error_message = 'Превышен лимит запросов к HeyGen API'
            error_code = '429'
        
        logger.error(f"HeyGen API лимит превышен: {error_message} (код: {error_code})")
        raise Exception(f"HeyGen API limit exceeded: {error_message} (code: {error_code})")
    
    response.raise_for_status()
    result = response.json()
    
    # Проверяем реальный статус в ответе HeyGen
    if result.get('video_id') is None:
        error_message = result.get('message', 'Неизвестная ошибка генерации')
        error_code = result.get('code', 'unknown')
        logger.error(f"HeyGen вернул ошибку при создании видео: {error_message} (код: {error_code})")
        raise Exception(f"HeyGen generation failed: {error_message} (code: {error_code})")
    
    logger.info(f"Видео создано успешно: {result.get('video_id')}")
    return result
    
except requests.exceptions.HTTPError as e:
    # Обрабатываем HTTP ошибки (400, 500 и т.д.)
    logger.error(f"HTTP ошибка HeyGen API: {e.response.status_code} - {e.response.text}")
    raise Exception(f"HeyGen API HTTP error: {e.response.status_code}")
        
except requests.exceptions.RequestException as e:
    logger.error(f"Ошибка HeyGen API при создании видео: {str(e)}")
    raise Exception(f"HeyGen API error: {str(e)}")
```

### 2. **Улучшена обработка ошибок в API endpoint**

**video_routes.py:**
```python
except Exception as e:
    logger.error(f"Ошибка при генерации урока с видео: {str(e)}")
    
    # Определяем тип ошибки и возвращаем соответствующий статус
    error_message = str(e)
    if "HeyGen API limit exceeded" in error_message:
        raise HTTPException(
            status_code=429, 
            detail="Превышен лимит HeyGen API (5 видео в день). Попробуйте завтра."
        )
    elif "HeyGen generation failed" in error_message:
        raise HTTPException(
            status_code=400, 
            detail=f"Ошибка генерации HeyGen: {error_message}"
        )
    elif "HeyGen API HTTP error" in error_message:
        raise HTTPException(
            status_code=502, 
            detail=f"Ошибка HeyGen API: {error_message}"
        )
    else:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации видео: {error_message}")
```

### 3. **Улучшена обработка ошибок на фронтенде**

**VideoGenerationPanel.jsx:**
```javascript
const response = await fetch(getVideoApiUrl('GENERATE_LESSON'), {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    title: lesson.title,
    content: lesson.content,
    avatar_id: selectedAvatar,
    voice_id: selectedVoice,
    language: 'ru'
  }),
  signal: abortController.signal
});

const data = await response.json();

// Проверяем HTTP статус ответа
if (!response.ok) {
  const errorMessage = data.detail || data.message || `HTTP ${response.status}: ${response.statusText}`;
  console.error(`HTTP ошибка ${response.status}:`, errorMessage);
  message.error(errorMessage);
  setIsGenerating(false);
  setProgress(0);
  clearVideoStatus();
  return;
}

if (data.success) {
  // Проверяем статус видео в ответе
  if (data.data.video && data.data.video.status === 'failed') {
    const errorMsg = data.data.video.error || 'Ошибка генерации видео';
    message.error(`Ошибка генерации: ${errorMsg}`);
    setIsGenerating(false);
    setProgress(0);
    clearVideoStatus();
  } else {
    message.success('Видео поставлено в очередь генерации');
    setVideoStatus(data.data.video);
    saveVideoStatus(data.data.video);
    
    if (data.data.video.video_id) {
      trackVideoProgress(data.data.video.video_id);
    }
    
    onVideoGenerated?.(data.data);
  }
}
```

### 4. **Детальная обработка ошибок в catch блоке**

**VideoGenerationPanel.jsx:**
```javascript
} catch (error) {
  if (error.name === 'AbortError') {
    message.warning('Генерация видео отменена');
  } else {
    console.error('Ошибка генерации видео:', error);
    
    // Пытаемся получить детальную информацию об ошибке
    let errorMessage = 'Ошибка при генерации видео';
    try {
      if (error.message && error.message.includes('HeyGen API limit exceeded')) {
        errorMessage = 'Превышен лимит HeyGen API (5 видео в день). Попробуйте завтра.';
      } else if (error.message && error.message.includes('HeyGen generation failed')) {
        errorMessage = `Ошибка HeyGen: ${error.message}`;
      } else if (error.message) {
        errorMessage = error.message;
      }
    } catch (e) {
      console.error('Ошибка при обработке сообщения об ошибке:', e);
    }
    
    message.error(errorMessage);
    setIsGenerating(false);
    setProgress(0);
    clearVideoStatus();
  }
}
```

## Результат

### ✅ **Корректные сообщения об ошибках**
**Вместо:**
```
Ошибка генерации: HeyGen generation failed: Неизвестная ошибка генерации (code: unknown)
```

**Теперь:**
```
Превышен лимит HeyGen API (5 видео в день). Попробуйте завтра.
```

### ✅ **Правильная остановка генерации**
- Генерация останавливается при получении HTTP 429
- Состояние сбрасывается (`setIsGenerating(false)`, `setProgress(0)`)
- localStorage очищается (`clearVideoStatus()`)

### ✅ **Детальные логи**
```
INFO - HTTP статус ответа HeyGen: 429
ERROR - HeyGen API лимит превышен: It seems you've reached your daily api trial limit 5. (код: trial_video_limit_exceeded)
ERROR - Ошибка при генерации урока с видео: HeyGen API limit exceeded: It seems you've reached your daily api trial limit 5. (code: trial_video_limit_exceeded)
```

### ✅ **Правильные HTTP статусы**
- 429 для превышения лимита
- 400 для ошибок генерации
- 502 для ошибок API
- 500 для общих ошибок

## Проверка исправлений

### 1. **Тест обработки ошибок**
```bash
cd backend
python test_error_handling.py
```

### 2. **Проверка в браузере**
- Откройте `http://localhost:3000/video-test`
- Попробуйте сгенерировать видео
- Должно появиться сообщение: "Превышен лимит HeyGen API (5 видео в день). Попробуйте завтра."
- Генерация должна остановиться

### 3. **Проверка логов**
В логах бэкенда должно быть:
```
INFO - HTTP статус ответа HeyGen: 429
ERROR - HeyGen API лимит превышен: It seems you've reached your daily api trial limit 5. (код: trial_video_limit_exceeded)
```

## Заключение

Проблема с обработкой ошибок лимита HeyGen API полностью решена! Теперь система:

- 🎯 **Показывает правильные сообщения** об ошибках лимита
- 🎯 **Останавливает генерацию** при получении ошибок
- 🎯 **Обрабатывает HTTP статусы** корректно
- 🎯 **Предоставляет детальные логи** для диагностики
- 🎯 **Возвращает правильные HTTP статусы** (429 для лимита)

Система AI Course Builder теперь корректно обрабатывает все типы ошибок HeyGen API! 🚀
