# 🏗️ Архитектура AI Course Builder

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
│  │  - Create    │  │  - Video*    │  │  - getVideo  │        │
│  │  - CourseView│  │  - Test*     │  │    ApiUrl    │        │
│  │  - Content*  │  │              │  │              │        │
│  │  - VideoTest │  │              │  │              │        │
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
│  │  │  lessons_routes.py   →  Уроки + Контент + Экспорт │   │   │
│  │  │  video_routes.py     →  Видео (урок/слайд/курс)│   │   │
│  │  └────────────────────────────────────────────────┘   │   │
│  └────────────────┬───────────────────────────────────────┘   │
│                   │                                            │
│  ┌────────────────▼───────────────────────────────────────┐   │
│  │              Service Layer                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │ ExportService│  │GenerationSvc│  │HeyGenService │   │   │
│  │  │ - HTML/MD   │  │ - AI regen  │  │ - Video gen  │   │   │
│  │  │ - PPTX/SCORM│  │ - Content   │  │ - Status     │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  │  ┌──────────────┐  ┌──────────────┐                    │   │
│  │  │VideoGenSvc   │  │TestGenSvc    │                    │   │
│  │  │ - Lesson vid │  │ - Questions  │                    │   │
│  │  └──────────────┘  └──────────────┘                    │   │
│  └────────────────┬───────────────────────────────────────┘   │
│                   │                                            │
│  ┌────────────────▼───────────────────────────────────────┐   │
│  │              AI Layer                                   │   │
│  │  ┌────────────────────────────────────────────────┐   │   │
│  │  │  OpenAI Client    →  GPT-4 API                │   │   │
│  │  │  Content Generator  →  Контент/Слайды         │   │   │
│  │  │  Prompts           →  Шаблоны запросов        │   │   │
│  │  │  Cache            →  Кэширование ответов    │   │   │
│  │  └────────────────────────────────────────────────┘   │   │
│  └────────────────┬───────────────────────────────────────┘   │
│                   │                                            │
│  ┌────────────────▼───────────────────────────────────────┐   │
│  │              Clients Layer                              │   │
│  │  ┌────────────────────────────────────────────────┐   │   │
│  │  │  HeyGen Client  →  HeyGen API (видео)         │   │   │
│  │  └────────────────────────────────────────────────┘   │   │
│  └────────────────┬───────────────────────────────────────┘   │
│                   │                                            │
│  ┌────────────────▼───────────────────────────────────────┐   │
│  │              Config Layer                              │   │
│  │  ┌────────────────────────────────────────────────┐   │   │
│  │  │  settings.py   →  Централизованные настройки  │   │   │
│  │  └────────────────────────────────────────────────┘   │   │
│  └────────────────┬───────────────────────────────────────┘   │
│                   │                                            │
│  ┌────────────────▼───────────────────────────────────────┐   │
│  │              Data Layer                                 │   │
│  │  ┌────────────────────────────────────────────────┐   │   │
│  │  │  PostgreSQL (Production) - psycopg2           │   │   │
│  │  │  SQLite (Development) - sqlite3               │   │   │
│  │  │  - courses, module_contents, lesson_contents  │   │   │
│  │  │  - JSONB для гибкого хранения контента         │   │   │
│  │  └────────────────────────────────────────────────┘   │   │
│  └────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
                    │                    │
                    ▼                    ▼
              OpenAI GPT-4 API      HeyGen API
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
| **Video** | HeyGen API | - | Видео генерация |
| **Database** | PostgreSQL (psycopg2) | - | Production DB (Render) |
|  | SQLite (sqlite3) | - | Development DB (встроенный) |
| **Export** | python-pptx | 0.6.23 | PowerPoint Export |
|  | SCORM | - | SCORM пакеты |

---

## 📂 Структура проекта

