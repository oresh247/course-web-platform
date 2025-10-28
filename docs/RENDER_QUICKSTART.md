# ⚡ Быстрый старт на Render.com

## 🎯 За 5 минут

### 1️⃣ Подготовка (1 мин)

```bash
# Загрузите проект в GitHub
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### 2️⃣ Создание сервисов на Render (3 мин)

1. Откройте https://dashboard.render.com/
2. Нажмите **"New +"** → **"Blueprint"**
3. Выберите ваш репозиторий
4. Render найдет `render.yaml` автоматически

### 3️⃣ Настройка (1 мин)

**Важно!** Добавьте переменную окружения для Backend:

```
OPENAI_API_KEY=ваш_ключ_от_openai
```

Получить ключ: https://platform.openai.com/api-keys

### 4️⃣ Запуск

Нажмите **"Apply"** и ждите ~5-10 минут.

## 🎉 Готово!

После развертывания:
- **Backend API**: `https://course-builder-api.onrender.com`
- **Frontend**: `https://course-builder-frontend.onrender.com`

## 📝 Что дальше?

- Полная инструкция: см. [DEPLOY.md](./DEPLOY.md)
- Для продакшн: настройте PostgreSQL базу данных
- Free план: сервис "засыпает" после 15 мин неактивности

## ⚠️ Важно

**SQLite на Free плане:**
- Данные не сохраняются при перезапуске
- Для продакшн используйте PostgreSQL (см. DEPLOY.md)

---

Нужна помощь? → [Render Community](https://community.render.com/)

