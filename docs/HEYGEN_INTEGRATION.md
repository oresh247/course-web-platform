"""
Интеграция HeyGen API в AI Course Builder

Этот файл содержит полное руководство по интеграции HeyGen API для генерации видео-контента по урокам.
"""

# 🎥 Интеграция HeyGen API для генерации видео-контента

## 📋 Обзор интеграции

HeyGen API позволяет создавать AI-аватары и генерировать видео-контент для каждого урока курса. Интеграция включает:

- **Автоматическую генерацию видео** для каждого урока
- **Настройку аватаров и голосов** для персонализации
- **Отслеживание прогресса** генерации видео
- **Скачивание готовых видео** в различных форматах

## 🚀 Быстрый старт

### 1. Получение API ключа HeyGen

1. Зарегистрируйтесь на [HeyGen](https://www.heygen.com/)
2. Перейдите в раздел API в личном кабинете
3. Создайте новый API ключ
4. Сохраните ключ в переменных окружения

```bash
# Добавьте в .env файл
HEYGEN_API_KEY=your_api_key_here
HEYGEN_API_URL=https://api.heygen.com/v1
HEYGEN_DEFAULT_AVATAR_ID=default
HEYGEN_DEFAULT_VOICE_ID=default
```

### 2. Установка зависимостей

```bash
pip install requests python-dotenv
```

### 3. Инициализация сервиса

```python
from backend.services.heygen_service import HeyGenService

# Инициализация сервиса
heygen_service = HeyGenService()

# Создание видео для урока
video_response = heygen_service.create_lesson_video(
    lesson_title="Введение в Python",
    lesson_content="Python - это высокоуровневый язык программирования...",
    avatar_id="default",
    voice_id="default"
)
```

## 🏗️ Архитектура интеграции

### Компоненты системы

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   HeyGen API    │
│                 │    │                  │    │                 │
│ VideoGeneration │◄──►│ VideoGeneration  │◄──►│ Video Creation  │
│ Panel           │    │ Service          │    │ Avatar & Voice  │
│                 │    │                  │    │ Management      │
│ Progress        │    │ Status Tracking  │    │ Download        │
│ Tracking        │    │                  │    │ Management      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Файловая структура

```
backend/
├── services/
│   ├── heygen_service.py           # Основной сервис HeyGen
│   └── video_generation_service.py # Сервис генерации видео
├── routes/
│   └── video_routes.py             # API роуты для видео
├── models/
│   └── video_models.py             # Модели данных для видео
└── requirements.txt                # Обновленные зависимости

frontend/
└── src/
    └── components/
        └── VideoGenerationPanel.jsx # UI компонент для видео
```

## 🔧 API Endpoints

### Основные эндпоинты

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/video/generate-lesson` | Генерация видео для урока |
| POST | `/api/video/generate-course` | Генерация видео для всего курса |
| GET | `/api/video/status/{video_id}` | Проверка статуса видео |
| POST | `/api/video/download/{video_id}` | Скачивание готового видео |
| GET | `/api/video/avatars` | Список доступных аватаров |
| GET | `/api/video/voices` | Список доступных голосов |

### Примеры использования

#### Генерация видео для урока

```javascript
// Frontend
const generateVideo = async (lessonData) => {
  const response = await fetch('/api/video/generate-lesson', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: lessonData.title,
      content: lessonData.content,
      avatar_id: 'default',
      voice_id: 'default',
      language: 'ru'
    })
  });
  
  const result = await response.json();
  return result.data;
};
```

#### Проверка статуса видео

```javascript
// Frontend
const checkVideoStatus = async (videoId) => {
  const response = await fetch(`/api/video/status/${videoId}`);
  const result = await response.json();
  return result.data;
};
```

## 🎨 Настройка аватаров и голосов

### Получение списка аватаров

```python
# Backend
avatars = await heygen_service.get_available_avatars()
print(f"Доступно аватаров: {len(avatars)}")

