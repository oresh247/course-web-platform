# 🏗️ Архитектура проекта AI Course Builder

## 📖 Полная документация

**Полное описание архитектуры:** [`docs/ARCHITECTURE_NEW.md`](docs/ARCHITECTURE_NEW.md)

## 🎯 Краткий обзор

Проект построен по архитектуре **клиент-сервер**:

- **Frontend**: React 18 + Ant Design + Vite
- **Backend**: FastAPI + Uvicorn
- **AI**: OpenAI GPT-4 API (через официальный SDK)
- **Video**: HeyGen API (генерация видео)
- **Database**: SQLite (dev) / PostgreSQL (prod на Render)

### Основные слои Backend:

1. **API Layer** (`backend/api/` + `backend/routes/`) - REST endpoints
   - `courses_routes.py` - CRUD курсов
   - `modules_routes.py` - Модули
   - `lessons_routes.py` - Уроки
   - `video_routes.py` - Видео генерация

2. **Service Layer** (`backend/services/`) - бизнес-логика
   - `export_service.py` - Экспорт (MD, HTML, PPTX, SCORM)
   - `generation_service.py` - AI генерация
   - `heygen_service.py` - HeyGen интеграция
   - `video_generation_service.py` - Генерация видео
   - `test_generator_service.py` - Генерация тестов

3. **AI Layer** (`backend/ai/`) - интеграция с OpenAI
   - `openai_client.py` - OpenAI клиент
   - `content_generator.py` - Генератор контента
   - `cache.py` - Кэш AI ответов

4. **Clients Layer** (`backend/clients/`) - внешние API
   - `heygen_client.py` - HeyGen API клиент

5. **Data Layer** (`backend/database/`) - работа с БД
   - `db.py` - SQLite (dev)
   - `db_postgres.py` - PostgreSQL (prod)
   - Автовыбор БД по `DATABASE_URL`

### Ключевые компоненты:

- `OpenAIClient` - клиент для OpenAI API с ретраями и экспоненциальным backoff
- `ContentGenerator` - генератор учебного контента (лекции, слайды)
- `GenerationService` - регенерация целей и планов уроков
- `ExportService` - экспорт в различные форматы (JSON, Markdown, HTML, PPTX, SCORM)
- `HeyGenService` - генерация видео через HeyGen API
- `VideoGenerationService` - управление генерацией видео для уроков
- `TestGeneratorService` - генерация тестов для уроков

### База данных:

- **3 таблицы**: `courses`, `module_contents`, `lesson_contents`
- **JSONB** для гибкого хранения структурированных данных
- **Автовыбор**: PostgreSQL (если `DATABASE_URL`) или SQLite (dev)

---

📚 **Для детального описания см. [`docs/ARCHITECTURE_NEW.md`](docs/ARCHITECTURE_NEW.md)**