```
course-web-platform/
├── backend/                          # FastAPI Backend
│   ├── api/                          # REST API (разделено по сущностям)
│   │   ├── courses_routes.py        # ✅ CRUD курсов
│   │   ├── modules_routes.py        # ✅ Endpoints модулей
│   │   └── lessons_routes.py        # ✅ Endpoints уроков
│   │
│   ├── routes/                       # 🆕 Видео роутеры
│   │   ├── video_routes.py          # Композит видео роутеров
│   │   ├── video_generate_routes.py # Генерация видео
│   │   ├── video_status_routes.py   # Статус видео
│   │   └── video_assets_routes.py   # Ассеты видео
│   │
│   ├── services/                     # Сервисный слой
│   │   ├── export_service.py        # Фасад экспорта
│   │   ├── generation_service.py    # AI-генерация
│   │   ├── heygen_service.py        # HeyGen интеграция
│   │   ├── video_generation_service.py # Генерация видео
│   │   ├── video_cache_service.py   # Кэш видео
│   │   ├── test_generator_service.py # Генерация тестов
│   │   └── export/                  # Модули экспорта
│   │       ├── markdown.py          # Markdown экспорт
│   │       ├── html.py              # HTML экспорт
│   │       ├── pptx.py              # PowerPoint экспорт
│   │       └── scorm.py             # SCORM экспорт
│   │
│   ├── clients/                      # Внешние клиенты
│   │   └── heygen_client.py         # HeyGen API клиент
│   │
│   ├── config/                       # Конфигурация
│   │   └── settings.py              # Централизованные настройки
│   │
│   ├── utils/                        # Утилиты
│   │   ├── formatters.py            # Форматирование файлов
│   │   ├── http.py                  # HTTP утилиты
│   │   └── strings.py               # Строковые утилиты
│   │
│   ├── ai/                           # AI модули
│   │   ├── openai_client.py         # OpenAI клиент
│   │   ├── content_generator.py    # Генератор контента
│   │   ├── prompts.py               # Промпты
│   │   ├── cache.py                 # Кэш AI ответов
│   │   └── json_sanitizer.py       # Очистка JSON
│   │
│   ├── database/                     # База данных
│   │   ├── db.py                    # SQLite (dev)
│   │   ├── db_postgres.py           # PostgreSQL (prod)
│   │   └── __init__.py              # Автовыбор БД
│   │
│   ├── models/                       # Pydantic модели
│   │   ├── domain.py                # Доменные модели
│   │   ├── video_models.py         # Модели видео
│   │   └── video_cache_models.py   # Модели кэша
│   │
│   └── main.py                       # Точка входа
│
└── frontend/                         # React Frontend
    ├── src/
    │   ├── components/               # React компоненты
    │   │   ├── Header.jsx
    │   │   ├── LessonItem.jsx
    │   │   ├── LessonVideoGenerator.jsx # Генератор видео
    │   │   ├── VideoGenerationPanel.jsx # Панель видео
    │   │   ├── LessonTestGenerator.jsx # Генератор тестов
    │   │   ├── LessonTestEditor.jsx    # Редактор тестов
    │   │   └── LessonTestRunner.jsx     # Запуск тестов
    │   │
│   ├── pages/                    # Страницы
│   │   ├── HomePage.jsx
│   │   ├── CoursesListPage.jsx
│   │   ├── CourseViewPage.jsx
│   │   ├── CourseContentEditorPage.jsx  # Редактор слайдов + видео по слайду
│   │   ├── CreateCoursePage.jsx
│   │   └── VideoTestPage.jsx    # Тестовая страница видео
    │   │
    │   ├── api/
    │   │   └── coursesApi.js        # API клиент
    │   │
    │   └── config/
    │       └── api.js                # Конфигурация API
    │
    └── package.json
```

---

## 🔄 Разделение ответственности

### **API Layer** (`backend/api/` + `backend/routes/`)

#### `courses_routes.py` - Курсы
- Создание курса с AI
- CRUD операции
- Экспорт всего курса (MD, HTML, PPTX, SCORM)

#### `modules_routes.py` - Модули
- Генерация детального контента модуля
- Регенерация целей модуля
- Экспорт детального контента модуля
- Дублирование модулей

#### `lessons_routes.py` - Уроки
- Генерация детального контента урока (лекция со слайдами)
- **PUT** детального контента урока (редактирование слайдов)
- Регенерация плана контента
- Экспорт детального контента урока
- Дублирование/удаление уроков, тесты

