## Предложения по улучшениям (архитектура, DX, качество)

Документ фиксирует предложения по развитию проекта на основе текущей структуры репозитория (FastAPI backend + React/Ant Design frontend, OpenAI/HeyGen, SQLite/Postgres на Render). Разбит на тематические разделы и поэтапный план внедрения.

---

## Архитектура и бэкенд (FastAPI)

1) Слои и DI по границам
- Укрепить границы слоёв:
  - `api/` — только контроллеры/DTO, без бизнес‑логики;
  - `domain/` — pydantic‑модели и value‑объекты;
  - `repositories/` (или `gateways/`) — внешние интеграции: БД, OpenAI, HeyGen;
  - `services/` — чистая бизнес‑логика.
- Ввести простой DI (инициализация клиентов/репозиториев в lifespan, хранение в `app.state`).

2) Полный async‑стек и «долгие» задачи
- Перейти на `httpx.AsyncClient` для внешних HTTP.
- Для тяжёлых операций (генерация структуры/контента/слайдов/видео) — фоновые задачи (Celery/RQ/Arq + Redis).
- Хранить `job_id`, `status`, `progress`, `result_url`, `error_code` в таблице `jobs`; фронт опрашивает `/api/jobs/{id}`.

3) Миграции и Postgres
- Добавить SQLAlchemy + Alembic.
- В Render (`render.yaml`) — preStart‑hook для миграций.
- Dev — SQLite по умолчанию, Prod — Postgres, совместимость через ENV.

4) Настройки/ENV как код
- Вынести конфиг на `pydantic‑settings` (Pydantic v2): типы, дефолты, обязательные значения.
- Маскирование секретов в логах; централизованные `CORS`/`DEBUG` профили.

5) Унифицированный HTTP‑клиент
- Модуль `core/http.py`:
  - таймауты из ENV;
  - ретраи с экспоненциальным backoff + jitter;
  - поддержка прокси;
  - метрики (latency, retries, error‑rate).

6) Ошибки и контракты
- Глобальные exception‑handlers, единая структура ответов по RFC 7807 (Problem Details).
- Машиночитаемые коды: `E.OPENAI.TIMEOUT`, `E.HEYGEN.QUOTA`, `E.DB.CONSTRAINT` и т. п.

7) Наблюдаемость и стоимость
- `structlog` с JSON‑логами, `request‑id/trace‑id`.
- OpenTelemetry: трассировка контроллер → сервис → gateway → БД.
- Prometheus: latency per endpoint, внешние вызовы, токены/стоимость.

---

## Работа с LLM

8) Версионирование промптов
- В `ai/prompts.py` добавить атрибуты: `id`, `version`, `checksum`, `owner`, `changelog`.
- Хранить версии в файлах + БД; прокидывать `prompt_version` в создаваемые артефакты.

9) Жёсткие схемы на выходе
- Все ответы моделей валидировать pydantic‑схемами.
- При несовпадении — авто‑ремедиация (1 повтор) или сохранение в «черновик».

10) Offline‑оценка качества
- «Золотой» набор запросов и nightly‑скрипт сравнения по критериям (полнота полей, соблюдение ограничений, стабильность разбиений).

11) Модерация и PII
- Базовый модерационный фильтр и детектор PII до сохранения (эвристики/регулярки; в перспективе — сервис).

---

## HeyGen и мультимедиа‑таски

12) Надёжный polling/webhook
- Единая модель `jobs` для всех долгих задач.
- Эндпоинт `/api/jobs/{id}` со статусами `queued/running/succeeded/failed/canceled`, `progress`, `steps`.
- Расширенный «мок‑режим»: искусственные задержки, инъекции ошибок, предсказуемые фикстуры для e2e.

---

## Фронтенд (React + Ant Design)

13) Data‑layer: TanStack Query
- Кэш, ретраи, инвалидация по ключам (`courses`, `modules(courseId)`, `lessons(moduleId)`), оптимистичные апдейты.

14) Формы и валидация
- `zod` (+ resolvers) для строгой валидации payload’ов форм.

