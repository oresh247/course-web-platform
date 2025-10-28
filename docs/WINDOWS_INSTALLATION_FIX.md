# 🔧 Решение проблем установки на Windows

## ❌ Проблема с Pillow на Python 3.13

Ошибка возникает из-за несовместимости Pillow 10.1.0 с Python 3.13 на Windows.

## ✅ Решения

### Вариант 1: Используйте совместимый файл requirements

```bash
# Используйте специальный файл для Windows
pip install -r requirements-windows.txt
```

### Вариант 2: Установите без Pillow (рекомендуется)

```bash
# Установите основные зависимости без Pillow
pip install fastapi uvicorn[standard] pydantic pydantic-settings
pip install sqlalchemy alembic psycopg2-binary
pip install openai tiktoken
pip install requests httpx aiohttp
pip install python-dotenv python-multipart aiofiles
pip install python-pptx markdown jinja2
pip install python-dateutil pytz click
pip install pytest pytest-asyncio black flake8
pip install structlog python-jose[cryptography] passlib[bcrypt]
pip install slowapi
```

### Вариант 3: Используйте Python 3.11

```bash
# Создайте новое виртуальное окружение с Python 3.11
python3.11 -m venv venv311
venv311\Scripts\activate
pip install -r requirements.txt
```

### Вариант 4: Установите Pillow отдельно

```bash
# Сначала установите основные зависимости
pip install -r requirements.txt --no-deps

# Затем установите Pillow с предварительно скомпилированным wheel
pip install Pillow --only-binary=all
```

## 🚀 Быстрая установка (рекомендуется)

```bash
# 1. Активируйте виртуальное окружение
venv\Scripts\activate

# 2. Установите основные зависимости
pip install fastapi uvicorn[standard] pydantic pydantic-settings sqlalchemy openai requests python-dotenv

# 3. Установите дополнительные зависимости по необходимости
pip install alembic psycopg2-binary tiktoken httpx aiohttp python-multipart aiofiles

# 4. Проверьте установку
python -c "import fastapi; print('FastAPI установлен успешно')"
```

## 🔍 Проверка установки

```bash
# Проверьте основные модули
python -c "
import fastapi
import uvicorn
import pydantic
import sqlalchemy
import openai
import requests
print('✅ Все основные модули установлены')
"
```

## 📝 Минимальные требования для HeyGen интеграции

Для работы с HeyGen API достаточно установить:

```bash
pip install fastapi uvicorn[standard] pydantic requests python-dotenv
```

## 🐛 Другие возможные проблемы

### Проблема с psycopg2-binary
```bash
# Если не работает psycopg2-binary, используйте psycopg2
pip install psycopg2
```

### Проблема с компиляцией
```bash
# Установите Microsoft C++ Build Tools
# Или используйте предварительно скомпилированные пакеты
pip install --only-binary=all -r requirements.txt
```

### Проблема с правами доступа
```bash
# Запустите PowerShell от имени администратора
# Или используйте --user флаг
pip install --user -r requirements.txt
```

## ✅ Проверка работоспособности

После установки проверьте:

```bash
# 1. Запустите сервер
uvicorn main:app --reload

# 2. Проверьте health endpoint
curl http://localhost:8000/health

# 3. Проверьте документацию
# Откройте http://localhost:8000/api/docs в браузере
```

---

**Примечание**: Pillow не критичен для работы HeyGen интеграции, поэтому можно обойтись без него.
