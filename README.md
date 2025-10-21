# 🎓 AI Course Builder - Web Platform

Веб-платформа для создания IT-курсов с помощью искусственного интеллекта (GPT-4). Современный стек: **FastAPI + React + Ant Design**.

## ✨ Возможности

- 🤖 **AI генерация структуры курса** - автоматическое создание модулей и уроков
- 📚 **Детальный контент** - генерация лекций, слайдов и учебных материалов
- ✏️ **Редактирование в веб-интерфейсе** - удобное редактирование курсов
- 💾 **База данных SQLite** - хранение курсов локально
- 🌐 **Работа через прокси** - поддержка корпоративных прокси для OpenAI API
- 📱 **Современный UI** - адаптивный интерфейс на Ant Design

## 🏗️ Архитектура проекта

```
course-web-platform/
├── backend/                    # FastAPI Backend
│   ├── ai/                     # AI модули (OpenAI, промпты)
│   │   ├── prompts.py         # Промпты для GPT
│   │   ├── openai_client.py   # Клиент OpenAI с прокси
│   │   └── content_generator.py
│   ├── models/                 # Pydantic модели
│   │   └── domain.py
│   ├── api/                    # REST API endpoints
│   │   └── courses.py
│   ├── database/               # SQLite база данных
│   │   └── db.py
│   ├── main.py                # Точка входа FastAPI
│   └── requirements.txt
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # React компоненты
│   │   ├── pages/             # Страницы
│   │   ├── api/               # API клиент
│   │   └── styles/            # CSS стили
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 🚀 Быстрый старт

> **🌐 Хотите развернуть в облаке?** См. [RENDER_QUICKSTART.md](./RENDER_QUICKSTART.md) для развертывания на Render.com за 5 минут!

### Предварительные требования

- Python 3.9+
- Node.js 18+
- OpenAI API ключ

### 1️⃣ Настройка Backend (FastAPI)

```bash
# Переходим в директорию backend
cd backend

# Создаем виртуальное окружение
python -m venv venv

# Активируем (Windows)
venv\Scripts\activate

# Устанавливаем зависимости
pip install -r requirements.txt

# Создаем .env файл
copy env.example .env

# Редактируем .env и добавляем ваш OpenAI API ключ
# OPENAI_API_KEY=sk-your-key-here
```

### 2️⃣ Настройка Frontend (React)

```bash
# Переходим в директорию frontend
cd frontend

# Устанавливаем зависимости
npm install
```

### 3️⃣ Запуск приложения

**Терминал 1 - Backend:**
```bash
cd backend
venv\Scripts\activate
python main.py
```

Backend будет доступен на: http://localhost:8000
- API документация: http://localhost:8000/api/docs

**Терминал 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Frontend будет доступен на: http://localhost:3000

## 🔧 Конфигурация

### Backend (.env)

```env
# OpenAI API
OPENAI_API_KEY=sk-your-key-here

# Прокси (опционально, для корпоративных сетей)
HTTP_PROXY=http://your-proxy:port
HTTPS_PROXY=http://your-proxy:port

# База данных
DATABASE_PATH=courses.db

# Сервер
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

### Работа через прокси

Если вы работаете в корпоративной сети с прокси:

1. Раскомментируйте строки `HTTP_PROXY` и `HTTPS_PROXY` в `.env`
2. Укажите адрес вашего прокси-сервера
3. SSL сертификаты автоматически отключаются для работы через прокси

## 📖 Использование

### Создание курса

1. Откройте http://localhost:3000
2. Нажмите "Создать курс"
3. Заполните параметры:
   - Тема курса (например: "Python для начинающих")
   - Уровень аудитории (Junior/Middle/Senior)
   - Количество модулей (2-10)
   - Длительность в неделях
4. Нажмите "Создать курс с помощью AI"
5. Подождите 20-30 секунд, пока AI создаст структуру

### Редактирование курса

1. Откройте созданный курс из списка "Мои курсы"
2. Просмотрите модули и уроки
3. Нажмите "Редактировать курс" для изменения
4. Сохраните изменения

### Генерация детального контента

