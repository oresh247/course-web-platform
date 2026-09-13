"""
Клиент для OpenAI API и OpenRouter с поддержкой прокси и настраиваемых таймаутов.

Поддерживаются два провайдера:
- OpenAI: задаётся OPENAI_API_KEY.
- OpenRouter (https://openrouter.ai/): задаётся OPENROUTER_API_KEY; при наличии
  этого ключа все вызовы идут через OpenRouter (модели в формате provider/model).

Используемые библиотеки:
- `openai` — официальный SDK (совместим с OpenRouter по base_url).
- `httpx` — HTTP‑клиент для прокси и таймаутов.

Примечание: в корпоративных сетях может понадобиться `HTTPS_PROXY`.
"""
import openai
import json
import logging
import httpx
import os
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Клиент для работы с OpenAI API или OpenRouter с поддержкой прокси.

    - Выбор провайдера: если задан OPENROUTER_API_KEY — используется OpenRouter,
      иначе OPENAI_API_KEY (OpenAI).
    - Работает через прокси (HTTPS_PROXY) для обоих провайдеров.
    - Логирует метрики (время, токены, ретраи) для диагностики.
    """

    def __init__(self):
        from backend.config import settings

        use_openrouter = settings.USE_OPENROUTER
        proxy_url = settings.HTTPS_PROXY or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
        timeout = float(settings.OPENAI_TIMEOUT or 120.0)

        if use_openrouter:
            api_key = settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENROUTER_API_KEY не найден. Задайте OPENROUTER_API_KEY в .env или "
                    "используйте OPENAI_API_KEY для работы через OpenAI."
                )
            base_url = settings.OPENROUTER_BASE_URL or "https://openrouter.ai/api/v1"
            self._use_openrouter = True
            if proxy_url:
                logger.info("Используем OpenRouter API через прокси")
            else:
                logger.info("Используем OpenRouter API (прямое подключение)")
        else:
            api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY не найден. Задайте OPENAI_API_KEY в .env или "
                    "OPENROUTER_API_KEY для работы через OpenRouter."
                )
            base_url = None
            self._use_openrouter = False
            if proxy_url:
                logger.info("Используем OpenAI API через прокси")
            else:
                logger.info("Используем OpenAI API (прямое подключение)")

        if proxy_url:
            http_client = httpx.Client(verify=False, timeout=timeout, proxies=proxy_url)
        else:
            http_client = httpx.Client(verify=False, timeout=timeout)

        create_kwargs: Dict[str, Any] = {
            "api_key": api_key,
            "http_client": http_client,
        }
        if base_url:
            create_kwargs["base_url"] = base_url

        self.client = openai.OpenAI(**create_kwargs)
    
    def generate_course_structure(
        self, 
        topic: str, 
        audience_level: str, 
        module_count: int, 
        course_goals: Optional[str] = None,
        duration_weeks: int = None, 
        hours_per_week: int = None
    ) -> Optional[Dict[str, Any]]:
        """Генерирует структуру курса с помощью Chat Completions.

        Args:
            topic: Тема курса
            audience_level: Уровень аудитории (junior/middle/senior)
            module_count: Количество модулей
            course_goals: Цели и задачи курса (может быть None)
            duration_weeks: Длительность в неделях
            hours_per_week: Часов в неделю
            
        Returns:
            JSON структура курса или None при ошибке
        """
        try:
            from .prompts import COURSE_GENERATION_SYSTEM_PROMPT, COURSE_GENERATION_PROMPT_TEMPLATE
            
            # Формируем строку длительности
            duration_text = ""
            if duration_weeks and hours_per_week:
                duration_text = f"{duration_weeks} недель, {hours_per_week} часов в неделю"
            elif duration_weeks:
                duration_text = f"{duration_weeks} недель"
            else:
                duration_text = "8 недель, 5 часов в неделю"
            
            course_goals_text = course_goals.strip() if course_goals and course_goals.strip() else "Не указаны"

            from backend.config import settings
            model = settings.OPENAI_MODEL_DEFAULT

            for attempt in range(2):
                prompt = COURSE_GENERATION_PROMPT_TEMPLATE.format(
                    topic=topic,
                    course_goals=course_goals_text,
                    audience=audience_level,
                    num_modules=module_count,
                    duration=duration_text
                )
                if attempt > 0:
                    prompt = f"{prompt}\n\nКРИТИЧЕСКИ ВАЖНО: верни РОВНО {module_count} модулей."

                logger.info(f"Генерируем структуру курса: {topic} для {audience_level}")

                json_content = self.call_ai_json(
                    system_prompt=COURSE_GENERATION_SYSTEM_PROMPT,
                    user_prompt=prompt,
                    model=model,
                    temperature=0.7,
                    max_tokens=settings.OPENAI_MAX_TOKENS_COURSE_STRUCTURE,
                    retries=settings.OPENAI_RETRIES_DEFAULT,
                    backoff_seconds=settings.OPENAI_BACKOFF_SECONDS_DEFAULT,
                )

                if not json_content:
                    logger.error("Не удалось извлечь JSON из ответа OpenAI")
                    continue

                # Постобработка: гарантируем, что estimated_time_minutes >= 15 для всех уроков
                self._normalize_lesson_times(json_content)

                if not self._validate_module_count(json_content, module_count):
                    logger.warning(
                        f"Модель вернула неверное количество модулей. "
                        f"Ожидалось: {module_count}, получено: {len(json_content.get('modules', []))}"
                    )
                    continue

                logger.info(f"✅ Структура курса создана: {json_content.get('course_title', 'Без названия')}")
                return json_content

            logger.error("Не удалось получить структуру курса с корректным количеством модулей")
            return None
                
        except Exception as e:
            logger.error(f"Ошибка при обращении к OpenAI API: {e}")
            return None
    
    def _normalize_lesson_times(self, course_data: Dict[str, Any]) -> None:
        """Нормализует estimated_time_minutes для всех уроков: гарантирует >= 15 минут.
        
        Args:
            course_data: Словарь с данными курса (будет изменен in-place)
        """
        if "modules" not in course_data:
            return
        
        for module in course_data.get("modules", []):
            if "lessons" not in module:
                continue
            
            for lesson in module.get("lessons", []):
                if "estimated_time_minutes" in lesson:
                    time_minutes = lesson["estimated_time_minutes"]
                    # Если значение меньше 15, устанавливаем минимум 15
                    if isinstance(time_minutes, (int, float)) and time_minutes < 15:
                        logger.warning(
                            f"Исправлено время урока '{lesson.get('lesson_title', 'Без названия')}': "
                            f"{time_minutes} -> 15 минут"
                        )
                        lesson["estimated_time_minutes"] = 15
                    # Если значение больше 480, ограничиваем до 480
                    elif isinstance(time_minutes, (int, float)) and time_minutes > 480:
                        logger.warning(
                            f"Исправлено время урока '{lesson.get('lesson_title', 'Без названия')}': "
                            f"{time_minutes} -> 480 минут"
                        )
                        lesson["estimated_time_minutes"] = 480
    
    def _extract_json_from_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Извлекает JSON из текстового ответа модели.

        Args:
            content: Текст ответа от API
            
        Returns:
            Распарсенный JSON или None
        """
        try:
            # Удаляем markdown блоки если есть
            content = content.replace('```json', '').replace('```', '').strip()
            
            # Ищем JSON блок в ответе
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Если JSON не найден, пытаемся распарсить весь контент
                return json.loads(content)
                
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            logger.debug(f"Проблемный контент: {content[:500]}...")
            return None

    def _validate_module_count(self, course_data: Dict[str, Any], expected_count: int) -> bool:
        modules = course_data.get("modules")
        if not isinstance(modules, list):
            logger.warning("Поле 'modules' отсутствует или имеет неверный тип")
            return False

        if len(modules) != expected_count:
            return False

        module_numbers: List[int] = []
        for module in modules:
            if not isinstance(module, dict):
                return False
            module_number = module.get("module_number")
            if not isinstance(module_number, int):
                return False
            module_numbers.append(module_number)

        return module_numbers == list(range(1, expected_count + 1))
    
    def call_ai(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        response_format: Optional[Dict[str, Any]] = None,
        retries: int = None,
        backoff_seconds: float = None
    ) -> Optional[str]:
        """
        Универсальный метод для вызова OpenAI API
        
        Args:
            system_prompt: Системный промпт
            user_prompt: Промпт пользователя
            model: Модель GPT
            temperature: Температура генерации
            max_tokens: Максимум токенов
            response_format: Формат ответа (например {"type": "json_object"}
                или строгая JSON Schema).
            
        Returns:
            Текст ответа или None
        """
        from backend.config import settings
        # Применяем значения по умолчанию из settings при отсутствии явных аргументов
        if model is None:
            model = settings.OPENAI_MODEL_DEFAULT
        if temperature is None:
            temperature = settings.OPENAI_TEMPERATURE_DEFAULT
        if max_tokens is None:
            max_tokens = settings.OPENAI_MAX_TOKENS_DEFAULT
        if retries is None:
            retries = settings.OPENAI_RETRIES_DEFAULT
        if backoff_seconds is None:
            backoff_seconds = settings.OPENAI_BACKOFF_SECONDS_DEFAULT

        import time
        start_time = time.time()
        attempt = 0
        last_error: Optional[Exception] = None
        while attempt <= retries:
            try:
                kwargs = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
                if response_format:
                    kwargs["response_format"] = response_format
                response = self.client.chat.completions.create(**kwargs)
                latency_ms = int((time.time() - start_time) * 1000)
                usage = getattr(response, "usage", None)
                total_tokens = getattr(usage, "total_tokens", None) if usage else None
                prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
                completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
                message = response.choices[0].message
                text = self._extract_message_text(message)
                logger.info(
                    f"OpenAI call ok | model={kwargs['model']} temp={kwargs['temperature']} max_tokens={kwargs['max_tokens']} "
                    f"attempt={attempt+1} latency_ms={latency_ms} tokens_total={total_tokens} tokens_prompt={prompt_tokens} tokens_completion={completion_tokens}"
                )
                if not text:
                    raise ValueError(
                        "Модель вернула HTTP 200 без текста в content/reasoning"
                    )
                return text
            except Exception as e:
                last_error = e
                logger.warning(f"OpenAI call fail attempt {attempt + 1}/{retries + 1}: {e}")
                if attempt == retries:
                    break
                try:
                    time.sleep(backoff_seconds * (2 ** attempt))
                except Exception:
                    pass
                attempt += 1
        total_duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"OpenAI call failed after {retries + 1} attempts in {total_duration_ms} ms: {last_error}")
        return None

    def call_ai_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        retries: int = None,
        backoff_seconds: float = None,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Вызывает модель и возвращает распарсенный JSON-объект.

        ``json_schema`` опционально включает Structured Outputs. Принимается
        либо definition из ``name``, ``schema`` и необязательного ``strict``,
        либо чистая JSON Schema (она будет обёрнута в definition). По умолчанию
        schema используется в строгом режиме.

        Поддержка response_format зависит от конкретной модели и провайдера.
        Поэтому форматы пробуются по убывающей строгости: JSON Schema,
        json_object, обычный текст с извлечением JSON. Неподдерживаемый формат
        не блокирует интервью и не повторяется много раз.
        """
        from backend.config import settings
        if model is None:
            model = settings.OPENAI_MODEL_DEFAULT

        # Для явной схемы сначала пробуем строгий режим. Одна попытка важна:
        # если выбранная OpenRouter-модель не поддерживает JSON Schema, повтор
        # того же запроса только расходует лимит и не помогает пользователю.
        if json_schema is not None:
            schema_response_format = self._build_json_schema_response_format(json_schema)
            if schema_response_format is not None:
                parsed = self._call_and_parse_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=schema_response_format,
                    retries=0,
                    backoff_seconds=backoff_seconds,
                )
                if parsed is not None:
                    return parsed
                logger.warning(
                    "Structured Outputs недоступен или вернул невалидный JSON "
                    "для model=%s; пробуем совместимый fallback",
                    model,
                )

        # Список моделей, которые поддерживают JSON mode (OpenAI и OpenRouter-идентификаторы)
        json_mode_models = [
            "gpt-4-turbo-preview", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k",
            "claude-3", "claude-3.5", "claude-3-opus", "claude-3-sonnet",
        ]
        # У OpenRouter поддержка JSON mode определяется маршрутом к конкретной
        # модели. Делаем одну попытку и ниже обязательно откатываемся к обычному
        # вызову, если endpoint отверг response_format.
        use_json_mode = self._use_openrouter or any(
            json_model in model.lower() for json_model in json_mode_models
        )

        if use_json_mode:
            parsed = self._call_and_parse_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                retries=0,
                backoff_seconds=backoff_seconds,
            )
            if parsed is not None:
                return parsed
            logger.warning(
                "JSON mode недоступен или вернул невалидный JSON для model=%s; "
                "используем текстовый fallback",
                model,
            )

        # Финальный fallback сохраняет прежнюю возможность получать JSON от
        # моделей без response_format. Здесь оставляем обычное число ретраев:
        # это уже не ошибка совместимости формата, а реальный сетевой вызов.
        return self._call_and_parse_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=None,
            retries=retries,
            backoff_seconds=backoff_seconds,
        )

    @staticmethod
    def _normalize_text_payload(value: Any) -> Optional[str]:
        """Сводит строку, список частей или вложенный объект к непустому тексту."""
        if value is None:
            return None
        if isinstance(value, str):
            text = value.strip()
            return text or None
        if isinstance(value, list):
            parts: List[str] = []
            for item in value:
                if isinstance(item, (str, list)):
                    raw_item: Any = item
                elif isinstance(item, dict):
                    raw_item = item.get("text") or item.get("content")
                else:
                    raw_item = getattr(item, "text", None) or getattr(item, "content", None)
                part = OpenAIClient._normalize_text_payload(raw_item)
                if part:
                    parts.append(part)
            joined = "\n".join(parts).strip()
            return joined or None
        return None

    @staticmethod
    def _extract_message_text(message: Any) -> Optional[str]:
        """Читает ответ модели из content, затем из reasoning-полей.

        Reasoning-модели OpenRouter часто оставляют ``content=None`` и кладут
        текст в ``reasoning`` / ``reasoning_content``. Пустой content больше
        не считается исключением: JSON-fallback остаётся только если текста нет
        или из него не собирается JSON.
        """
        if message is None:
            return None

        content = OpenAIClient._normalize_text_payload(getattr(message, "content", None))
        if content:
            return content

        for field_name in ("reasoning", "reasoning_content"):
            reasoning = OpenAIClient._normalize_text_payload(getattr(message, field_name, None))
            if reasoning:
                logger.info("Ответ модели взят из поля %s, content пуст", field_name)
                return reasoning

        if isinstance(message, dict):
            content = OpenAIClient._normalize_text_payload(message.get("content"))
            if content:
                return content
            for field_name in ("reasoning", "reasoning_content"):
                reasoning = OpenAIClient._normalize_text_payload(message.get(field_name))
                if reasoning:
                    logger.info("Ответ модели взят из поля %s, content пуст", field_name)
                    return reasoning
        return None

    @staticmethod
    def _build_json_schema_response_format(
        json_schema: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Нормализует schema definition в Chat Completions response_format.

        Поддерживаются оба удобных входа:

        * ``{"name": "result", "schema": {...}, "strict": True}``;
        * чистая JSON Schema, например ``{"type": "object", ...}``.

        Также допускается уже собранный ``{"type": "json_schema",
        "json_schema": {...}}``. Некорректная схема не ломает основной
        fallback и только пропускает попытку Structured Outputs.
        """
        if not isinstance(json_schema, dict):
            logger.warning("json_schema должен быть объектом; Structured Outputs пропущен")
            return None

        if json_schema.get("type") == "json_schema":
            definition = json_schema.get("json_schema")
            if not isinstance(definition, dict):
                logger.warning("json_schema.json_schema должен быть объектом")
                return None
            definition = dict(definition)
        elif "schema" in json_schema:
            definition = dict(json_schema)
        else:
            definition = {
                "name": "structured_response",
                "schema": dict(json_schema),
            }

        schema = definition.get("schema")
        if not isinstance(schema, dict):
            logger.warning("json_schema.schema должен быть объектом")
            return None

        definition.setdefault("name", "structured_response")
        definition.setdefault("strict", True)
        return {"type": "json_schema", "json_schema": definition}

    def _call_and_parse_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
        response_format: Optional[Dict[str, Any]],
        retries: Optional[int],
        backoff_seconds: Optional[float],
    ) -> Optional[Dict[str, Any]]:
        """Выполняет один вариант формата и извлекает JSON из его ответа."""
        content = self.call_ai(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            retries=retries,
            backoff_seconds=backoff_seconds,
        )
        if content is None:
            return None

        try:
            return json.loads(content)
        except Exception:
            from backend.ai.json_sanitizer import extract_json
            return extract_json(content, expected_key=None)
