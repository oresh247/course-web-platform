# 🔑 Переменные окружения для Render.com

## Backend Service (`course-builder-api`)

Добавьте эти переменные в Environment Variables на Render Dashboard:

### Обязательные

```env
OPENAI_API_KEY=sk-your-openai-key-here
```
**Где получить:** https://platform.openai.com/api-keys

### Автоматические (уже настроены в render.yaml)

```env
PYTHONUNBUFFERED=1
PYTHON_VERSION=3.11.0
PORT=10000
```

### Опциональные

```env
# CORS настройки (для продакшн замените * на конкретный домен)
ALLOWED_ORIGINS=*

# PostgreSQL (рекомендуется для продакшн)
# DATABASE_URL=postgresql://user:password@host:5432/dbname
```

---

## Frontend Service (`course-builder-frontend`)

### Автоматические (настраиваются Render)

```env
NODE_VERSION=18.18.0
VITE_API_URL=https://course-builder-api.onrender.com
```

**Примечание:** `VITE_API_URL` будет автоматически установлен Render при использовании Blueprint (render.yaml).

---

## ⚠️ Важно

1. **OPENAI_API_KEY** - единственная переменная, которую нужно добавить вручную
2. Все остальное настраивается автоматически через `render.yaml`
3. Для продакшн используйте PostgreSQL вместо SQLite
4. Ограничьте CORS только вашим доменом в продакшн

---

## 🔄 Как обновить переменные

1. Откройте Dashboard → Ваш сервис
2. Перейдите в раздел "Environment"
3. Нажмите "Add Environment Variable"
4. Введите Key и Value
5. Нажмите "Save Changes"
6. Сервис автоматически перезапустится

