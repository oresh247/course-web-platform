# Исправление структуры ответа HeyGen API

## Проблема

Система показывала ошибку `"HeyGen generation failed: Неизвестная ошибка генерации (code: unknown)"` даже при успешном создании видео, потому что неправильно обрабатывала структуру ответа HeyGen API.

### Причина проблемы:
HeyGen API изменил структуру ответа с:
```json
{
  "video_id": "c97f571975a5401e8b31cb465a6e2dbe"
}
```

На:
```json
{
  "error": null,
  "data": {
    "video_id": "c97f571975a5401e8b31cb465a6e2dbe"
  }
}
```

## Диагностика

### Логи показывали:
```
INFO - HTTP статус ответа HeyGen: 200
INFO - Полный ответ HeyGen API: {'error': None, 'data': {'video_id': 'c97f571975a5401e8b31cb465a6e2dbe'}}
ERROR - HeyGen вернул ошибку при создании видео: Неизвестная ошибка генерации (код: unknown)
ERROR - Полный ответ с ошибкой: {'error': None, 'data': {'video_id': 'c97f571975a5401e8b31cb465a6e2dbe'}}
```

### Проблема:
Система искала `video_id` в корне ответа (`result.get('video_id')`), но он находился в `result['data']['video_id']`.

## Решение ✅

### 1. **Исправлена обработка структуры ответа HeyGen**

**heygen_service.py:**
```python
response.raise_for_status()
result = response.json()

# Логируем полный ответ HeyGen для диагностики
logger.info(f"Полный ответ HeyGen API: {result}")

# Проверяем структуру ответа HeyGen
video_id = None
if result.get('data') and result['data'].get('video_id'):
    # Новая структура: {"data": {"video_id": "..."}}
    video_id = result['data']['video_id']
elif result.get('video_id'):
    # Старая структура: {"video_id": "..."}
    video_id = result['video_id']

# Проверяем реальный статус в ответе HeyGen
if video_id is None:
    error_message = result.get('message', 'Неизвестная ошибка генерации')
    error_code = result.get('code', 'unknown')
    logger.error(f"HeyGen вернул ошибку при создании видео: {error_message} (код: {error_code})")
    logger.error(f"Полный ответ с ошибкой: {result}")
    raise Exception(f"HeyGen generation failed: {error_message} (code: {error_code})")

logger.info(f"Видео создано успешно: {video_id}")

# Возвращаем результат в стандартном формате
return {
    'video_id': video_id,
    'script': result.get('data', {}).get('script', ''),
    'created_at': result.get('data', {}).get('created_at', ''),
    'status': result.get('data', {}).get('status', 'generating')
}
```

### 2. **Обновлен тестовый скрипт**

**test_error_handling.py:**
```python
elif response.status_code == 200:
    try:
        data = response.json()
        
        # Проверяем структуру ответа HeyGen
        video_id = None
        if data.get('data') and data['data'].get('video_id'):
            # Новая структура: {"data": {"video_id": "..."}}
            video_id = data['data']['video_id']
        elif data.get('video_id'):
            # Старая структура: {"video_id": "..."}
            video_id = data['video_id']
        
        if video_id:
            print(f"\nВидео создано успешно: {video_id}")
            print(f"   Структура ответа: {data}")
        else:
            print(f"\nОшибка: video_id отсутствует")
            print(f"   Данные: {data}")
    except Exception as e:
        print(f"Ошибка парсинга JSON: {e}")
```

## Структуры ответов HeyGen API

### 1. **Новая структура (текущая)**
```json
{
  "error": null,
  "data": {
    "video_id": "c97f571975a5401e8b31cb465a6e2dbe",
    "script": "Текст для озвучивания",
    "created_at": "2025-10-28T20:27:40Z",
    "status": "generating"
  }
}
```

### 2. **Старая структура (для совместимости)**
```json
{
  "video_id": "c97f571975a5401e8b31cb465a6e2dbe",
  "script": "Текст для озвучивания",
  "created_at": "2025-10-28T20:27:40Z",
  "status": "generating"
}
```

### 3. **Структура ошибки**
```json
{
  "error": {
    "code": "trial_video_limit_exceeded",
    "message": "It seems you've reached your daily api trial limit 5."
  },
  "data": null
}
```

## Результат

### ✅ **Корректная обработка успешных ответов**
**Вместо:**
```
ERROR - HeyGen вернул ошибку при создании видео: Неизвестная ошибка генерации (код: unknown)
```

**Теперь:**
```
INFO - Видео создано успешно: c97f571975a5401e8b31cb465a6e2dbe
```

### ✅ **Поддержка обеих структур**
- Новая структура: `result['data']['video_id']`
- Старая структура: `result['video_id']`
- Автоматическое определение структуры

### ✅ **Стандартизированный возврат**
```python
return {
    'video_id': video_id,
    'script': result.get('data', {}).get('script', ''),
    'created_at': result.get('data', {}).get('created_at', ''),
    'status': result.get('data', {}).get('status', 'generating')
}
```

### ✅ **Обратная совместимость**
Система работает с обеими структурами ответов HeyGen API.

## Проверка исправлений

### 1. **Тест структуры ответа**
```bash
cd backend
python test_error_handling.py
```

### 2. **Проверка в браузере**
- Откройте `http://localhost:3000/video-test`
- Попробуйте сгенерировать видео
- Должно появиться сообщение: "Видео поставлено в очередь генерации"
- В логах должно быть: "Видео создано успешно: [video_id]"

### 3. **Проверка логов**
В логах бэкенда должно быть:
```
INFO - HTTP статус ответа HeyGen: 200
INFO - Полный ответ HeyGen API: {'error': None, 'data': {'video_id': 'c97f571975a5401e8b31cb465a6e2dbe'}}
INFO - Видео создано успешно: c97f571975a5401e8b31cb465a6e2dbe
```

## Заключение

Проблема со структурой ответа HeyGen API полностью решена! Теперь система:

- 🎯 **Правильно обрабатывает** новую структуру ответа HeyGen
- 🎯 **Поддерживает обратную совместимость** со старой структурой
- 🎯 **Автоматически определяет** структуру ответа
- 🎯 **Возвращает стандартизированный** результат
- 🎯 **Не показывает ложные ошибки** при успешном создании видео

Система AI Course Builder теперь корректно работает с актуальной версией HeyGen API! 🚀
