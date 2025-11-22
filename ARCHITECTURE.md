# 🏗️ Архитектура проекта AI Course Builder

## 📖 Полная документация

**Полное описание архитектуры:** [`docs/ARCHITECTURE_NEW.md`](docs/ARCHITECTURE_NEW.md)

## 🎯 Краткий обзор

Проект построен по архитектуре **клиент-сервер**:

- **Frontend**: React 18 + Ant Design + Vite
- **Backend**: FastAPI + Uvicorn
- **AI**: OpenAI GPT-4 API (через официальный SDK)
- **Database**: SQLite (dev) / PostgreSQL (prod)

### Основные слои Backend:

1. **API Layer** (`backend/api/`) - REST endpoints
2. **Service Layer** (`backend/services/`) - бизнес-логика
3. **AI Layer** (`backend/ai/`) - интеграция с OpenAI
4. **Data Layer** (`backend/database/`) - работа с БД

### Ключевые компоненты:

- `OpenAIClient` - клиент для OpenAI API с ретраями и экспоненциальным backoff
- `ContentGenerator` - генератор учебного контента (лекции, слайды)
- `GenerationService` - регенерация целей и планов уроков
- `ExportService` - экспорт в различные форматы (JSON, Markdown, HTML, PPTX)

---

📚 **Для детального описания см. [`docs/ARCHITECTURE_NEW.md`](docs/ARCHITECTURE_NEW.md)**

