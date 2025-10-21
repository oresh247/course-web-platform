# 🚀 Развертывание на Render.com

Пошаговая инструкция по развертыванию AI Course Builder Platform на Render.com.

## 📋 Предварительные требования

1. Аккаунт на [Render.com](https://dashboard.render.com/)
2. Репозиторий GitHub с кодом проекта
3. API ключ OpenAI

## 🔧 Подготовка проекта

### 1. Убедитесь, что все файлы на месте

Проект должен содержать следующие файлы:

- ✅ `render.yaml` - конфигурация сервисов Render
- ✅ `build.sh` - скрипт сборки backend
- ✅ `backend/requirements.txt` - зависимости Python
- ✅ `frontend/package.json` - зависимости Node.js
- ✅ `backend/env.example` - пример переменных окружения

### 2. Загрузите код в GitHub

```bash
git init
git add .
git commit -m "Initial commit for Render deployment"
git remote add origin https://github.com/ваш-username/ваш-репозиторий.git
git push -u origin main
```

## 🌐 Развертывание на Render.com

### Способ 1: Автоматическое развертывание через render.yaml (Рекомендуется)

1. **Войдите в Render Dashboard**
   - Перейдите на https://dashboard.render.com/
   - Авторизуйтесь через GitHub

2. **Создайте новый Blueprint**
   - Нажмите кнопку "New +" → "Blueprint"
   - Выберите ваш GitHub репозиторий
   - Render автоматически обнаружит `render.yaml`

3. **Настройте переменные окружения**
   
   Для Backend сервиса (`course-builder-api`):
   - `OPENAI_API_KEY` - ваш API ключ OpenAI (обязательно!)
   - `PYTHONUNBUFFERED=1` - уже настроено
   - `PORT` - уже настроено

4. **Запустите развертывание**
   - Нажмите "Apply"
   - Дождитесь завершения сборки (5-10 минут)

### Способ 2: Ручное создание сервисов

#### Backend API

1. **Создайте Web Service**
   - New + → Web Service
   - Подключите GitHub репозиторий
   - Настройки:
     - **Name**: `course-builder-api`
     - **Region**: Frankfurt (или ближайший)
     - **Branch**: `main`
     - **Root Directory**: оставьте пустым
     - **Environment**: `Python 3`
     - **Build Command**: `./build.sh`
     - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
     - **Plan**: Free

2. **Добавьте переменные окружения**:
   ```
   OPENAI_API_KEY=ваш_ключ_openai
   PYTHONUNBUFFERED=1
   ```

3. **Создайте сервис**

#### Frontend

1. **Создайте Static Site**
   - New + → Static Site
   - Подключите тот же GitHub репозиторий
   - Настройки:
     - **Name**: `course-builder-frontend`
     - **Region**: Frankfurt
     - **Branch**: `main`
     - **Root Directory**: оставьте пустым
     - **Build Command**: `cd frontend && npm install && npm run build`
     - **Publish Directory**: `frontend/dist`

2. **Добавьте переменную окружения**:
   ```
   VITE_API_URL=https://ваш-backend-url.onrender.com
   ```
   (Замените на реальный URL вашего backend после его создания)

3. **Настройте Rewrite Rules**
   - В настройках Static Site найдите "Redirects/Rewrites"
   - Добавьте правило:
     - **Source**: `/*`
     - **Destination**: `/index.html`
     - **Action**: `Rewrite`

## 🔑 Получение OpenAI API ключа

1. Перейдите на https://platform.openai.com/
2. Войдите в аккаунт
3. Перейдите в раздел "API keys"
4. Создайте новый ключ
5. Скопируйте и сохраните его (он показывается только один раз!)

## ✅ Проверка развертывания

После успешного развертывания:

1. **Backend API** будет доступен по адресу:
   ```
   https://course-builder-api.onrender.com
   ```
   
   Проверьте здоровье: `/health`
   ```
   https://course-builder-api.onrender.com/health
   ```

2. **Frontend** будет доступен по адресу:
   ```
   https://course-builder-frontend.onrender.com
   ```

## 🔄 Автоматические обновления

После первоначального развертывания:
- Каждый push в ветку `main` автоматически запускает новую сборку
- Backend перезапускается автоматически
- Frontend пересобирается автоматически

## ⚠️ Важные замечания

### База данных

**Текущая конфигурация использует SQLite:**
- ✅ Простая настройка
- ❌ Данные НЕ персистентны на Free плане Render
- ❌ При перезапуске сервиса данные теряются

**Для продакшн рекомендуется PostgreSQL:**

1. **Создайте PostgreSQL Database на Render**:
   - New + → PostgreSQL
   - Выберите Free план
   - Скопируйте Internal Database URL

2. **Обновите backend для работы с PostgreSQL**:
   ```bash
   pip install psycopg2-binary sqlalchemy
   ```

3. **Добавьте переменную окружения**:
   ```
   DATABASE_URL=postgresql://...
   ```

### Free Plan ограничения

- Сервисы "засыпают" после 15 минут неактивности
- Первый запрос после пробуждения занимает ~30 секунд
- 750 часов работы в месяц (достаточно для одного сервиса)

Для постоянной доступности рассмотрите платный план.

## 🐛 Troubleshooting

### Backend не запускается

1. Проверьте логи в Render Dashboard
2. Убедитесь, что `OPENAI_API_KEY` установлен
3. Проверьте, что `build.sh` имеет права на выполнение

### Frontend не подключается к Backend

1. Проверьте переменную `VITE_API_URL` во Frontend
2. Убедитесь, что указан правильный URL backend
3. Проверьте CORS настройки в `backend/main.py`

### Ошибки при сборке

1. **Python**: проверьте версию в `render.yaml` (должна быть 3.11+)
2. **Node.js**: проверьте версию (должна быть 18+)
3. **Зависимости**: убедитесь, что все файлы requirements.txt и package.json актуальны

## 📊 Мониторинг

В Render Dashboard вы можете:
- Просматривать логи в реальном времени
- Мониторить использование ресурсов
- Настраивать алерты
- Просматривать метрики производительности

## 🔐 Безопасность

1. **Никогда не коммитьте `.env` файлы**
2. **Используйте Secret переменные окружения** для чувствительных данных
3. **Ограничьте CORS** для продакшн (замените `*` на конкретные домены)
4. **Регулярно обновляйте зависимости**

## 💰 Стоимость

**Free Plan включает:**
- Static Sites: неограниченно
- Web Services: 750 часов/месяц
- PostgreSQL: 90 дней бесплатно
- 100 GB пропускной способности

Для коммерческого использования рассмотрите Starter план ($7/месяц за сервис).

## 📚 Дополнительные ресурсы

- [Render Documentation](https://render.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)
- [OpenAI API Docs](https://platform.openai.com/docs)

## 🆘 Поддержка

Если возникли проблемы:
1. Проверьте логи в Render Dashboard
2. Обратитесь к [Render Community](https://community.render.com/)
3. Проверьте [Render Status](https://status.render.com/)

---

**Удачного развертывания! 🚀**