#### `video_routes.py` - Видео (композит)
- `video_generate_routes.py` - Генерация видео: урок (`generate-lesson-cached`), **слайд** (`generate-slide-cached`), курс
- `video_status_routes.py` - Проверка статуса генерации (обновление БД для урока и для слайда по ключу кэша)
- `video_assets_routes.py` - Аватары/голоса HeyGen, кэш, скачивание

---

### **Service Layer** (`backend/services/`)

#### `export_service.py` - Экспорт (фасад)
Централизованная логика экспорта для всех сущностей:
- `export_course_*()` - Экспорт курса (MD, HTML, TXT, PPTX, SCORM)
- `export_module_*()` - Экспорт модуля (MD, HTML, PPTX)
- `export_lesson_*()` - Экспорт урока (MD, HTML, PPTX)

**Модули экспорта** (`services/export/`):
- `markdown.py` - Markdown экспорт
- `html.py` - HTML экспорт
- `pptx.py` - PowerPoint экспорт
- `scorm.py` - SCORM пакеты

#### `generation_service.py` - AI генерация
Логика AI-генерации и регенерации:
- `regenerate_module_goal()` - Регенерация цели модуля
- `regenerate_lesson_content_outline()` - Регенерация плана урока

#### `heygen_service.py` - HeyGen интеграция
- Генерация видео из текста
- Проверка статуса генерации
- Скачивание готовых видео
- Поддержка Mock режима (без API ключа)

#### `video_generation_service.py` - Генерация видео
- Генерация видео для уроков
- Генерация видео для слайдов
- Массовая генерация для курса

#### `video_cache_service.py` - Кэш видео
- Кэширование сгенерированных видео по ключу урока `course_id_module_number_lesson_index` или по слайду `..._slide_index`
- Избежание дублирования генераций при том же контенте
- Обновление статуса и download_url при опросе HeyGen

#### `test_generator_service.py` - Генерация тестов
- Генерация вопросов для уроков
- Валидация тестов
- Форматирование тестов

---

### **Clients Layer** (`backend/clients/`)

#### `heygen_client.py` - HeyGen API клиент
- HTTP клиент для HeyGen API (POST/GET/stream)
- Отключение предупреждения InsecureRequestWarning при `verify=False`
- Обработка ошибок и таймаутов, поддержка прокси

---

### **Config Layer** (`backend/config/`)

#### `settings.py` - Централизованные настройки
- OpenAI настройки (модели, токены, таймауты)
- HeyGen настройки (API ключ, аватары, голоса)
- Настройки кэша
- Настройки сети (прокси)

---

### **Utils Layer** (`backend/utils/`)

#### `formatters.py` - Форматирование
- `safe_filename()` - Безопасные имена файлов
- `encode_filename()` - URL-кодирование кириллицы
- `format_content_disposition()` - Заголовки для скачивания

#### `http.py` - HTTP утилиты
- HTTP клиенты с прокси поддержкой

#### `strings.py` - Строковые утилиты
- Утилиты для работы со строками

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

## 💾 База данных

### Структура БД (PostgreSQL/SQLite)

**Таблица `courses`:**
- `id` - SERIAL PRIMARY KEY
- `course_title` - VARCHAR(255)
- `target_audience` - VARCHAR(255)
- `duration_hours` - INTEGER
- `duration_weeks` - INTEGER
- `course_data` - JSONB (полная структура курса)
- `created_at`, `updated_at` - TIMESTAMP

**Таблица `module_contents`:**
- `id` - SERIAL PRIMARY KEY
- `course_id` - INTEGER (FK → courses)
- `module_number` - INTEGER
- `module_title` - VARCHAR(255)
- `content_data` - JSONB (лекции, слайды)
- `created_at` - TIMESTAMP
- UNIQUE (course_id, module_number)

**Таблица `lesson_contents`:**
- `id` - SERIAL PRIMARY KEY
- `course_id` - INTEGER (FK → courses)
- `module_number` - INTEGER
- `lesson_index` - INTEGER
- `lesson_title` - VARCHAR(255)
- `content_data` - JSONB (детальный контент: `lecture_title`, `duration_minutes`, `learning_objectives`, `key_takeaways`, `slides[]`; у каждого элемента `slides[]` могут быть `video_id`, `video_status`, `video_download_url` для видео по слайду)
- `video_id` - TEXT (HeyGen video ID для урока целиком)
- `video_download_url` - TEXT
- `video_status` - TEXT
- `video_generated_at` - TIMESTAMP
- `created_at` - TIMESTAMP
- UNIQUE (course_id, module_number, lesson_index)

