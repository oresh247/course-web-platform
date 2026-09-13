# OpenRouter для интервью Course Brief

Этот документ относится к обычному backend (`backend.main`). Он нужен, когда
интервью по структуре курса должно обращаться к настоящей модели. Для
локального демонстрационного сценария ключ не нужен.

## Настройка

Из корня репозитория один раз создайте локальный файл конфигурации, если его
ещё нет:

```powershell
Copy-Item -LiteralPath .\backend\env.example -Destination .\backend\.env
```

Откройте `backend/.env` и укажите свой ключ, не добавляя его в Git:

```dotenv
OPENROUTER_API_KEY=ваш_ключ_OpenRouter

# Модель для основной генерации структуры курса.
OPENAI_MODEL_DEFAULT=provider/model

# Необязательно. Если не задано, используется OPENAI_MODEL_DEFAULT.
COURSE_BRIEF_INTERVIEW_MODEL=provider/model
COURSE_BRIEF_INTERVIEW_TEMPERATURE=0.2
COURSE_BRIEF_INTERVIEW_MAX_TOKENS=1200

COURSE_BRIEF_DEMO_MODE=false
```

`provider/model` — точный идентификатор модели из каталога OpenRouter на
момент настройки. Для воспроизводимого поведения задавайте конкретную модель,
а не маршрут, который выбирает модель автоматически. Доступность бесплатных
моделей и поддержка Structured Outputs меняются, поэтому перед выбором
проверяйте её карточку в каталоге OpenRouter.

Настройки загружаются именно из `backend/.env`, независимо от того, запущен
uvicorn из корня репозитория или из каталога `backend`. Переменные среды,
заданные в операционной системе, имеют приоритет над файлом.

## Запуск с настоящей моделью

```powershell
Set-Location C:\projects\course-web-platform
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

При заданном `OPENROUTER_API_KEY` обычный `backend.main` создаёт
`OpenAIClient` с OpenRouter base URL. Внешний запрос происходит только тогда,
когда endpoint действительно запускает генерацию или интерпретацию ответа
пользователя.

## Чем отличается local demo

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.local_demo:app --reload --host 127.0.0.1 --port 8000
```

`backend.local_demo` перед импортом маршрутов принудительно включает
`COURSE_BRIEF_DEMO_MODE=true`. Поэтому `CourseBriefService` использует
детерминированный `CourseBriefDemoClient`; он не создаёт `OpenAIClient` и не
вызывает ни OpenRouter, ни OpenAI, даже если ключ находится в `backend/.env`.
Этот режим предназначен для проверки интерфейса и базового сценария, а не
качества промпта.

## Строгий JSON для интервью

`OpenAIClient.call_ai_json` принимает дополнительный аргумент `json_schema`.
Передайте definition с именем, схемой и строгим режимом:

```python
result = client.call_ai_json(
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    model=settings.COURSE_BRIEF_INTERVIEW_MODEL,
    temperature=settings.COURSE_BRIEF_INTERVIEW_TEMPERATURE,
    max_tokens=settings.COURSE_BRIEF_INTERVIEW_MAX_TOKENS,
    json_schema={
        "name": "course_brief_interview",
        "strict": True,
        "schema": interview_result_schema,
    },
)
```

Можно передать и чистую JSON Schema: клиент сам добавит имя и `strict: true`.
Схема задаёт формат транспорта, но backend всё равно должен валидировать
содержимое Pydantic-моделью до сохранения решения.

Поддержка `response_format` неодинакова у моделей и маршрутов OpenRouter.
Поэтому клиент пробует форматы в такой последовательности:

1. строгая `json_schema`, если она передана;
2. совместимый `json_object`, если модель обычно поддерживает JSON mode;
3. обычный текстовый ответ с безопасным извлечением JSON.

Для каждого structured-формата выполняется одна попытка. Если провайдер его
отклонил, клиент не расходует все ретраи на тот же неподдерживаемый параметр,
а переходит к следующему варианту. Настроенные ретраи применяются к финальному
обычному вызову.

## Быстрая локальная проверка без сети

После установки backend-зависимостей выполните:

```powershell
.\.venv\Scripts\python.exe .\backend\tools\test_openai_client_json_fallback.py
```

Проверка использует фальшивый клиент и не требует ключа, не запускает сервер и
не делает внешних запросов.
