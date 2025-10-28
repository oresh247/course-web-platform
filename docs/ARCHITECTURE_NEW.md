# 🏗️ Новая архитектура AI Course Builder (после рефакторинга)

## 🎯 Обзор

Проект построен по архитектуре **клиент-сервер** с разделением на Frontend (React) и Backend (FastAPI).

### 📊 Архитектурная схема системы

```
┌───────────────────────────────────────────────────────────────┐
│                      Browser (React)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │    Pages     │  │ Components   │  │ API Client   │        │
│  │  - Home      │  │  - Header    │  │  - Axios     │        │
│  │  - Courses   │  │  - LessonItem│  │  - API calls │        │
│  │  - Create    │  │              │  │              │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
└─────────┼─────────────────┼─────────────────┼────────────────┘
          │                 │                 │
          └─────────────────┴─────────────────┘
                           │
                    HTTP REST API
                           │
┌──────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend                            │
│  ┌───────────────────────────────────────────────────────┐   │
│  │                    API Layer                          │   │
│  │  ┌────────────────────────────────────────────────┐   │   │
│  │  │  courses_routes.py   →  CRUD курсов            │   │   │
│  │  │  modules_routes.py   →  Модули + Генерация    │   │   │
│  │  │  lessons_routes.py   →  Уроки + Экспорт        │   │   │
│  │  └────────────────────────────────────────────────┘   │   │
│  └────────────────┬───────────────────────────────────────┘   │
│                   │                                            │
│  ┌────────────────▼───────────────────────────────────────┐   │
│  │              Service Layer                              │   │
│  │  ┌──────────────────────┐  ┌──────────────────────┐   │   │
│  │  │  ExportService       │  │ GenerationService    │   │   │
│  │  │  - HTML/MD/PPTX      │  │ - AI regen          │   │   │
│  │  │  - Module export     │  │ - Content gen       │   │   │
│  │  │  - Lesson export     │  │                      │   │   │
│  │  └──────────────────────┘  └──────────────────────┘   │   │
│  └────────────────┬───────────────────────────────────────┘   │
│                   │                                            │
│  ┌────────────────▼───────────────────────────────────────┐   │
│  │              AI Layer                                   │   │
│  │  ┌────────────────────────────────────────────────┐   │   │
│  │  │  OpenAI Client    →  GPT-4 API                │   │   │
│  │  │  Content Generator  →  Контент/Слайды         │   │   │
│  │  │  Prompts           →  Шаблоны запросов        │   │   │
│  │  └────────────────────────────────────────────────┘   │   │
│  └────────────────┬───────────────────────────────────────┘   │
│                   │                                            │
│  ┌────────────────▼───────────────────────────────────────┐   │
│  │              Utils Layer                               │   │
│  │  ┌────────────────────────────────────────────────┐   │   │
│  │  │  formatters.py  →  Имена файлов, кодирование   │   │   │
│  │  └────────────────────────────────────────────────┘   │   │
│  └────────────────┬───────────────────────────────────────┘   │
│                   │                                            │
│  ┌────────────────▼───────────────────────────────────────┐   │
│  │              Data Layer                                 │   │
│  │  ┌────────────────────────────────────────────────┐   │   │
│  │  │  SQLAlchemy ORM                                 │   │   │
│  │  │  - PostgreSQL (Production)                     │   │   │
│  │  │  - SQLite (Development)                        │   │   │
│  │  └────────────────────────────────────────────────┘   │   │
│  └────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
                    │
                    ▼
              OpenAI GPT-4 API
```

### 🔧 Технологии

| **Слой** | **Технология** | **Версия** | **Назначение** |
|----------|---------------|------------|----------------|
| **Frontend** | React | 18.2.0 | UI Framework |
|  | React Router | 6.20.0 | Client-side Routing |
|  | Vite | 5.0.8 | Build Tool & Dev Server |
|  | Ant Design | 5.12.0 | UI Component Library |
|  | Axios | 1.6.2 | HTTP Client |
|  | React Markdown | 9.0.1 | Markdown Rendering |
| **Backend** | FastAPI | 0.115.0 | Web Framework |
|  | Uvicorn | 0.32.0 | ASGI Server |
|  | Pydantic | 2.9.0 | Data Validation |
|  | Gunicorn | 21.2.0 | Production Server |
| **AI** | OpenAI | 1.54.0 | AI Content Generation |
|  | httpx | 0.27.0 | HTTP Client |
| **Database** | SQLAlchemy | 2.0.23 | ORM |
|  | PostgreSQL | - | Production DB |
|  | SQLite | - | Development DB |
| **Export** | python-pptx | 0.6.23 | PowerPoint Export |

---

## 📂 Структура проекта

```
course-web-platform/
├── backend/                          # FastAPI Backend
│   ├── api/                          # REST API (разделено по сущностям)
│   │   ├── courses_routes.py        # ✅ CRUD курсов (~230 строк)
│   │   ├── modules_routes.py        # ✅ Endpoints модулей (~210 строк)
│   │   └── lessons_routes.py        # ✅ Endpoints уроков (~210 строк)
│   │
│   ├── services/                     # 🆕 Сервисный слой
│   │   ├── export_service.py        # Экспорт (HTML/MD/PPTX/JSON)
│   │   └── generation_service.py    # AI-генерация
│   │
│   ├── utils/                        # 🆕 Утилиты
│   │   └── formatters.py            # Форматирование файлов
│   │
│   ├── ai/                           # AI модули
│   │   ├── openai_client.py
│   │   ├── content_generator.py
│   │   └── prompts.py
│   │
│   ├── database/                     # База данных
│   │   └── db.py
│   │
│   ├── models/                       # Pydantic модели
│   │   └── domain.py
│   │
│   └── main.py                       # Точка входа
│
└── frontend/                         # React Frontend
    ├── src/
    │   ├── components/               # React компоненты
    │   │   ├── Header.jsx
    │   │   └── LessonItem.jsx       # 🆕 Компонент урока
    │   │
    │   ├── pages/                    # Страницы
    │   │   ├── HomePage.jsx
    │   │   ├── CoursesListPage.jsx
    │   │   ├── CourseViewPage.jsx
    │   │   └── CreateCoursePage.jsx
    │   │
    │   └── api/
    │       └── coursesApi.js
    │
    └── package.json
```

