# 🚀 Установка и запуск AI Course Builder с HeyGen интеграцией

## 📋 Предварительные требования

- Python 3.11+
- Node.js 18+
- PostgreSQL (для продакшена) или SQLite (для разработки)
- API ключ HeyGen

## 🔧 Установка Backend

### 1. Перейдите в папку backend
```bash
cd backend
```

### 2. Создайте виртуальное окружение
```bash
python -m venv venv
```

### 3. Активируйте виртуальное окружение

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Установите зависимости
```bash
pip install -r requirements.txt
```

### 5. Настройте переменные окружения
Скопируйте `env.example` в `.env` и заполните:
```bash
cp env.example .env
```

Отредактируйте `.env`:
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# HeyGen Configuration
HEYGEN_API_KEY=your_heygen_api_key_here
HEYGEN_API_URL=https://api.heygen.com/v1
HEYGEN_DEFAULT_AVATAR_ID=default
HEYGEN_DEFAULT_VOICE_ID=default

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/course_platform
# или для SQLite:
# SQLITE_DB_PATH=courses.db
```

### 6. Запустите сервер
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🎨 Установка Frontend

### 1. Перейдите в папку frontend
```bash
cd frontend
```

### 2. Установите зависимости
```bash
npm install
```

### 3. Запустите dev сервер
```bash
npm run dev
```

## 🎥 Настройка HeyGen

### 1. Получите API ключ
1. Зарегистрируйтесь на [HeyGen](https://www.heygen.com/)
2. Перейдите в раздел API
3. Создайте новый API ключ
4. Добавьте ключ в `.env` файл

### 2. Проверьте доступные аватары и голоса
```bash
curl -X GET "http://localhost:8000/api/video/avatars" \
  -H "X-API-KEY: your_heygen_api_key"

curl -X GET "http://localhost:8000/api/video/voices" \
  -H "X-API-KEY: your_heygen_api_key"
```

## 🧪 Тестирование интеграции

### 1. Проверьте здоровье сервиса
```bash
curl http://localhost:8000/api/video/health
```

### 2. Создайте тестовое видео
```bash
curl -X POST "http://localhost:8000/api/video/generate-lesson" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Тестовый урок",
    "content": "Это тестовый контент для проверки генерации видео.",
    "avatar_id": "default",
    "voice_id": "default",
    "language": "ru"
  }'
```

## 🐛 Решение проблем

### Ошибка "Could not open requirements file"
**Решение:** Убедитесь, что вы находитесь в папке `backend` при выполнении команды `pip install -r requirements.txt`

### Ошибка HeyGen API
**Возможные причины:**
- Неверный API ключ
- Превышен лимит запросов
- Недостаточно кредитов

**Решение:**
1. Проверьте API ключ в `.env`
2. Проверьте баланс на HeyGen
3. Убедитесь в правильности URL API

### Ошибки импорта модулей
**Решение:**
1. Убедитесь, что виртуальное окружение активировано
2. Переустановите зависимости: `pip install -r requirements.txt --force-reinstall`

## 📊 Мониторинг

### Логи приложения
```bash
tail -f logs/app.log
```

### Метрики API
```bash
curl http://localhost:8000/metrics
```

## 🚀 Продакшен деплой

### 1. Настройте переменные окружения
```bash
export OPENAI_API_KEY="your_production_key"
export HEYGEN_API_KEY="your_production_key"
export DATABASE_URL="postgresql://user:pass@host:port/db"
```

### 2. Запустите с Gunicorn
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 3. Настройте Nginx (опционально)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📚 Дополнительные ресурсы

- [Документация HeyGen API](https://docs.heygen.com/)
- [FastAPI документация](https://fastapi.tiangolo.com/)
- [React документация](https://react.dev/)

---

**Примечание:** Убедитесь, что у вас достаточно кредитов HeyGen для генерации видео. Рекомендуется начать с тестовых запросов.
