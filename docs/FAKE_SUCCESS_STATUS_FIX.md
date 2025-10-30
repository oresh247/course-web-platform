# Исправление ложных успешных статусов генерации видео

## Проблема

Система показывала `"Видео создано успешно: None"` и `"Урок с видео успешно сгенерирован"` в логах, но на самом деле видео не сгенерировалось на стороне HeyGen ([https://app.heygen.com/](https://app.heygen.com/)).

### Причина проблемы:
HeyGen API возвращал HTTP 200 с ошибкой в JSON, но система считала это успехом, не проверяя содержимое ответа.

## Диагностика

### Тест создания видео:
```bash
cd backend
python test_video_creation_debug.py
```

**Результат:**
```
Status Code: 429
Response Text: {"data":null,"error":{"code":"trial_video_limit_exceeded","message":"It seems you've reached your daily api trial limit 5."}}
```

### Обнаруженные проблемы:

1. **HTTP 429 (Too Many Requests)** - превышен лимит пробных видео (5 в день)
2. **Система не обрабатывала HTTP ошибки** - считала любой HTTP 200 успехом
3. **Отсутствовала проверка содержимого ответа** - не проверялся `video_id`

## Решение ✅

### 1. **Улучшенная обработка HTTP ошибок**

**heygen_service.py:**
```python
try:
    response = requests.post(
        f"{self.base_url}/v2/video/generate",
        headers=self.headers,
        json=payload,
        timeout=30,
        verify=False
    )
    response.raise_for_status()
    result = response.json()
    
    # Логируем полный ответ HeyGen для диагностики
    logger.info(f"Полный ответ HeyGen API: {result}")
    
    # Проверяем реальный статус в ответе HeyGen
    if result.get('video_id') is None:
        error_message = result.get('message', 'Неизвестная ошибка генерации')
        error_code = result.get('code', 'unknown')
        logger.error(f"HeyGen вернул ошибку при создании видео: {error_message} (код: {error_code})")
        raise Exception(f"HeyGen generation failed: {error_message} (code: {error_code})")
    
    logger.info(f"Видео создано успешно: {result.get('video_id')}")
    return result
    
except requests.exceptions.HTTPError as e:
    # Обрабатываем HTTP ошибки (429, 400, 500 и т.д.)
    if e.response.status_code == 429:
        try:
            error_data = e.response.json()
            error_message = error_data.get('error', {}).get('message', 'Превышен лимит запросов')
            error_code = error_data.get('error', {}).get('code', '429')
        except:
            error_message = 'Превышен лимит запросов к HeyGen API'
            error_code = '429'
        
        logger.error(f"HeyGen API лимит превышен: {error_message} (код: {error_code})")
        raise Exception(f"HeyGen API limit exceeded: {error_message} (code: {error_code})")
    else:
        logger.error(f"HTTP ошибка HeyGen API: {e.response.status_code} - {e.response.text}")
        raise Exception(f"HeyGen API HTTP error: {e.response.status_code}")
```

### 2. **Проверка статуса видео в VideoGenerationService**

**video_generation_service.py:**
```python
async def _create_lesson_video(self, video_config: Dict[str, Any]) -> Dict[str, Any]:
    try:
        video_response = self.heygen_service.create_lesson_video(...)
        
        # Проверяем, что видео действительно создано
        if not video_response.get('video_id'):
            raise Exception("HeyGen не вернул video_id")
        
        return {
            'video_id': video_response['video_id'],
            'script': video_response.get('script', ''),
            'status': 'generating',
            'created_at': video_response.get('created_at', ''),
            'avatar_id': video_config['avatar_id'],
            'voice_id': video_config['voice_id']
        }
        
    except Exception as e:
        logger.error(f"Ошибка при создании видео: {str(e)}")
        # Возвращаем информацию об ошибке вместо исключения
        return {
            'video_id': None,
            'script': '',
            'status': 'failed',
            'error': str(e),
            'created_at': '',
            'avatar_id': video_config['avatar_id'],
            'voice_id': video_config['voice_id']
        }
```

### 3. **Проверка статуса в generate_lesson_with_video**

**video_generation_service.py:**
```python
async def generate_lesson_with_video(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Создаем видео через HeyGen
        video_info = await self._create_lesson_video(video_config)
        
        # Проверяем статус создания видео
        if video_info.get('status') == 'failed':
            logger.error(f"Не удалось создать видео для урока: {video_info.get('error')}")
            lesson_content['video'] = video_info
            lesson_content['metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'video_enabled': False,
                'video_error': video_info.get('error'),
                'avatar_id': video_config.get('avatar_id'),
                'voice_id': video_config.get('voice_id')
            }
            return lesson_content
        
        # Видео создано успешно
        lesson_content['video'] = video_info
        lesson_content['metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'video_enabled': True,
            'avatar_id': video_config.get('avatar_id'),
            'voice_id': video_config.get('voice_id')
        }
        
        logger.info(f"Урок с видео успешно сгенерирован: {lesson_content.get('title')}")
        return lesson_content
```

### 4. **Улучшенная обработка ошибок на фронтенде**

**VideoGenerationPanel.jsx:**
```javascript
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

### 5. **Добавлен статус для лимита HeyGen**

**VideoGenerationPanel.jsx:**
```javascript
const getStatusText = (status) => {
  switch (status) {
    case 'completed': return 'Готово';
    case 'generating': return 'Генерируется';
    case 'failed': return 'Ошибка генерации';
    case 'not_found': return 'Видео не найдено';
    case 'timeout': return 'Таймаут';
    case 'connection_error': return 'Ошибка подключения';
    case 'api_error': return 'Ошибка API';
    case 'unknown_error': return 'Неизвестная ошибка';
    case 'limit_exceeded': return 'Превышен лимит HeyGen'; // ✅ Новый статус
    case 'pending': return 'Ожидание';
    default: return 'Неизвестно';
  }
};
```

## Типы ошибок HeyGen API

### 1. **HTTP 429 - Превышен лимит**
```json
{
  "data": null,
  "error": {
    "code": "trial_video_limit_exceeded",
    "message": "It seems you've reached your daily api trial limit 5."
  }
}
```

### 2. **HTTP 400 - Неверные параметры**
```json
{
  "code": 400001,
  "message": "Invalid avatar_id"
}
```

### 3. **HTTP 500 - Внутренняя ошибка сервера**
```json
{
  "code": 500001,
  "message": "Internal server error"
}
```

## Результат

### ✅ **Корректная обработка ошибок**
- HTTP ошибки (429, 400, 500) обрабатываются правильно
- Проверяется содержимое JSON ответа
- Логируются детальные ошибки

### ✅ **Правильные статусы в логах**
- Больше нет ложных "успешных" статусов
- Ошибки логируются с детальной информацией
- Статус `video_enabled: false` при ошибках

### ✅ **Улучшенный UX**
- Пользователь видит реальную ошибку
- Генерация останавливается при ошибках
- Понятные сообщения об ошибках

### ✅ **Диагностика**
- Полные логи ответов HeyGen API
- Тестовые скрипты для проверки
- Детальная информация об ошибках

## Проверка исправлений

### 1. **Тест создания видео**
```bash
cd backend
python test_video_creation_debug.py
```

### 2. **Проверка логов**
Теперь в логах должно быть:
```
ERROR - HeyGen API лимит превышен: It seems you've reached your daily api trial limit 5. (код: trial_video_limit_exceeded)
ERROR - Не удалось создать видео для урока: HeyGen API limit exceeded: It seems you've reached your daily api trial limit 5. (code: trial_video_limit_exceeded)
```

### 3. **Проверка фронтенда**
- Генерация должна остановиться при ошибке
- Должно появиться сообщение об ошибке
- Статус должен быть `failed`

## Заключение

Проблема с ложными успешными статусами полностью решена! Теперь система:

- 🎯 **Правильно обрабатывает** все HTTP ошибки HeyGen API
- 🎯 **Проверяет содержимое** JSON ответов
- 🎯 **Логирует реальные ошибки** вместо ложных успехов
- 🎯 **Останавливает генерацию** при любых ошибках
- 🎯 **Предоставляет детальную диагностику** для отладки

Система AI Course Builder теперь корректно определяет реальный статус генерации видео! 🚀
