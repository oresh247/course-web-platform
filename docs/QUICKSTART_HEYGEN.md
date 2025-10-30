# 🚀 Быстрый запуск AI Course Builder с HeyGen

## ⚡ Установка за 5 минут

### 1. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Настройка .env
```bash
# Скопируйте env.example в .env
cp env.example .env

# Добавьте ваши API ключи:
OPENAI_API_KEY=your_openai_key
HEYGEN_API_KEY=your_heygen_key
```

### 3. Запуск
```bash
# Backend
uvicorn main:app --reload

# Frontend (в новом терминале)
cd frontend
npm install
npm run dev
```

## 🎥 Тестирование HeyGen

### Проверка API
```bash
curl http://localhost:8000/api/video/health
```

### Создание тестового видео
```bash
curl -X POST "http://localhost:8000/api/video/generate-lesson" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Тест",
    "content": "Привет! Это тестовое видео.",
    "avatar_id": "default",
    "voice_id": "default"
  }'
```

## 📚 Доступные endpoints

- **API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health
- **Video Health**: http://localhost:8000/api/video/health
- **Avatars**: http://localhost:8000/api/video/avatars
- **Voices**: http://localhost:8000/api/video/voices

## 🔧 Решение проблем

### Ошибка requirements.txt
```bash
# Убедитесь, что вы в папке backend
cd backend
pip install -r requirements.txt
```

### Ошибка HeyGen API
- Проверьте API ключ в .env
- Убедитесь в наличии кредитов на HeyGen
- Проверьте интернет-соединение

### Ошибки импорта
```bash
# Переустановите зависимости
pip install -r requirements.txt --force-reinstall
```

---

**Готово!** 🎉 Теперь у вас есть полнофункциональный AI Course Builder с поддержкой генерации видео через HeyGen API.