---

## 🔄 Разделение ответственности

### **API Layer** (`backend/api/`)

#### `courses_routes.py` - Курсы
- Создание курса с AI
- CRUD операции
- Экспорт всего курса

#### `modules_routes.py` - Модули
- Генерация детального контента модуля
- Регенерация целей модуля
- Экспорт детального контента модуля

#### `lessons_routes.py` - Уроки
- Генерация слайдов урока
- Регенерация плана контента
- Экспорт детального контента урока

---

### **Service Layer** (`backend/services/`)

#### `export_service.py` - Экспорт
Централизованная логика экспорта для всех сущностей:
- `export_course_*()` - Экспорт курса (MD, HTML, TXT, PPTX)
- `export_module_*()` - Экспорт модуля (MD, HTML, PPTX)
- `export_lesson_*()` - Экспорт урока (MD, HTML, PPTX)

#### `generation_service.py` - AI генерация
Логика AI-генерации и регенерации:
- `regenerate_module_goal()` - Регенерация цели модуля
- `regenerate_lesson_content_outline()` - Регенерация плана урока

---

### **Utils Layer** (`backend/utils/`)

#### `formatters.py` - Форматирование
- `safe_filename()` - Безопасные имена файлов
- `encode_filename()` - URL-кодирование кириллицы
- `format_content_disposition()` - Заголовки для скачивания

---

## 🎯 Преимущества новой архитектуры

### 1. **Модульность**
- Каждый модуль решает одну задачу
- Легко найти нужную функцию
- Проще ориентироваться в коде

### 2. **Переиспользование**
- ExportService используется из всех роутеров
- GenerationService централизует AI-логику
- Форматтеры используются везде

### 3. **Масштабируемость**
- Легко добавить новый формат экспорта
- Просто добавить новую AI-функцию
- Удобно расширять API

### 4. **Тестируемость**
- Сервисы легко тестировать
- Роутеры тонкие - только обработка запросов
- Четкие зависимости

---

## 📊 Метрики улучшения

| Метрика | До | После | Улучшение |
|---------|-----|--------|-----------|
| Максимальный размер файла | 1827 строк | 480 строк | ↓ 74% |
| Количество файлов Backend API | 1 | 3 | +200% |
| Сервисный слой | Нет | 2 файла | ✅ Новый |
| Утилиты | Нет | 1 файл | ✅ Новый |
| Компоненты Frontend | 1 | 2 | +100% |

---

## 🔌 API Endpoints (без изменений)

Все endpoints остались теми же, только распределены по файлам:

### Курсы (`courses_routes.py`)
```
POST   /api/courses/                    # Создать курс
GET    /api/courses/                    # Список курсов
GET    /api/courses/{id}                # Получить курс
PUT    /api/courses/{id}                # Обновить курс
DELETE /api/courses/{id}                # Удалить курс
GET    /api/courses/{id}/export/{fmt}  # Экспорт курса
```

### Модули (`modules_routes.py`)
```
POST /api/courses/{id}/modules/{num}/generate           # Генерация контента
POST /api/courses/{id}/modules/{num}/regenerate-goal    # Регенерация цели
GET  /api/courses/{id}/modules/{num}/content            # Получить контент
GET  /api/courses/{id}/modules/{num}/export/{fmt}       # Экспорт модуля
```

### Уроки (`lessons_routes.py`)
```
POST /api/courses/{id}/modules/{num}/lessons/{idx}/regenerate-content  # Регенерация плана
POST /api/courses/{id}/modules/{num}/lessons/{idx}/generate            # Генерация слайдов
GET  /api/courses/{id}/modules/{num}/lessons/{idx}/content             # Получить контент
GET  /api/courses/{id}/modules/{num}/lessons/{idx}/export/{fmt}        # Экспорт урока
```

---

## 🎨 Frontend компоненты

### `LessonItem.jsx` - Компонент урока
**Ответственность:** Отображение одного урока с действиями

**Props:**
- `lesson` - Данные урока
- `moduleNumber` - Номер модуля
- `index` - Индекс урока
- `onGenerateContent` - Генерация слайдов
- `onViewContent` - Просмотр
- `onExportContent` - Экспорт
- `onEdit` - Редактирование
- `isGenerating` - Состояние загрузки

**UI:**
- Название урока с иконками действий справа
- План контента с отступом
- Компактное отображение

---

## 🔐 Принципы архитектуры

### **SOLID Principles:**
- ✅ **Single Responsibility** - каждый модуль одна задача
- ✅ **Open/Closed** - легко расширять, не меняя существующий код
- ✅ **Dependency Inversion** - зависимости через абстракции

### **Clean Architecture:**
- API Layer → Service Layer → Data Layer
- Четкое разделение слоев
- Бизнес-логика изолирована

---

## 🚀 Готово к работе!

После рефакторинга:
- ✅ Код чище и организованнее
- ✅ Легче поддерживать
- ✅ Проще расширять
- ✅ Все работает как раньше

