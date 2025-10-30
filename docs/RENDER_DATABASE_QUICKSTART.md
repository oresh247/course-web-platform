# Краткая инструкция по подключению к Render PostgreSQL

## Что нужно сделать

### 1. Получить DATABASE_URL из Render Dashboard

1. Войдите в [Render Dashboard](https://dashboard.render.com/)
2. Найдите ваш PostgreSQL сервис
3. Перейдите в настройки базы данных
4. Скопируйте "External Database URL" - он выглядит так:
   ```
   postgresql://username:password@dpg-xxxxx-a.oregon-postgres.render.com/database_name
   ```

### 2. Настроить переменные окружения

Создайте файл `.env` в корневой директории проекта:

```env
DATABASE_URL=postgresql://username:password@dpg-xxxxx-a.oregon-postgres.render.com/database_name
```

### 3. Протестировать подключение

```bash
python backend/test_render_database.py
```

## Что происходит сейчас

- ✅ **Локальная SQLite**: Работает отлично для разработки
- ✅ **Адаптивная система**: Автоматически выбирает SQLite (так как нет DATABASE_URL)
- ⏳ **Render PostgreSQL**: Готов к использованию, нужно только добавить DATABASE_URL

## Преимущества Render PostgreSQL

- 🚀 **Высокая производительность**: SSD + оптимизированные настройки
- 🔒 **Безопасность**: SSL, автоматические бэкапы
- 📈 **Масштабируемость**: Легко увеличить ресурсы
- 🌐 **Доступность**: 99.9% uptime гарантия

## Как использовать

После настройки DATABASE_URL система автоматически переключится на PostgreSQL:

```python
from database.db_postgres import get_database

# Автоматически выберет PostgreSQL если доступен DATABASE_URL
db = get_database()

# Использование одинаково для обеих баз данных
course_id = db.save_course(course_data)
course = db.get_course(course_id)
```

## Troubleshooting

### Ошибка подключения
```
psycopg2.OperationalError: could not connect to server
```
**Решение**: Проверьте DATABASE_URL и доступность сервера

### SSL ошибки
```
psycopg2.OperationalError: SSL connection is required
```
**Решение**: Убедитесь, что используется `sslmode=require`

### Ошибки аутентификации
```
psycopg2.OperationalError: password authentication failed
```
**Решение**: Проверьте правильность username и password в DATABASE_URL

## Заключение

Система готова к работе с Render PostgreSQL! Просто добавьте DATABASE_URL и перезапустите приложение.