Методы БД для видео по слайду: `update_lesson_slide_video_info(course_id, module_number, lesson_index, slide_index, ...)` — обновляет поля видео в `content_data.slides[slide_index]`.

### Особенности

- **Автовыбор БД**: Если `DATABASE_URL` установлен → PostgreSQL, иначе → SQLite
- **JSONB**: Гибкое хранение структурированных данных
- **CASCADE**: Удаление курса удаляет связанные модули и уроки
- **Индексы**: Оптимизация запросов по course_id, created_at

## 📊 Метрики проекта

| Метрика | Значение |
|---------|----------|
| Backend API файлов | 4 (courses, modules, lessons, video) |
| Сервисных модулей | 6+ (export, generation, heygen, video, test, cache) |
| Frontend страниц | 6 (Home, Courses, Create, CourseView, **CourseContentEditor**, VideoTest) |
| Frontend компонентов | 7+ |
| Поддерживаемых форматов экспорта | 5 (MD, HTML, PPTX, SCORM, JSON) |
| Интеграций | 2 (OpenAI, HeyGen) |

---

## 🔌 API Endpoints

### Курсы (`courses_routes.py`)
```
POST   /api/courses/                    # Создать курс
GET    /api/courses/                    # Список курсов
GET    /api/courses/{id}                # Получить курс
PUT    /api/courses/{id}                # Обновить курс
DELETE /api/courses/{id}                # Удалить курс
GET    /api/courses/{id}/export/{fmt}  # Экспорт курса (md, html, pptx, scorm)
```

### Модули (`modules_routes.py`)
```
POST   /api/courses/{id}/modules/{num}/generate           # Генерация контента
POST   /api/courses/{id}/modules/{num}/regenerate-goal    # Регенерация цели
GET    /api/courses/{id}/modules/{num}/content            # Получить контент
GET    /api/courses/{id}/modules/{num}/export/{fmt}       # Экспорт модуля
POST   /api/courses/{id}/modules/{num}/duplicate          # Дублировать модуль
DELETE /api/courses/{id}/modules/{num}                    # Удалить модуль
```

### Уроки (`lessons_routes.py`)
```
POST   /api/courses/{id}/modules/{num}/lessons/{idx}/regenerate-content  # Регенерация плана
POST   /api/courses/{id}/modules/{num}/lessons/{idx}/generate            # Генерация контента (лекция + слайды)
GET    /api/courses/{id}/modules/{num}/lessons/{idx}/content             # Получить контент
PUT    /api/courses/{id}/modules/{num}/lessons/{idx}/content             # Обновить контент (редактирование слайдов)
GET    /api/courses/{id}/modules/{num}/lessons/{idx}/export/{fmt}         # Экспорт урока
POST   /api/courses/{id}/modules/{num}/lessons/{idx}/duplicate            # Дублировать урок
DELETE /api/courses/{id}/modules/{num}/lessons/{idx}                       # Удалить урок
```

### Видео (`video_routes.py`)
```
POST   /api/video/generate-lesson-cached                 # Генерация видео для урока (query: course_id, module_number, lesson_index)
POST   /api/video/generate-slide-cached                  # Генерация видео для одного слайда (query: + slide_index)
POST   /api/video/generate-lesson                        # Генерация урока с видео (body)
POST   /api/video/generate-lesson-slides                 # Генерация урока с видео по слайдам (body)
POST   /api/video/generate-course                        # Массовая генерация для курса
GET    /api/video/status/{video_id}                      # Статус генерации (обновляет кэш и БД: урок или слайд по ключу)
GET    /api/video/avatars                                # Список аватаров HeyGen
GET    /api/video/voices                                 # Список голосов HeyGen
GET    /api/video/lesson/{cid}/{mn}/{li}/info            # Информация о видео урока
```