15) UX генеративной цепочки
- Пошаговый мастер: параметры → структура → детализация → слайды → экспорт.
- Diff‑просмотр версий, «Regenerate section» для точечной регенерации.

16) Редактор контента
- Markdown/MDX‑редактор с предпросмотром, авто‑сохранением и историей изменений на уровне урока.

17) i18n и доступность
- `react‑i18next`, проверка a11y: aria‑атрибуты, фокус‑ловушки модалок, контраст.

---

## Форматы и экспорт/импорт

18) Профили экспорта
- Варианты: JSON (внутренний с метаданными: `prompt_version`, `model`, `tokens`, `cost`, `generated_at`), Markdown/MDX, HTML/ZIP, PPTX.
- Профили: минимальный/полный.

---

## Безопасность и эксплуатация

19) Политики и заголовки
- CSP, HSTS, `X‑Frame‑Options`, `Referrer‑Policy`, `Permissions‑Policy`.
- Строгий CORS по whitelist из ENV; rate‑limit; лимит размера тела запросов.

20) Санитизация рендеринга
- DOM‑sanitizer для HTML/Markdown‑контента (ограничение опасных тегов/атрибутов).

21) Логи/бэкапы/алерты
- Централизованные логи (Loki/ELK), бэкапы БД (для SQLite — снапшоты; предпочтительно Postgres), алерты по 500‑rate/таймаутам/дорогим генерациям.

---

## Качество кода и тесты

22) Хуки и форматтеры
- `pre‑commit`: Black/Ruff (Python), Prettier/ESLint (frontend).

23) Тестовая пирамида
- Unit: сервисы/репозитории (моки OpenAI/HeyGen).
- Контрактные API‑тесты (Schemathesis по OpenAPI).
- Интеграционные (SQLite/Postgres, локально или в Docker).
- e2e (Playwright): сценарий мастера генерации и экспорта.
- Chaos‑флаги в gateway‑слое: задержки/ошибки для внешних сервисов.

---

## CI/CD и деплой

24) GitHub Actions
- Матрица: линты → тесты → сборка (client/server) → SBOM → security‑scan → релиз.

25) Docker multi‑stage
- Раздельные слои build/runtime, non‑root user, HEALTHCHECK, минимальные базовые образы.
- Интеграция с Render (`render.yaml`), healthcheck‑эндпоинты.

---

## Документация и DX

26) ADR и диаграммы
- ADR на ключевые решения (FastAPI vs Django, Postgres, фоновые job’ы).
- Диаграмма последовательности: параметры → генерация → детализация → экспорт → видео.

27) Примеры API
- В `README` добавить curl/httpie‑примеры и sample‑payload’ы; фикстуры JSON.

---

## Дорожная карта (6–8 недель)

Недели 1–2 (быстрые выигрыши)
- `pydantic‑settings`, строгий ENV, профили CORS/HTTPS.
- Единый HTTP‑клиент (таймауты/ретраи/прокси), глобальные хендлеры ошибок.
- Healthz/readiness.
- GitHub Actions: линт/тест/build, pre‑commit.

Недели 3–4
- Async‑клиенты, Redis + фоновые job’ы, таблица `jobs`, фронтовый polling.
- Alembic и переход на Postgres (dev — совместимость с SQLite).

Недели 5–6
- Версионирование промптов, жёсткие JSON‑схемы и авто‑ремедиация.
- TanStack Query, мастер генерации + diff‑просмотр; базовая модерация/PII.

Недели 7–8
- Экспорт/импорт (JSON/MD/HTML/PPTX), observability (OTel + Prometheus).
- Security‑заголовки, rate‑limit, e2e (Playwright).

---

## Быстрый старт внедрения (скелет файлов)

Рекомендуемые новые модули (без изменения существующей логики):
- `backend/core/settings.py` — типизированные ENV.
- `backend/core/http.py` — единый HTTP‑клиент (timeouts/retries/backoff/proxy).
- `backend/core/lifespan.py` — инициализация DI/БД/клиентов.
- `backend/services/jobs.py`, `backend/api/routes/jobs.py` — единая job‑модель и API.
- (Frontend) провайдер TanStack Query и клиент API.