for avatar in avatars:
    print(f"ID: {avatar['avatar_id']}, Name: {avatar['name']}")
```

### Получение списка голосов

```python
# Backend
voices = await heygen_service.get_available_voices()
print(f"Доступно голосов: {len(voices)}")

for voice in voices:
    print(f"ID: {voice['voice_id']}, Language: {voice['language']}")
```

## 📊 Отслеживание прогресса

### Мониторинг генерации видео

```python
# Backend
async def track_video_progress(video_id):
    while True:
        status = await heygen_service.get_video_status(video_id)
        
        if status['status'] == 'completed':
            print("Видео готово!")
            break
        elif status['status'] == 'failed':
            print("Ошибка генерации видео")
            break
        
        print(f"Прогресс: {status.get('progress', 0)}%")
        await asyncio.sleep(10)  # Проверяем каждые 10 секунд
```

### Frontend компонент отслеживания

```jsx
// Frontend
const VideoProgressTracker = ({ videoId }) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('generating');

  useEffect(() => {
    const interval = setInterval(async () => {
      const statusData = await checkVideoStatus(videoId);
      setProgress(statusData.progress || 0);
      setStatus(statusData.status);
      
      if (statusData.status === 'completed') {
        clearInterval(interval);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [videoId]);

  return (
    <Progress 
      percent={progress} 
      status={status === 'completed' ? 'success' : 'active'} 
    />
  );
};
```

## 💾 Управление файлами

### Скачивание готовых видео

```python
# Backend
async def download_lesson_video(video_id, lesson_title):
    output_path = f"./storage/videos/{lesson_title}_video.mp4"
    
    success = await heygen_service.download_video(video_id, output_path)
    
    if success:
        print(f"Видео сохранено: {output_path}")
        return output_path
    else:
        print("Ошибка при скачивании видео")
        return None
```

### Организация файлов

```
storage/
├── videos/                 # Готовые видео
│   ├── lesson_1_video.mp4
│   ├── lesson_2_video.mp4
│   └── ...
├── temp/                  # Временные файлы
└── thumbnails/            # Превью видео
```

## 🔒 Безопасность и ограничения

### Rate Limiting

```python
# Backend
import time
from functools import wraps

def rate_limit(calls_per_minute=10):
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = 60.0 / calls_per_minute - elapsed
            
            if left_to_wait > 0:
                await asyncio.sleep(left_to_wait)
            
            last_called[0] = time.time()
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

@rate_limit(calls_per_minute=5)
async def create_video_with_rate_limit(lesson_data):
    return await heygen_service.create_lesson_video(lesson_data)
```

### Валидация контента

```python
# Backend
def validate_video_content(content):
    """Валидация контента перед генерацией видео"""
    
    # Проверка длины контента
    if len(content) > 2000:
        raise ValueError("Контент слишком длинный для видео")
    
    # Проверка на недопустимый контент
    forbidden_words = ['spam', 'scam', 'fake']
    if any(word in content.lower() for word in forbidden_words):
        raise ValueError("Контент содержит недопустимые слова")
    
    return True
```

## 🚀 Развертывание

### Переменные окружения

```bash
# .env файл
HEYGEN_API_KEY=your_heygen_api_key
HEYGEN_API_URL=https://api.heygen.com/v1
HEYGEN_DEFAULT_AVATAR_ID=default
HEYGEN_DEFAULT_VOICE_ID=default
HEYGEN_DEFAULT_LANGUAGE=ru

# Настройки видео
VIDEO_QUALITY=high
VIDEO_ASPECT_RATIO=16:9
VIDEO_MAX_DURATION=300
VIDEO_DEFAULT_BACKGROUND=#ffffff

# Хранилище файлов
VIDEO_STORAGE_PATH=./storage/videos
TEMP_STORAGE_PATH=./storage/temp
MAX_FILE_SIZE=100MB
```

### Docker конфигурация

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Создаем директории для хранения видео
RUN mkdir -p storage/videos storage/temp storage/thumbnails

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📈 Мониторинг и аналитика

### Метрики генерации видео

```python
# Backend
import time
from collections import defaultdict

class VideoMetrics:
    def __init__(self):
        self.generation_times = []
        self.success_rate = 0
        self.total_videos = 0
        self.failed_videos = 0
    
    def record_generation(self, start_time, success):
        generation_time = time.time() - start_time
        self.generation_times.append(generation_time)
        self.total_videos += 1
        
        if not success:
            self.failed_videos += 1
        
        self.success_rate = (self.total_videos - self.failed_videos) / self.total_videos
    
    def get_stats(self):
        return {
            'total_videos': self.total_videos,
            'success_rate': self.success_rate,
            'average_generation_time': sum(self.generation_times) / len(self.generation_times),
            'failed_videos': self.failed_videos
        }

# Использование
video_metrics = VideoMetrics()
```

## 🐛 Обработка ошибок

### Типичные ошибки и решения

```python
# Backend
class HeyGenErrorHandler:
    @staticmethod
    def handle_api_error(error):
        """Обработка ошибок HeyGen API"""
        
        if "rate_limit" in str(error).lower():
            return "Превышен лимит запросов. Попробуйте позже."
        elif "invalid_api_key" in str(error).lower():
            return "Неверный API ключ HeyGen."
        elif "insufficient_credits" in str(error).lower():
            return "Недостаточно кредитов HeyGen."
        elif "video_too_long" in str(error).lower():
            return "Видео слишком длинное. Сократите контент."
        else:
            return f"Ошибка HeyGen API: {str(error)}"
    
    @staticmethod
    def handle_generation_error(error):
        """Обработка ошибок генерации"""
        
        if "content_too_long" in str(error).lower():
            return "Контент урока слишком длинный для видео."
        elif "invalid_avatar" in str(error).lower():
            return "Выбранный аватар недоступен."
        elif "invalid_voice" in str(error).lower():
            return "Выбранный голос недоступен."
        else:
            return f"Ошибка генерации: {str(error)}"
```

## 🔄 Интеграция с существующим кодом

### Обновление сервиса генерации

```python
# backend/services/generation_service.py
from .video_generation_service import VideoGenerationService

class EnhancedGenerationService(GenerationService):
    def __init__(self):
        super().__init__()
        self.video_service = VideoGenerationService()
    
    async def generate_lesson_with_video(self, lesson_data):
        """Генерация урока с видео-контентом"""
        
        # 1. Генерируем текстовый контент
        lesson_content = await self.generate_lesson_content(lesson_data)
        
        # 2. Создаем видео
        if lesson_data.get('video_enabled', True):
            video_info = await self.video_service.generate_lesson_with_video(lesson_data)
            lesson_content['video'] = video_info
        
        return lesson_content
```

### Обновление API роутов

```python
# backend/routes/lessons_routes.py
from .video_routes import router as video_router

# Добавляем видео роуты к основному приложению
app.include_router(video_router)
```

## 📚 Дополнительные ресурсы

### Документация HeyGen API

- [Официальная документация](https://docs.heygen.com/)
- [API Reference](https://docs.heygen.com/api-reference)
- [Примеры использования](https://docs.heygen.com/examples)

### Полезные ссылки

- [HeyGen Dashboard](https://app.heygen.com/)
- [Поддержка HeyGen](https://support.heygen.com/)
- [Сообщество разработчиков](https://community.heygen.com/)

## 🎯 Следующие шаги

1. **Тестирование интеграции** - проверьте все API endpoints
2. **Настройка аватаров** - выберите подходящие аватары для курсов
3. **Оптимизация скриптов** - адаптируйте контент для видео-формата
4. **Мониторинг производительности** - отслеживайте время генерации
5. **Масштабирование** - настройте обработку множественных запросов

---

**Примечание**: Убедитесь, что у вас достаточно кредитов HeyGen для генерации видео. Рекомендуется начать с небольшого количества уроков для тестирования.
