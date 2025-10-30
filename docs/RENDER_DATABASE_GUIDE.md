# Подключение к Render PostgreSQL базе данных

## Обзор

Render предоставляет управляемые PostgreSQL базы данных, к которым можно подключаться как из облачных сервисов, так и локально для разработки. Это позволяет использовать одну и ту же базу данных для разработки, тестирования и продакшена.

## 1. Получение строки подключения

### Через Render Dashboard

1. **Войдите в [Render Dashboard](https://dashboard.render.com/)**
2. **Найдите ваш PostgreSQL сервис** в списке сервисов
3. **Перейдите в настройки базы данных** (обычно называется "Database" или "PostgreSQL")
4. **Найдите раздел "External Database URL"** или "Connection String"
5. **Скопируйте строку подключения** - она будет выглядеть так:
   ```
   postgresql://username:password@dpg-xxxxx-a.oregon-postgres.render.com/database_name
   ```

### Через Render CLI (альтернативный способ)

```bash
# Установите Render CLI
npm install -g @render/cli

# Войдите в аккаунт
render login

# Получите информацию о базе данных
render services list
render databases list
```

## 2. Настройка локального подключения

### Создание файла .env

Создайте файл `.env` в корневой директории проекта:

```env
# Render Database Connection
DATABASE_URL=postgresql://username:password@dpg-xxxxx-a.oregon-postgres.render.com/database_name

# Local Development Database (опционально)
LOCAL_DATABASE_URL=sqlite:///./courses.db

# HeyGen API
HEYGEN_API_KEY=your_heygen_api_key
HEYGEN_API_URL=https://api.heygen.com

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# SSL Bypass for corporate networks
PYTHONHTTPSVERIFY=0
CURL_CA_BUNDLE=
REQUESTS_CA_BUNDLE=
```

### Установка зависимостей

Убедитесь, что установлен `psycopg2-binary`:

```bash
pip install psycopg2-binary
```

Или используйте существующий `requirements.txt`:

```bash
pip install -r requirements.txt
```

## 3. Тестирование подключения

Запустите тестовый скрипт:

```bash
cd backend
python test_render_database.py
```

Этот скрипт проверит:
- ✅ Наличие DATABASE_URL в переменных окружения
- ✅ Корректность формата URL
- ✅ Подключение к Render PostgreSQL
- ✅ Создание таблиц
- ✅ Базовые операции (создание, чтение, обновление, удаление)
- ✅ Адаптивную систему выбора базы данных

## 4. Использование в коде

### Адаптивная система

Система автоматически выбирает базу данных:

```python
from database.db_postgres import get_database

# Автоматически выберет PostgreSQL если доступен DATABASE_URL,
# иначе SQLite для локальной разработки
db = get_database()

# Использование одинаково для обеих баз данных
course_id = db.save_course(course_data)
course = db.get_course(course_id)
courses = db.get_all_courses()
```

### Прямое использование PostgreSQL

```python
from database.db_postgres import RenderDatabase

# Прямое подключение к Render PostgreSQL
db = RenderDatabase(os.getenv('DATABASE_URL'))
```

### Прямое использование SQLite

```python
from database.db import CourseDatabase

# Локальная SQLite база данных
db = CourseDatabase("courses.db")
```

## 5. Преимущества Render PostgreSQL

### Производительность
- **Высокая производительность**: Render использует SSD и оптимизированные настройки PostgreSQL
- **Индексы**: Автоматически создаются индексы для улучшения производительности запросов
- **JSONB**: Поддержка JSONB для гибкого хранения структурированных данных

### Надежность
- **Автоматические бэкапы**: Регулярные бэкапы базы данных
- **Высокая доступность**: 99.9% uptime гарантия
- **Мониторинг**: Встроенный мониторинг производительности

### Масштабируемость
- **Горизонтальное масштабирование**: Возможность увеличения ресурсов
- **Вертикальное масштабирование**: Увеличение CPU и RAM
- **Read replicas**: Реплики для чтения для улучшения производительности

## 6. Безопасность

### SSL/TLS
- **Обязательное SSL**: Все соединения должны использовать SSL
- **Сертификаты**: Автоматически управляемые SSL сертификаты

### Аутентификация
- **Пароли**: Сильные пароли генерируются автоматически
- **Ограничение доступа**: Доступ только с разрешенных IP адресов

### Переменные окружения
- **Безопасное хранение**: DATABASE_URL хранится в переменных окружения
- **Не в коде**: Никогда не храните пароли в коде

## 7. Мониторинг и отладка

### Render Dashboard
- **Метрики**: CPU, память, дисковое пространство
- **Логи**: Логи подключений и запросов
- **Алерты**: Уведомления о проблемах

### Локальная отладка
```python
import logging

# Включите подробное логирование
logging.basicConfig(level=logging.DEBUG)

# Проверьте подключение
from database.db_postgres import RenderDatabase
db = RenderDatabase()
print("✅ Подключение к Render PostgreSQL успешно!")
```

## 8. Миграция данных

### Из SQLite в PostgreSQL
```python
# Скрипт миграции данных
from database.db import CourseDatabase as SQLiteDB
from database.db_postgres import RenderDatabase as PostgreSQLDB

# Подключение к обеим базам
sqlite_db = SQLiteDB("courses.db")
postgres_db = PostgreSQLDB(os.getenv('DATABASE_URL'))

# Миграция курсов
courses = sqlite_db.get_all_courses()
for course in courses:
    postgres_db.save_course(course)
    print(f"✅ Мигрирован курс: {course['course_title']}")
```

## 9. Troubleshooting

### Частые проблемы

#### Ошибка подключения
```
psycopg2.OperationalError: could not connect to server
```
**Решение**: Проверьте DATABASE_URL и доступность сервера

#### SSL ошибки
```
psycopg2.OperationalError: SSL connection is required
```
**Решение**: Убедитесь, что используется `sslmode=require`

#### Ошибки аутентификации
```
psycopg2.OperationalError: password authentication failed
```
**Решение**: Проверьте правильность username и password в DATABASE_URL

### Отладка подключения
```python
import psycopg2
from urllib.parse import urlparse

# Парсинг DATABASE_URL
url = urlparse(os.getenv('DATABASE_URL'))
print(f"Host: {url.hostname}")
print(f"Port: {url.port}")
print(f"Database: {url.path[1:]}")
print(f"User: {url.username}")

# Тест подключения
try:
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port,
        database=url.path[1:],
        user=url.username,
        password=url.password,
        sslmode='require'
    )
    print("✅ Подключение успешно!")
    conn.close()
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
```

## 10. Лучшие практики

### Переменные окружения
- ✅ Используйте `.env` файлы для локальной разработки
- ✅ Никогда не коммитьте `.env` файлы в Git
- ✅ Используйте разные DATABASE_URL для разных сред

### Подключения
- ✅ Используйте connection pooling для продакшена
- ✅ Закрывайте соединения после использования
- ✅ Обрабатывайте исключения подключения

### Производительность
- ✅ Используйте индексы для часто запрашиваемых полей
- ✅ Ограничивайте размер результатов запросов
- ✅ Используйте пагинацию для больших наборов данных

### Безопасность
- ✅ Регулярно обновляйте пароли
- ✅ Используйте принцип минимальных привилегий
- ✅ Мониторьте подозрительную активность

## Заключение

Подключение к Render PostgreSQL базе данных позволяет:
- 🚀 Использовать одну базу данных для всех сред
- 🔒 Обеспечить высокую безопасность и надежность
- 📈 Масштабировать приложение по мере роста
- 🛠️ Упростить развертывание и управление

Следуйте этой инструкции для успешного подключения к Render PostgreSQL базе данных!