### Системные
```
GET    /health                                           # Health check
GET    /api/health                                       # Health check (альтернативный)
GET    /api/docs                                         # Swagger документация
GET    /api/redoc                                        # ReDoc документация
```

---

## 🎨 Frontend компоненты

### `LessonItem.jsx` - Компонент урока
**Ответственность:** Отображение одного урока с действиями

**Props:**
- `lesson` - Данные урока
- `moduleNumber` - Номер модуля
- `index` - Индекс урока
- `onGenerateContent` - Генерация контента
- `onViewContent` - Просмотр
- `onExportContent` - Экспорт
- `onEdit` - Редактирование
- `isGenerating` - Состояние загрузки

**UI:**
- Название урока с иконками действий справа
- План контента с отступом
- Компактное отображение

### `LessonVideoGenerator.jsx` - Генератор видео
**Ответственность:** Генерация видео для урока через HeyGen

**Функции:**
- Генерация видео из текста урока
- Отслеживание статуса генерации
- Скачивание готовых видео

### `CourseContentEditorPage.jsx` - Редактор контента курса
**Маршрут:** `/courses/:id/content`

**Ответственность:** Редактирование слайдов уроков и генерация видео по каждому слайду

**Функции:**
- Дерево модулей и уроков слева; справа — форма редактирования выбранного урока (название лекции, длительность, цели, выводы, список слайдов)
- Редактирование полей слайда: заголовок, текст, тип, пример кода, заметки; добавление/удаление слайдов
- Сохранение контента через `PUT .../lessons/{idx}/content`
- Для каждого слайда кнопка «Видео»: модальное окно с текстом для озвучки, выбор аватара и голоса (HeyGen), генерация через `POST /api/video/generate-slide-cached`; опрос статуса и отображение ссылки на готовое видео
- Загрузка аватаров/голосов через `getVideoApiUrl('AVATARS'/'VOICES')` (как на странице курса)
- Отображение переносов строк в тексте слайда (литеральные `\n` → реальные переносы)

📄 **Подробнее:** [LESSON_SLIDES_EDITOR.md](LESSON_SLIDES_EDITOR.md)

### `VideoGenerationPanel.jsx` - Панель видео
**Ответственность:** Управление видео генерацией

**Функции:**
- Массовая генерация для курса
- Просмотр статуса всех видео
- Управление видео ассетами

### `LessonTestGenerator.jsx` - Генератор тестов
**Ответственность:** Генерация тестов для урока

**Функции:**
- Генерация вопросов через AI
- Валидация тестов
- Сохранение тестов

### `LessonTestEditor.jsx` - Редактор тестов
**Ответственность:** Редактирование тестов

**Функции:**
- Редактирование вопросов
- Добавление/удаление вариантов ответов
- Настройка проходного балла

### `LessonTestRunner.jsx` - Запуск тестов
**Ответственность:** Прохождение тестов

**Функции:**
- Отображение вопросов
- Проверка ответов
- Показ результатов

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

## 🔄 Интеграции

### OpenAI Integration
- **Модели**: GPT-4, GPT-4 Turbo
- **Использование**: Генерация контента курсов, модулей, уроков, тестов
- **Кэширование**: Включено по умолчанию (TTL: 24 часа)
- **Ретраи**: Автоматические с экспоненциальным backoff

### HeyGen Integration
- **API**: HeyGen Video API
- **Использование**: Генерация видео для урока целиком или для каждого слайда урока (редактор контента)
- **Режимы**: Реальный API или Mock (для разработки)
- **Функции**: Генерация по тексту, проверка статуса, скачивание; аватары и голоса через `/api/video/avatars`, `/api/video/voices`
- **Нормализация статусов** (`backend/services/heygen/normalizers.py`): статусы `processing`, `in_progress`, `queued`, `pending`, `working` приводятся к `generating`; для кода `MOVIO_PAYMENT_INSUFFICIENT_CREDIT` возвращается понятное сообщение о пополнении баланса HeyGen
- **Клиент** (`backend/clients/heygen_client.py`): отключено предупреждение InsecureRequestWarning при `verify=False`

---

## 📐 Принципы развития архитектуры

