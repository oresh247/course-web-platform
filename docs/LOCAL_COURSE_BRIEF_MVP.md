# Локальная проверка Course Brief MVP

Этот сценарий запускает новый экран `/create` вместе с изолированным backend
для интервью. Он не требует ключа OpenAI или OpenRouter и не выполняет внешних
AI-запросов: локальный клиент создаёт детерминированный черновик, а финальная
структура собирается существующим fallback-алгоритмом.

## Подготовка

Из корня репозитория один раз создайте виртуальное окружение и установите
backend-зависимости:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
```

Установите frontend-зависимости:

```powershell
Set-Location .\frontend
npm install
Set-Location ..
```

## Запуск

В первом терминале запустите изолированный API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.local_demo:app --reload --host 127.0.0.1 --port 8000
```

Он использует SQLite-файл `.local/course-brief-demo.db`; рабочая база курсов
не затрагивается. Проверка доступности: <http://127.0.0.1:8000/api/health>.

Во втором терминале запустите UI:

```powershell
Set-Location .\frontend
$env:VITE_API_URL = 'http://127.0.0.1:8000'
npm run dev -- --host 127.0.0.1 --strictPort
```

Если `npm` не добавлен в `PATH`, используйте подготовленный PowerShell-скрипт:

```powershell
Set-Location .\frontend
.\start-local-demo.ps1
```

Он сначала ищет системный `node`, а затем использует runtime Codex. Если
политика PowerShell запрещает выполнение скриптов, запустите его так:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-local-demo.ps1
```

Откройте <http://127.0.0.1:3000/create>.

## Что проверить вручную

1. Введите тему и начните диалог.
2. Убедитесь, что справа показаны `0%`, число вопросов и оставшееся количество, но не черновой outline.
3. Для каждого вопроса выберите глубину; часть разделов можно пропустить.
4. Проверьте рост прогресса и финальную структуру на `100%`.
5. Нажмите «Новый диалог» и убедитесь, что начинается новая сессия.

## Автоматический smoke

Пока API из первого терминала запущен, в третьем терминале выполните:

```powershell
.\.venv\Scripts\python.exe .\backend\tools\smoke_course_brief_demo.py
```

Скрипт проверяет HTTP-контракт, отсутствие черновой структуры в ответах,
восстановление состояния, прогресс, финализацию и защиту от устаревшего ответа
через `409 Conflict`.

## Проверка с настоящей моделью

Для реального AI-сценария создайте `backend/.env` из `backend/env.example`,
задайте `OPENAI_API_KEY` или `OPENROUTER_API_KEY` и запустите обычное
приложение:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Затем используйте тот же frontend. Demo-entrypoint предназначен только для
локальной проверки Course Brief MVP и не заменяет обычный backend.
