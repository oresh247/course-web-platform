# Решение проблемы с подключением к продакшн API

## Проблема
Фронтенд пытается подключиться к продакшн URL `https://course-builder-api.onrender.com` вместо локального бэкенда `http://localhost:8000`, что приводит к ошибке:

```
GET https://course-builder-api.onrender.com/api/courses/?limit=50&offset=0 net::ERR_FAILED 503 (Service Unavailable)
```

## Причина
В файле `frontend/vite.config.js` было установлено неправильное дефолтное значение для `VITE_API_URL`:

```javascript
// БЫЛО (неправильно):
'import.meta.env.VITE_API_URL': JSON.stringify(
  process.env.VITE_API_URL || 'https://course-builder-api.onrender.com'
)

// СТАЛО (правильно):
'import.meta.env.VITE_API_URL': JSON.stringify(
  process.env.VITE_API_URL || 'http://localhost:8000'
)
```

## Решение

### Шаг 1: Исправлен vite.config.js ✅
Файл `frontend/vite.config.js` уже исправлен и теперь использует локальный URL по умолчанию.

### Шаг 2: Перезапустите фронтенд
```bash
# Остановите все процессы Node.js
taskkill /F /IM node.exe

# Перейдите в папку фронтенда
cd frontend

# Запустите фронтенд
npm run dev
```

### Шаг 3: Проверьте работу
1. Откройте `http://localhost:3000/courses` в браузере
2. Проверьте консоль разработчика (F12) - теперь должны быть запросы к `http://localhost:8000`
3. Курсы должны загружаться из Render PostgreSQL

## Альтернативное решение

Если фронтенд все еще не работает, используйте тестовый HTML файл:

1. Откройте `test_env_variables.html` в браузере
2. Убедитесь, что локальный API работает
3. Проверьте, что курсы загружаются из Render PostgreSQL

## Проверка результата

После исправления:
- ✅ Фронтенд подключается к `http://localhost:8000`
- ✅ Курсы загружаются из Render PostgreSQL
- ✅ Нет ошибок 503 Service Unavailable
- ✅ Страница `/courses` отображает курсы

## Troubleshooting

### Если фронтенд не запускается:
```bash
# Проверьте, что Node.js установлен
node --version

# Переустановите зависимости
cd frontend
npm install

# Запустите фронтенд
npm run dev
```

### Если все еще подключается к продакшн API:
1. Убедитесь, что файл `frontend/.env.local` содержит:
   ```
   VITE_API_URL=http://localhost:8000
   ```

2. Перезапустите фронтенд после изменения файлов

3. Проверьте, что в консоли браузера нет кэшированных запросов (очистите кэш: Ctrl+Shift+R)

## Заключение

Проблема была в неправильной конфигурации Vite. После исправления `vite.config.js` фронтенд должен корректно подключаться к локальному бэкенду и отображать курсы из Render PostgreSQL.
