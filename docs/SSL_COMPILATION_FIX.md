# 🔧 Решение проблем SSL и компиляции на Windows

## ❌ Проблемы

1. **SSL Certificate Error** - проблема с корпоративными сертификатами
2. **Rust Compilation Error** - pydantic-core требует компиляции Rust
3. **Python 3.13 Compatibility** - некоторые пакеты не совместимы

## ✅ Решения

### Вариант 1: Минимальная установка (рекомендуется)

```bash
# Установите только необходимые пакеты
pip install -r requirements-minimal.txt
```

### Вариант 2: Обход SSL проблем

```bash
# Отключите проверку SSL (только для разработки!)
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements-minimal.txt
```

### Вариант 3: Использование предварительно скомпилированных пакетов

```bash
# Установите только wheel пакеты (без компиляции)
pip install --only-binary=all fastapi uvicorn[standard] pydantic requests python-dotenv
```

### Вариант 4: Установка по одному пакету

```bash
# Установите пакеты по одному для выявления проблемного
pip install fastapi
pip install uvicorn[standard]
pip install pydantic
pip install requests
pip install python-dotenv
```

## 🚀 Быстрый тест HeyGen интеграции

После установки минимальных зависимостей:

```bash
# 1. Создайте простой тест
python -c "
import fastapi
import uvicorn
import pydantic
import requests
import os
from dotenv import load_dotenv
print('✅ Все модули установлены успешно')
"
```

### Простой тест HeyGen API

```python
# test_heygen.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_heygen_api():
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        print("❌ HEYGEN_API_KEY не найден в .env")
        return
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        # Тест получения аватаров
        response = requests.get(
            'https://api.heygen.com/v1/avatar.list',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ HeyGen API работает!")
            print(f"Доступно аватаров: {len(response.json().get('data', []))}")
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    test_heygen_api()
```

## 🔧 Настройка корпоративной сети

### Обход SSL для разработки

```bash
# Установите переменные окружения
set PYTHONHTTPSVERIFY=0
set CURL_CA_BUNDLE=
set REQUESTS_CA_BUNDLE=

# Или добавьте в .env файл
echo "PYTHONHTTPSVERIFY=0" >> .env
echo "CURL_CA_BUNDLE=" >> .env
echo "REQUESTS_CA_BUNDLE=" >> .env
```

### Использование корпоративного прокси

```bash
# Если есть корпоративный прокси
pip install --proxy http://proxy.company.com:8080 -r requirements-minimal.txt
```

## 🎯 Минимальная рабочая конфигурация

### 1. Установите только необходимое

```bash
pip install fastapi uvicorn[standard] pydantic requests python-dotenv
```

### 2. Создайте простой main.py

```python
# simple_main.py
from fastapi import FastAPI
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Course Builder - Minimal")

@app.get("/")
async def root():
    return {"message": "AI Course Builder работает!"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "heygen_configured": bool(os.getenv("HEYGEN_API_KEY"))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. Запустите сервер

```bash
python simple_main.py
```

### 4. Проверьте работу

```bash
curl http://localhost:8000/health
```

## 📝 Альтернативные решения

### Использование Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements-minimal.txt .
RUN pip install -r requirements-minimal.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Использование conda

```bash
# Создайте conda окружение
conda create -n course-builder python=3.11
conda activate course-builder

# Установите пакеты через conda
conda install -c conda-forge fastapi uvicorn pydantic requests python-dotenv
```

## ✅ Проверка работоспособности

После установки проверьте:

```bash
# 1. Импорт модулей
python -c "import fastapi, uvicorn, pydantic, requests; print('✅ Все модули работают')"

# 2. Запуск сервера
uvicorn main:app --reload

# 3. Проверка API
curl http://localhost:8000/health
```

---

**Примечание**: Минимальная конфигурация позволяет протестировать HeyGen интеграцию без сложных зависимостей.