1. Откройте курс
2. Раскройте нужный модуль
3. Нажмите "Сгенерировать детальный контент"
4. AI создаст лекции со слайдами для модуля

## 🔌 API Endpoints

### Курсы

- `POST /api/courses/` - Создать курс
- `GET /api/courses/` - Получить список курсов
- `GET /api/courses/{id}` - Получить курс по ID
- `PUT /api/courses/{id}` - Обновить курс
- `DELETE /api/courses/{id}` - Удалить курс

### Контент модулей

- `POST /api/courses/{id}/modules/{module_number}/generate` - Сгенерировать контент
- `GET /api/courses/{id}/modules/{module_number}/content` - Получить контент модуля

### Документация

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 🎨 Технологии

### Backend
- **FastAPI** - современный веб-фреймворк
- **Pydantic** - валидация данных
- **OpenAI API** - генерация контента с GPT-4
- **SQLite** - локальная база данных
- **httpx** - HTTP клиент с поддержкой прокси

### Frontend
- **React 18** - UI библиотека
- **Vite** - быстрый сборщик
- **Ant Design** - UI компоненты
- **React Router** - маршрутизация
- **Axios** - HTTP клиент

## 🔄 Переиспользование кода

Этот проект переиспользует AI функционал из TGBotCreateCourse:

✅ **Промпты** (`backend/ai/prompts.py`) - все шаблоны для GPT
✅ **OpenAI клиент** (`backend/ai/openai_client.py`) - с поддержкой прокси
✅ **Генератор контента** (`backend/ai/content_generator.py`)
✅ **Модели данных** (`backend/models/domain.py`)
✅ **SSL Fix** - для корпоративных сетей

## 📝 Различия с Telegram ботом

| Функция | Telegram Бот | Web Platform |
|---------|--------------|--------------|
| Интерфейс | Telegram чат | Веб-браузер |
| Редактирование | Команды бота | Формы и редакторы |
| Хранение | Сессии в памяти | SQLite БД |
| Экспорт | Файлы в Telegram | Скачивание файлов (скоро) |
| Мультипользователь | Да | Нет (локальная версия) |

## 🛠️ Разработка

### Backend разработка

```bash
cd backend
venv\Scripts\activate

# Запуск с автоперезагрузкой
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend разработка

```bash
cd frontend

# Разработка
npm run dev

# Сборка для production
npm run build

# Preview production сборки
npm run preview
```

## 🐛 Решение проблем

### OpenAI API не работает

1. Проверьте, что ваш API ключ действителен
2. Убедитесь, что у вас есть баланс на аккаунте OpenAI
3. Проверьте настройки прокси, если используете корпоративную сеть

### CORS ошибки

1. Убедитесь, что backend запущен на порту 8000
2. Frontend должен быть на порту 3000
3. Проверьте настройки CORS в `backend/main.py`

### База данных

База данных SQLite создается автоматически при первом запуске.
Файл: `backend/courses.db`

Для сброса базы - просто удалите файл `courses.db`.

## 🌐 Развертывание

### Render.com (Рекомендуется)

Самый простой способ развернуть приложение в облаке:

- ⚡ **Быстрый старт**: [RENDER_QUICKSTART.md](./RENDER_QUICKSTART.md) - развертывание за 5 минут
- 📖 **Полная инструкция**: [DEPLOY.md](./DEPLOY.md) - детальное руководство с troubleshooting

**Free план включает:**
- ✅ Автоматическое развертывание из GitHub
- ✅ SSL сертификаты
- ✅ Автоматические обновления при push
- ✅ 750 часов работы в месяц

### Другие платформы

Проект также можно развернуть на:
- **Vercel** (Frontend) + **Railway** (Backend)
- **Netlify** (Frontend) + **Heroku** (Backend)
- **AWS** / **Google Cloud** / **Azure**
- **Docker** - см. `.dockerignore`

## 📄 Лицензия

MIT License

## 🤝 Поддержка

Если у вас возникли вопросы или проблемы:
1. Проверьте документацию выше
2. Посмотрите логи backend и frontend
3. Проверьте раздел "Решение проблем"
4. Для развертывания см. [DEPLOY.md](./DEPLOY.md)

---

**Создано с использованием AI (GPT-4) 🤖**

