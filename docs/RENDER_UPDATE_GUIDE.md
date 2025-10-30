# Инструкция по обновлению Render

## Обновление репозитория

✅ **Выполнено**: Репозиторий обновлен с последними изменениями HeyGen интеграции

## Обновление сервисов на Render

### 1. Обновление course-builder-api

1. Перейдите в [Render Dashboard](https://dashboard.render.com/)
2. Найдите сервис `course-builder-api`
3. Нажмите **"Manual Deploy"** → **"Deploy latest commit"**
4. Дождитесь завершения деплоя

### 2. Обновление course-builder-frontend

1. Найдите сервис `course-builder-frontend`
2. Нажмите **"Manual Deploy"** → **"Deploy latest commit"**
3. **ВАЖНО**: Добавьте переменные окружения:
   - `REACT_APP_API_URL` = `https://course-builder-api.onrender.com`
   - `REACT_APP_DEBUG` = `false`
   - `REACT_APP_VERSION` = `1.0.0`
4. Дождитесь завершения деплоя

### 3. Проверка работы

После деплоя проверьте:

1. **API**: https://course-builder-api.onrender.com/health
2. **Frontend**: https://course-builder-frontend.onrender.com
3. **Video Test**: https://course-builder-frontend.onrender.com/video-test

### 4. Настройка HeyGen API

В настройках `course-builder-api` добавьте переменные окружения:

```
HEYGEN_API_KEY=your_heygen_api_key_here
HEYGEN_API_URL=https://api.heygen.com
HEYGEN_DEFAULT_AVATAR_ID=Abigail_expressive_2024112501
HEYGEN_DEFAULT_VOICE_ID=9799f1ba6acd4b2b993fe813a18f9a91
```

## Новые возможности

После обновления будут доступны:

- ✅ Генерация видео для уроков
- ✅ Генерация видео для слайдов
- ✅ Выбор аватаров и голосов
- ✅ Отслеживание статуса генерации
- ✅ Скачивание готовых видео
- ✅ Адаптивная система (работает с мок-сервисом если нет API ключа)

## Устранение неполадок

Если что-то не работает:

1. Проверьте логи в Render Dashboard
2. Убедитесь, что все переменные окружения установлены
3. Проверьте, что HeyGen API ключ действителен
4. Проверьте CORS настройки в бэкенде
