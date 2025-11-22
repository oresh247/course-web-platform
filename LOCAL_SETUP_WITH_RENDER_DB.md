# Локальный запуск с подключением к базе данных Render

## 📋 Шаг 1: Получение DATABASE_URL из Render

1. Зайдите в [Render Dashboard](https://dashboard.render.com)
2. Выберите ваш **PostgreSQL** сервис (не веб-сервис!)
3. В разделе **"Connections"** найдите:
   - **External Database URL** (для подключения с вашего компьютера)
4. Скопируйте URL (формат: `postgresql://user:password@host:port/dbname`)

## 🔧 Шаг 2: Настройка Backend

### Windows PowerShell:

```powershell
# Перейдите в директорию backend
cd backend

# Создайте виртуальное окружение (если еще не создано)
python -m venv venv

# Активируйте виртуальное окружение
.\venv\Scripts\Activate.ps1

# Установите зависимости (если еще не установлены)
pip install -r requirements.txt

# Создайте .env файл из примера
copy env.example .env

# Откройте .env файл и добавьте:
# DATABASE_URL=postgresql://user:password@host:port/dbname
# OPENAI_API_KEY=your_openai_api_key_here
```

**Или установите переменные окружения напрямую:**

```powershell
# Установите DATABASE_URL
$env:DATABASE_URL='postgresql://user:password@host:port/dbname'

# Установите OPENAI_API_KEY
$env:OPENAI_API_KEY='your_openai_api_key_here'

# Запустите бэкенд
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Windows CMD:

```cmd
cd backend
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
copy env.example .env

REM Отредактируйте .env файл и добавьте DATABASE_URL

REM Или установите переменные окружения:
set DATABASE_URL=postgresql://user:password@host:port/dbname
set OPENAI_API_KEY=your_openai_api_key_here

REM Запустите бэкенд
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Linux/Mac:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env

# Отредактируйте .env файл и добавьте DATABASE_URL

# Или установите переменные окружения:
export DATABASE_URL='postgresql://user:password@host:port/dbname'
export OPENAI_API_KEY='your_openai_api_key_here'

# Запустите бэкенд
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🎨 Шаг 3: Настройка Frontend

### Windows PowerShell/CMD:

```powershell
# Перейдите в директорию frontend
cd frontend

# Установите зависимости (если еще не установлены)
npm install

# Запустите dev сервер
npm run dev
```

### Linux/Mac:

```bash
cd frontend
npm install
npm run dev
```

## ✅ Шаг 4: Проверка подключения

1. **Backend** должен быть доступен на: `http://localhost:8000`
   - API документация: `http://localhost:8000/api/docs`
   - Health check: `http://localhost:8000/health`

2. **Frontend** должен быть доступен на: `http://localhost:3000` (или другой порт, который покажет Vite)

3. **Проверьте подключение к базе:**
   - В логах бэкенда должно быть: `🐘 Используется PostgreSQL`
   - Если видите `📁 Используется SQLite` - проверьте, что `DATABASE_URL` установлен правильно

## 🔍 Проверка подключения к базе данных

### Способ 1: Через скрипт

```powershell
# Установите DATABASE_URL
$env:DATABASE_URL='postgresql://...'

# Проверьте подключение
python backend/tools/check_course_api_response.py 12
```

### Способ 2: Через API

Откройте в браузере: `http://localhost:8000/api/courses/12`

Должен вернуться JSON с данными курса.

## ⚠️ Важные моменты

1. **DATABASE_URL должен быть External Database URL** (не Internal!)
   - Internal URL работает только внутри сети Render
   - External URL работает извне

2. **Безопасность:**
   - НЕ коммитьте `.env` файл в Git
   - НЕ публикуйте DATABASE_URL

3. **Если не работает:**
   - Проверьте, что PostgreSQL сервис запущен на Render
   - Проверьте, что используете External Database URL
   - Проверьте логи бэкенда на наличие ошибок подключения

## 📝 Пример .env файла

```env
# Database (Render PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/dbname

# OpenAI API
OPENAI_API_KEY=sk-your-openai-key-here

# HeyGen API (optional)
HEYGEN_API_KEY=your-heygen-key-here

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

## 🚀 Быстрый старт (одной командой)

### Windows PowerShell:

```powershell
# Терминал 1 - Backend
cd backend
$env:DATABASE_URL='postgresql://...'
$env:OPENAI_API_KEY='sk-...'
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Терминал 2 - Frontend
cd frontend
npm run dev
```

### Linux/Mac:

```bash
# Терминал 1 - Backend
cd backend
export DATABASE_URL='postgresql://...'
export OPENAI_API_KEY='sk-...'
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Терминал 2 - Frontend
cd frontend
npm run dev
```

