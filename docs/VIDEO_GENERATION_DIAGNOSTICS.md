# Диагностика проблемы с неостановкой генерации при ошибках HeyGen

## Проблема

Ошибка уже отображается на сайте HeyGen ([https://app.heygen.com/projects](https://app.heygen.com/projects)), но в браузере генерация продолжает крутиться. Это означает, что наша система не получает актуальный статус от HeyGen API.

## Диагностика

### 1. **Проверка HeyGen API**

**Тест endpoint статуса:**
```bash
cd backend
python test_video_status_debug.py
```

**Результат для несуществующего видео:**
```
Status Code: 404
Response Text: {"code":400569,"message":"ResourceType.PACIFIC_VIDEO not found"}
```

### 2. **Возможные причины**

#### A. **Неправильный video_id**
- Система использует неправильный `video_id`
- `video_id` не соответствует реальному видео в HeyGen

#### B. **Кэширование старого статуса**
- localStorage содержит старый статус
- Браузер не обновляет статус

#### C. **Проблема с интервалом проверки**
- Интервал не очищается при ошибке
- Система продолжает проверять несуществующее видео

#### D. **Проблема с обработкой 404**
- Бэкенд не правильно обрабатывает 404 статус
- Фронтенд не получает информацию об ошибке

## Решение ✅

### 1. **Улучшенная обработка 404 статуса**

**heygen_service.py:**
```python
if response.status_code == 404:
    try:
        error_data = response.json()
        error_message = error_data.get("message", "Видео не найдено в системе HeyGen")
        error_code = error_data.get("code", "404")
    except:
        error_message = "Видео не найдено в системе HeyGen"
        error_code = "404"
    
    logger.warning(f"Видео {video_id} не найдено в HeyGen: {error_message}")
    return {
        "status": "not_found",
        "error": error_message,
        "error_code": error_code,
        "video_id": video_id
    }
```

### 2. **Полная передача данных статуса**

**video_generation_service.py:**
```python
async def check_video_status(self, video_id: str) -> Dict[str, Any]:
    try:
        status = self.heygen_service.get_video_status(video_id)
        
        # Передаем все поля из ответа HeyGen API
        result = {
            'video_id': video_id,
            'status': status.get('status', 'unknown'),
            'progress': status.get('progress', 0),
            'download_url': status.get('download_url'),
            'error': status.get('error'),
            'error_code': status.get('error_code'),
            'error_details': status.get('error_details'),
            'duration': status.get('duration'),
            'file_size': status.get('file_size'),
            'created_at': status.get('created_at'),
            'estimated_time': status.get('estimated_time')
        }
        
        logger.info(f"Статус видео {video_id}: {result['status']}")
        return result
```

### 3. **Детальное логирование в фронтенде**

**VideoGenerationPanel.jsx:**
```javascript
const checkVideoStatus = async (videoId) => {
  try {
    console.log(`🔍 Проверяем статус видео: ${videoId}`);
    const response = await fetch(`${getVideoApiUrl('STATUS')}/${videoId}`);
    const data = await response.json();
    
    console.log(`📊 Ответ API статуса:`, data);
    
    if (data.success) {
      setVideoStatus(data.data);
      return data.data;
    } else {
      console.error(`❌ Ошибка в ответе API статуса:`, data);
      return null;
    }
  } catch (error) {
    console.error('❌ Ошибка проверки статуса:', error);
  }
  return null;
};

const trackVideoProgress = async (videoId) => {
  console.log(`🎬 Начинаем отслеживание прогресса видео: ${videoId}`);
  
  const interval = setInterval(async () => {
    attempts++;
    console.log(`🔄 Попытка ${attempts}/${maxAttempts} для видео ${videoId}`);
    
    try {
      const status = await checkVideoStatus(videoId);
      
      if (status) {
        console.log(`📋 Получен статус:`, status);
        
        // Немедленно останавливаем генерацию при любых ошибках
        if (['failed', 'not_found', 'timeout', 'connection_error', 'api_error', 'unknown_error'].includes(status.status)) {
          console.log(`🛑 Останавливаем генерацию из-за статуса: ${status.status}`);
          clearInterval(interval);
          stopGenerationImmediately(getStatusText(status.status));
          return; // Выходим из функции немедленно
        }
      }
    } catch (error) {
      console.error(`❌ Ошибка при проверке статуса видео ${videoId}:`, error);
    }
  }, 5000);
};
```

### 4. **Кнопка ручной проверки статуса**

**VideoGenerationPanel.jsx:**
```javascript
{videoStatus?.video_id && (
  <Button
    icon={<EyeOutlined />}
    onClick={() => {
      console.log('🔍 Проверяем статус вручную для видео:', videoStatus.video_id);
      checkVideoStatus(videoStatus.video_id);
    }}
    disabled={isGenerating}
  >
    Проверить статус
  </Button>
)}
```

## Инструкции по диагностике

### 1. **Откройте консоль браузера**
- Нажмите F12
- Перейдите на вкладку Console

### 2. **Сгенерируйте видео**
- Откройте `http://localhost:3000/video-test`
- Нажмите "Создать видео"
- Следите за логами в консоли

### 3. **Проверьте логи**
Должны появиться сообщения:
```
🎬 Начинаем отслеживание прогресса видео: [video_id]
🔄 Попытка 1/60 для видео [video_id]
🔍 Проверяем статус видео: [video_id]
📊 Ответ API статуса: {...}
```

### 4. **Если генерация не останавливается**
- Нажмите кнопку "Проверить статус"
- Посмотрите на ответ API в консоли
- Проверьте, какой статус возвращается

### 5. **Проверьте HeyGen Dashboard**
- Откройте [https://app.heygen.com/projects](https://app.heygen.com/projects)
- Найдите ваше видео
- Проверьте его статус

## Типичные проблемы и решения

### Проблема 1: video_id не найден
**Симптомы:**
- Статус 404 в консоли
- Сообщение "ResourceType.PACIFIC_VIDEO not found"

**Решение:**
- Проверьте правильность video_id
- Убедитесь, что видео существует в HeyGen

### Проблема 2: Кэширование старого статуса
**Симптомы:**
- Статус не обновляется
- Показывается старый прогресс

**Решение:**
- Нажмите "Сбросить состояние"
- Очистите localStorage

### Проблема 3: Интервал не очищается
**Симптомы:**
- Генерация продолжается бесконечно
- Логи показывают повторяющиеся попытки

**Решение:**
- Нажмите "Отменить генерацию"
- Проверьте логи на наличие ошибок

## Проверка исправлений

### 1. **Тест с несуществующим video_id**
```bash
cd backend
python test_video_status_debug.py
```

### 2. **Тест в браузере**
- Откройте консоль
- Сгенерируйте видео
- Следите за логами
- Проверьте остановку при ошибке

### 3. **Тест ручной проверки**
- Нажмите "Проверить статус"
- Посмотрите на ответ в консоли
- Убедитесь, что статус корректный

## Заключение

После применения исправлений система должна:

- ✅ **Немедленно останавливать** генерацию при получении 404
- ✅ **Показывать детальные логи** в консоли браузера
- ✅ **Обрабатывать все типы ошибок** HeyGen API
- ✅ **Предоставлять кнопку** ручной проверки статуса

Если проблема сохраняется, проверьте логи в консоли браузера и используйте кнопку "Проверить статус" для диагностики! 🔍