### При добавлении нового функционала

1. **Определи слой**: API → Service → AI/Data
2. **Используй существующее**: Проверь, есть ли похожий функционал
3. **Следуй структуре**: Новые файлы в правильных директориях
4. **Документируй**: Обнови архитектуру при значительных изменениях

### Правила для разработчиков

#### API Layer (Роутеры)
- ✅ Только HTTP обработка, валидация, вызов сервисов
- ✅ Использование Pydantic моделей для валидации
- ✅ Обработка HTTP ошибок с правильными статусами
- ❌ НЕ содержит бизнес-логику
- ❌ НЕ содержит прямые SQL запросы

#### Service Layer
- ✅ Вся бизнес-логика
- ✅ Переиспользование между роутерами
- ✅ Использование `backend/database/db` для БД
- ✅ Использование `backend/ai/` для AI
- ❌ НЕ содержит HTTP специфику

#### AI Layer
- ✅ Интеграция с OpenAI/HeyGen
- ✅ Промпты и шаблоны
- ✅ Кэширование AI ответов
- ❌ НЕ содержит бизнес-логику

#### Data Layer
- ✅ Абстракция над БД
- ✅ CRUD операции
- ✅ Автовыбор БД (PostgreSQL/SQLite)
- ❌ НЕ содержит бизнес-логику

### Запрещено

- ❌ Прямые SQL запросы вне `backend/database/`
- ❌ Бизнес-логика в роутерах
- ❌ Дублирование кода между модулями
- ❌ Хардкод настроек (используй `backend/config/settings.py`)
- ❌ Прямые вызовы внешних API из роутеров (используй клиенты)

### Рекомендуется

- ✅ Использовать существующие сервисы для переиспользования
- ✅ Создавать новые сервисы для новой функциональности
- ✅ Использовать Pydantic модели для валидации
- ✅ Логировать важные действия через logger
- ✅ Обрабатывать ошибки с правильными HTTP статусами
- ✅ Использовать async функции для всех endpoints
- ✅ Документировать сложную логику

### Примеры добавления функционала

#### Новый API endpoint
```python
# 1. Создать роутер в backend/api/new_feature_routes.py
from fastapi import APIRouter
from backend.services.new_feature_service import NewFeatureService

router = APIRouter(prefix="/api/new-feature", tags=["new-feature"])

@router.post("/")
async def create_new_feature(data: NewFeatureRequest):
    service = NewFeatureService()
    result = await service.create(data)
    return result

# 2. Подключить в backend/main.py
from backend.api.new_feature_routes import router as new_feature_router
app.include_router(new_feature_router)
```

#### Новый сервис
```python
# backend/services/new_feature_service.py
from backend.database import db
from backend.ai.content_generator import ContentGenerator

class NewFeatureService:
    def __init__(self):
        self.db = db
        self.ai = ContentGenerator()
    
    async def create(self, data):
        # Бизнес-логика здесь
        result = await self.ai.generate(data)
        self.db.save(result)
        return result
```

#### Новый формат экспорта
```python
# 1. Создать модуль в backend/services/export/pdf.py
def export_course_pdf(course: Course) -> bytes:
    # Логика экспорта в PDF
    pass

# 2. Добавить в ExportService как фасад
# backend/services/export_service.py
from backend.services.export.pdf import export_course_pdf as _export_course_pdf

class ExportService:
    @staticmethod
    def export_course_pdf(course: Course) -> bytes:
        return _export_course_pdf(course)
```

📚 **Подробные принципы для AI ассистента:** [`.cursor/rules/architecture-principles.mdc`](../.cursor/rules/architecture-principles.mdc)

---

## 🚀 Готово к работе!

Текущее состояние:
- ✅ Модульная архитектура
- ✅ Разделение ответственности
- ✅ Легко поддерживать и расширять
- ✅ Поддержка PostgreSQL и SQLite
- ✅ Интеграция с OpenAI и HeyGen
- ✅ Экспорт в 5 форматов
- ✅ Генерация видео (урок целиком и по каждому слайду)
- ✅ Редактор слайдов урока (страница `/courses/:id/content`) с сохранением контента и видео по слайду
- ✅ Генерация тестов

