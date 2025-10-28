# ✅ Чеклист развертывания на Render.com

## Перед развертыванием

- [ ] Код загружен в GitHub репозиторий
- [ ] Есть OpenAI API ключ (https://platform.openai.com/api-keys)
- [ ] Проверено, что все файлы на месте:
  - [ ] `render.yaml`
  - [ ] `build.sh`
  - [ ] `backend/requirements.txt`
  - [ ] `frontend/package.json`

## Создание сервисов на Render

- [ ] Зарегистрирован аккаунт на https://dashboard.render.com/
- [ ] Подключен GitHub аккаунт к Render
- [ ] Создан Blueprint из репозитория
- [ ] Render обнаружил `render.yaml`

## Настройка Backend

- [ ] Добавлена переменная окружения `OPENAI_API_KEY`
- [ ] Проверен статус сборки (должен быть зеленым)
- [ ] Проверен endpoint `/health`:
  ```
  https://course-builder-api.onrender.com/health
  ```
  Должен вернуть: `{"status":"healthy"}`

## Настройка Frontend

- [ ] Переменная `VITE_API_URL` установлена автоматически
- [ ] Проверен статус сборки
- [ ] Открыт frontend URL в браузере
- [ ] Проверена главная страница

## Тестирование

- [ ] Открывается главная страница
- [ ] Можно создать новый курс
- [ ] AI генерация работает
- [ ] Курсы сохраняются
- [ ] Можно просмотреть созданный курс
- [ ] Детальный контент генерируется
- [ ] Экспорт работает

## Для продакшн (опционально)

- [ ] Создана PostgreSQL база данных на Render
- [ ] Обновлена переменная `DATABASE_URL` в Backend
- [ ] Обновлен код для работы с PostgreSQL
- [ ] CORS ограничен конкретным доменом (не `*`)
- [ ] Настроен собственный домен (опционально)
- [ ] Включен monitoring и алерты

## Проблемы?

Если что-то не работает:

1. **Backend не стартует** → проверьте логи в Render Dashboard
2. **Frontend не подключается** → проверьте `VITE_API_URL`
3. **AI не работает** → проверьте `OPENAI_API_KEY` и баланс OpenAI
4. **Данные теряются** → настройте PostgreSQL (см. DEPLOY.md)

## Ссылки

- 📖 Полная инструкция: [DEPLOY.md](./DEPLOY.md)
- ⚡ Быстрый старт: [RENDER_QUICKSTART.md](./RENDER_QUICKSTART.md)
- 🔑 Переменные окружения: [RENDER_ENV.md](./RENDER_ENV.md)
- 📚 Render Docs: https://render.com/docs

---

**Удачи с развертыванием! 🚀**

