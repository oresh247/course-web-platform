# 🏗️ Архитектура проекта AI Course Builder

## Обзор

Проект построен по архитектуре **клиент-сервер** с разделением на Frontend (React) и Backend (FastAPI).

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (React)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  Pages   │  │Components│  │  API     │              │
│  │          │  │          │  │ Client   │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
└───────┼────────────┼─────────────┼────────────────────┘
        │            │             │
        └────────────┴─────────────┘
                     │
              HTTP REST API
                     │
┌────────────────────┼─────────────────────────────────────┐
│                    ▼                                      │
│              FastAPI Backend                              │
│  ┌────────────────────────────────────────────┐          │
│  │              API Layer                      │          │
│  │  ┌──────────────────────────────────┐     │          │
│  │  │  /api/courses/* endpoints        │     │          │
│  │  └──────────────────────────────────┘     │          │
│  └────────────────┬───────────────────────────┘          │
│                   │                                       │
│  ┌────────────────▼───────────────────────────┐          │
│  │          Business Logic Layer               │          │
│  │  ┌──────────────┐  ┌──────────────┐       │          │
│  │  │   AI Layer   │  │ Models Layer │       │          │
│  │  │  - Prompts   │  │  - Pydantic  │       │          │
│  │  │  - OpenAI    │  │  - Validation│       │          │
│  │  │  - Generator │  │              │       │          │
│  │  └──────────────┘  └──────────────┘       │          │
│  └────────────────┬───────────────────────────┘          │
│                   │                                       │
│  ┌────────────────▼───────────────────────────┐          │
│  │          Data Layer                         │          │
│  │  ┌──────────────────────────────────┐     │          │
│  │  │      SQLite Database             │     │          │
│  │  │  - courses                       │     │          │
│  │  │  - module_contents               │     │          │
│  │  └──────────────────────────────────┘     │          │
│  └──────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────┘
                     │
                     ▼
              OpenAI GPT-4 API
```

## Структура Backend

### 1. API Layer (`backend/api/`)

**Отвечает за:** HTTP endpoints, валидацию запросов, обработку ошибок

```python
backend/api/
├── courses.py          # CRUD операции с курсами
│   ├── POST   /api/courses/                    # Создать курс
│   ├── GET    /api/courses/                    # Список курсов
│   ├── GET    /api/courses/{id}                # Получить курс
│   ├── PUT    /api/courses/{id}                # Обновить курс
│   ├── DELETE /api/courses/{id}                # Удалить курс
│   ├── POST   /api/courses/{id}/modules/{n}/generate  # Генерация контента
│   └── GET    /api/courses/{id}/modules/{n}/content   # Получить контент
└── __init__.py
```

### 2. AI Layer (`backend/ai/`)

**Отвечает за:** Взаимодействие с OpenAI API, генерацию контента

```python
backend/ai/
├── prompts.py              # Промпты для GPT-4
│   ├── COURSE_GENERATION_PROMPT        # Создание структуры курса
│   ├── MODULE_CONTENT_PROMPT           # Генерация лекций и слайдов
│   ├── TOPIC_MATERIAL_PROMPT           # Детальные материалы
│   └── format_* функции                # Форматирование данных
│
├── openai_client.py        # Клиент OpenAI с прокси
│   ├── OpenAIClient
│   │   ├── __init__()                  # Настройка прокси и SSL
│   │   ├── generate_course_structure() # Генерация курса
│   │   └── call_ai()                   # Универсальный вызов API
│   
└── content_generator.py    # Генератор контента
    ├── ContentGenerator
    │   ├── generate_module_content()   # Лекции + слайды
    │   ├── generate_topic_material()   # Детальные материалы
    │   └── _try_* методы               # Стратегии генерации
```

**Ключевые особенности AI Layer:**
- ✅ Поддержка корпоративных прокси
- ✅ Отключение SSL для работы в защищенных сетях
- ✅ Fallback стратегии (JSON mode → Text mode → Test data)
- ✅ Переиспользование промптов из Telegram бота

### 3. Models Layer (`backend/models/`)

**Отвечает за:** Валидация данных, типизация

```python
backend/models/
└── domain.py
    ├── Доменные модели (Pydantic)
    │   ├── Course            # Курс
    │   ├── Module            # Модуль
    │   ├── Lesson            # Урок
    │   ├── Lecture           # Лекция
    │   ├── Slide             # Слайд
    │   ├── TopicMaterial     # Материал по теме
    │   └── ModuleContent     # Контент модуля
    │
    └── API модели
        ├── CourseCreateRequest
        ├── CourseResponse
        └── ErrorResponse
```

### 4. Data Layer (`backend/database/`)

**Отвечает за:** Хранение и извлечение данных

```python
backend/database/
└── db.py
    ├── CourseDatabase
    │   ├── save_course()           # Сохранить курс
    │   ├── get_course()            # Получить курс
    │   ├── update_course()         # Обновить
    │   ├── delete_course()         # Удалить
    │   ├── save_module_content()   # Сохранить контент модуля
    │   └── get_module_content()    # Получить контент модуля
    │
    └── SQLite таблицы:
        ├── courses             # Основная информация о курсах
        └── module_contents     # Детальный контент модулей
```

**Схема БД:**

```sql
CREATE TABLE courses (
    id INTEGER PRIMARY KEY,
    course_title TEXT,
    target_audience TEXT,
    duration_hours INTEGER,
    duration_weeks INTEGER,
    course_data TEXT,        -- JSON с полной структурой
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE module_contents (
    id INTEGER PRIMARY KEY,
    course_id INTEGER,
    module_number INTEGER,
    module_title TEXT,
    content_data TEXT,       -- JSON с лекциями и слайдами
    created_at TIMESTAMP,
    UNIQUE(course_id, module_number)
);
```

## Структура Frontend

### 1. Pages Layer (`frontend/src/pages/`)

**Отвечает за:** Основные страницы приложения

```javascript
pages/
├── HomePage.jsx            # Главная страница
├── CreateCoursePage.jsx    # Форма создания курса
├── CoursesListPage.jsx     # Список курсов
└── CourseViewPage.jsx      # Просмотр/редактирование курса
```

### 2. Components Layer (`frontend/src/components/`)

**Отвечает за:** Переиспользуемые компоненты

```javascript
components/
└── Header.jsx              # Шапка приложения с навигацией
```

### 3. API Client Layer (`frontend/src/api/`)

**Отвечает за:** HTTP запросы к backend

```javascript
api/
└── coursesApi.js
    ├── createCourse()          # POST /api/courses/
    ├── getCourses()            # GET /api/courses/
    ├── getCourse(id)           # GET /api/courses/{id}
    ├── updateCourse(id)        # PUT /api/courses/{id}
    ├── deleteCourse(id)        # DELETE /api/courses/{id}
    ├── generateModuleContent() # POST .../generate
    └── getModuleContent()      # GET .../content
```

## Потоки данных

### Создание курса

```
User Input (Form)
    │
    ▼
CreateCoursePage
    │
    ▼
coursesApi.createCourse()
    │ HTTP POST /api/courses/
    ▼
FastAPI endpoint
    │
    ▼
OpenAIClient.generate_course_structure()
    │ → OpenAI GPT-4 API
    ▼
Course (Pydantic validation)
    │
    ▼
CourseDatabase.save_course()
    │
    ▼
SQLite Database
    │
    ▼
Response to Frontend
    │
    ▼
Navigate to CourseViewPage
```

### Генерация контента модуля

```
User clicks "Generate Content"
    │
    ▼
CourseViewPage
    │
    ▼
coursesApi.generateModuleContent()
    │ HTTP POST .../modules/{n}/generate
    ▼
FastAPI endpoint
    │
    ▼
ContentGenerator.generate_module_content()
    │ → OpenAI GPT-4 API
    │    (Multiple strategies: JSON mode, Text mode, Fallback)
    ▼
ModuleContent (with Lectures & Slides)
    │
    ▼
CourseDatabase.save_module_content()
    │
    ▼
Response with generated content
```

## Переиспользование кода из Telegram бота

| Компонент | Источник | Назначение | Изменения |
|-----------|----------|------------|-----------|
| `prompts.py` | TGBotCreateCourse | Промпты GPT | ✅ Без изменений |
| `openai_client.py` | TGBotCreateCourse | OpenAI API + прокси | ✅ Добавлен универсальный метод |
| `content_generator.py` | TGBotCreateCourse | Генерация контента | ✅ Убраны зависимости от Telegram |
| `models.py → domain.py` | TGBotCreateCourse | Pydantic модели | ✅ Добавлены API модели |
| SSL Fix | TGBotCreateCourse | Работа без SSL | ✅ Без изменений |

## Технологический стек

### Backend
- **FastAPI** 0.104+ - Веб-фреймворк
- **Pydantic** 2.5+ - Валидация данных
- **OpenAI** 1.3.0 - GPT-4 API
- **httpx** 0.24.1 - HTTP клиент с прокси
- **SQLite** - Встроенная БД
- **uvicorn** - ASGI сервер

### Frontend
- **React** 18.2 - UI библиотека
- **Vite** 5.0 - Build tool
- **Ant Design** 5.12 - UI компоненты
- **React Router** 6.20 - Навигация
- **Axios** 1.6 - HTTP клиент

## Масштабирование

### Текущая архитектура (v1.0)
- ✅ Локальная SQLite БД
- ✅ Один пользователь
- ✅ Синхронная генерация контента

### Возможные улучшения (v2.0+)

1. **База данных**
   - PostgreSQL для мультипользовательского режима
   - Redis для кэширования

2. **Асинхронность**
   - Celery + Redis для фоновых задач
   - WebSocket для real-time обновлений

3. **Аутентификация**
   - JWT токены
   - OAuth (Google, GitHub)

4. **Deployment**
   - Docker контейнеры
   - Kubernetes для масштабирования
   - AWS/Azure/GCP хостинг

---

**Архитектура разработана с учетом:**
- ✅ Переиспользования кода
- ✅ Модульности и расширяемости
- ✅ Простоты разработки и поддержки

