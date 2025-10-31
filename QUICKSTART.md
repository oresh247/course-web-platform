# 🚀 Быстрый старт - AI Course Builder

## За 5 минут до первого курса!

### Шаг 1: Подготовка (1 минута)

Убедитесь, что у вас установлено:
- ✅ Python 3.9+ (`python --version`)
- ✅ Node.js 18+ (`node --version`)
- ✅ OpenAI API ключ ([получить здесь](https://platform.openai.com/api-keys))

### Шаг 2: Настройка Backend (2 минуты)

```bash
# 1. Перейдите в директорию backend
cd backend

# 2. Создайте виртуальное окружение
python -m venv venv

# 3. Активируйте (Windows PowerShell)
venv\Scripts\activate

# 4. Установите зависимости
pip install -r requirements.txt

# 5. Создайте .env файл
copy env.example .env
```

**Важно!** Откройте файл `.env` и добавьте ваш OpenAI API ключ:
```env
OPENAI_API_KEY=sk-your-actual-key-here
```

### Шаг 3: Настройка Frontend (1 минута)

Откройте **новый терминал** (не закрывайте первый!):

```bash
# 1. Перейдите в директорию frontend
cd frontend

# 2. Установите зависимости
npm install
```

### Шаг 4: Запуск (1 минута)

**Терминал 1 (Backend):**
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Вы должны увидеть:
```
🚀 Запуск AI Course Builder API...
📚 Документация доступна на: http://localhost:8000/api/docs
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Терминал 2 (Frontend):**
```bash
cd frontend
npm run dev
```

Вы должны увидеть:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  press h + enter to show help
```

### Шаг 5: Создайте первый курс! 🎉

1. Откройте браузер: http://localhost:3000
2. Нажмите "Создать курс"
3. Заполните форму:
   - **Тема**: Python для начинающих
   - **Аудитория**: Junior
   - **Модули**: 4
4. Нажмите "Создать курс с помощью AI"
5. Подождите 20-30 секунд ⏳
6. Готово! Ваш первый AI-курс создан! 🎓

## ❓ Что-то пошло не так?

### Backend не запускается

**Ошибка:** `OPENAI_API_KEY не найден`
- ✅ Проверьте, что файл `.env` создан в директории `backend/`
- ✅ Убедитесь, что в `.env` есть строка с вашим ключом

**Ошибка:** `Module not found`
- ✅ Активируйте виртуальное окружение: `venv\Scripts\activate`
- ✅ Установите зависимости заново: `pip install -r requirements.txt`

### Frontend не запускается

**Ошибка:** `command not found: npm`
- ✅ Установите Node.js: https://nodejs.org/

**Ошибка:** `ECONNREFUSED 127.0.0.1:8000`
- ✅ Убедитесь, что backend запущен и работает на порту 8000

### AI не генерирует курсы

**Ошибка в консоли:** `401 Unauthorized`
- ✅ Проверьте правильность API ключа OpenAI
- ✅ Убедитесь, что у вас есть баланс на аккаунте OpenAI

**Долгая генерация (>60 секунд)**
- ✅ Это нормально для первого запроса
- ✅ Проверьте интернет-соединение
- ✅ Если используете прокси, настройте его в `.env`

## 🌐 Работа через корпоративный прокси

Если вы в корпоративной сети:

1. Откройте `backend/.env`
2. Раскомментируйте и настройте:
```env
HTTP_PROXY=http://your-proxy-server:port
HTTPS_PROXY=http://your-proxy-server:port
```

## 📚 Полезные ссылки

- 📖 Полная документация: `README.md`
- 🔌 API документация: http://localhost:8000/api/docs
- 🎨 Frontend: http://localhost:3000

## 🧩 Полезные утилиты

Запускать из корня проекта:

```bash
python backend/tools/check_heygen_access.py --video <VIDEO_ID> [--backend http://localhost:8000]
python backend/tools/test_video_caching.py
python backend/tools/test_video_diagnostic.py
```

---

**Готово! Теперь вы можете создавать курсы с помощью AI! 🚀**

