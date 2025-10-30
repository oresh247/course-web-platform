# Диагностика проблемы генерации видео

## Проблема

При выполнении команды "Генерировать видео" на форме генерации видео для урока "История Java" генерация прерывалась со статусом "Неизвестно".

## Диагностика

### **1. Проверка API endpoints**
- ✅ Backend работает корректно
- ✅ Endpoint `/api/video/generate-lesson` доступен
- ✅ Endpoint `/api/video/status/{video_id}` доступен

### **2. Анализ процесса генерации**
- ✅ Видео успешно создается (получаем `video_id`)
- ❌ При проверке статуса возвращается `status: "unknown"`

### **3. Прямое обращение к HeyGen API**

Создан тестовый скрипт для проверки прямого обращения к HeyGen API:

```python
# Тест: test_heygen_direct.py
video_id = "2e6c51c2ec9340be95977ee44af35863"
url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
```

**Результат:**
```json
{
  "code": 100,
  "data": {
    "status": "failed",
    "error": {
      "code": "RESOLUTION_NOT_ALLOWED",
      "message": "Please subscribe to higher plan to generate higher resolution videos"
    }
  }
}
```

## Корень проблемы

**HeyGen API возвращает ошибку `RESOLUTION_NOT_ALLOWED`** - это означает, что текущий план HeyGen не позволяет генерировать видео высокого разрешения.

## Решение ✅

### **1. Изменение качества видео по умолчанию**

В `backend/services/heygen_service.py` изменено значение по умолчанию:

```python
# Было:
quality: str = "high",

# Стало:
quality: str = "low",
```

### **2. Проверка использования низкого качества**

В `backend/services/video_generation_service.py` уже используется:

```python
'quality': lesson_data.get('quality', 'low'),
```

### **3. Тестирование с низким качеством**

Создан тестовый скрипт `test_video_low_quality.py` с явным указанием:

```python
payload = {
    "title": "История Java",
    "content": test_script,
    "avatar_id": avatar_id,
    "voice_id": voice_id,
    "language": "ru",
    "quality": "low"  # Явно указываем низкое качество
}
```

## Технические детали

### **Структура payload для HeyGen API:**

```json
{
  "video_inputs": [...],
  "dimension": {
    "width": 1920,  // high quality
    "height": 1080  // high quality
  },
  "quality": "high"  // ← Проблема здесь
}
```

**Исправлено на:**

```json
{
  "video_inputs": [...],
  "dimension": {
    "width": 1280,  // low quality
    "height": 720   // low quality
  },
  "quality": "low"   // ← Решение
}
```

### **Обработка ошибок в коде:**

```python
# В HeyGenService.get_video_status()
if result.get("status") == "failed":
    error_details = result.get("error", {})
    return {
        "status": "failed",
        "error": error_details.get("message", "Неизвестная ошибка генерации"),
        "error_code": error_details.get("code", "unknown"),
        "error_details": error_details,
        "video_id": video_id
    }
```

## Результат

### **До исправления:**
- ❌ Генерация видео прерывалась со статусом "Неизвестно"
- ❌ HeyGen API возвращал `RESOLUTION_NOT_ALLOWED`
- ❌ Пользователь не получал информацию об ошибке

### **После исправления:**
- ✅ Видео генерируется с низким качеством (1280x720)
- ✅ Обход ограничений плана HeyGen
- ✅ Корректная обработка ошибок
- ✅ Информативные сообщения пользователю

## Рекомендации

### **1. Для пользователей:**
- Видео будут генерироваться с разрешением 1280x720 вместо 1920x1080
- Это не влияет на качество контента, только на разрешение

### **2. Для разработчиков:**
- При необходимости высокого качества можно передать `quality: "high"` в запросе
- Для этого потребуется подписка на более высокий план HeyGen

### **3. Мониторинг:**
- Следить за ошибками `RESOLUTION_NOT_ALLOWED` в логах
- При появлении таких ошибок проверять настройки качества

## Заключение

Проблема была успешно диагностирована и решена! Изменение качества видео по умолчанию с `"high"` на `"low"` позволяет обойти ограничения плана HeyGen и обеспечивает стабильную генерацию видео. 🚀
