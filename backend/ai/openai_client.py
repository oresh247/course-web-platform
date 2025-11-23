"""
Клиент для OpenAI API с поддержкой прокси и настраиваемых таймаутов.

Используемые библиотеки:
- `openai` — официальный SDK для обращения к Chat Completions и др.
- `httpx` — HTTP‑клиент, позволяет гибко настраивать прокси и таймауты,
  здесь мы передаём его в OpenAI SDK как транспорт.

Примечание: в корпоративных сетях может понадобиться `HTTPS_PROXY`.
"""
import openai
import json
import logging
import httpx
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Клиент для работы с OpenAI API с поддержкой прокси.

    - Автоматически берёт ключ из `settings`/переменных окружения.
    - Умеет работать через прокси (`HTTPS_PROXY`).
    - Логирует метрики (время, токены, ретраи) для диагностики.
    """
    
    def __init__(self):
        from backend.config import settings
        # Получаем API ключ из переменных окружения
        api_key = settings.OPENAI_API_KEY or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
        
        # Настраиваем прокси из .env или используем прямое подключение
        proxy_url = settings.HTTPS_PROXY or os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')
        
        if proxy_url:
            logger.info(f"Используем прокси для OpenAI API")
            http_client = httpx.Client(
                verify=False,
                timeout=float(settings.OPENAI_TIMEOUT or 120.0),
                proxies=proxy_url
            )
        else:
            logger.info("Прямое подключение к OpenAI API")
            http_client = httpx.Client(verify=False, timeout=float(settings.OPENAI_TIMEOUT or 120.0))
        
        self.client = openai.OpenAI(
            api_key=api_key,
            http_client=http_client
        )
    
    def generate_course_structure(
        self, 
        topic: str, 
        audience_level: str, 
        module_count: int, 
        duration_weeks: int = None, 
        hours_per_week: int = None
    ) -> Optional[Dict[str, Any]]:
        """Генерирует структуру курса с помощью Chat Completions.

        Args:
            topic: Тема курса
            audience_level: Уровень аудитории (junior/middle/senior)
            module_count: Количество модулей
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
            
            prompt = COURSE_GENERATION_PROMPT_TEMPLATE.format(
                topic=topic,
                audience=audience_level,
                num_modules=module_count,
                duration=duration_text
            )
            
            logger.info(f"Генерируем структуру курса: {topic} для {audience_level}")
            
            from backend.config import settings
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": COURSE_GENERATION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS_DEFAULT,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"Получен ответ от OpenAI ({len(content)} символов)")
            
            # Извлекаем JSON из ответа
            json_content = self._extract_json_from_response(content)
            
            if json_content:
                # Постобработка: гарантируем, что estimated_time_minutes >= 15 для всех уроков
                self._normalize_lesson_times(json_content)
                logger.info(f"✅ Структура курса создана: {json_content.get('course_title', 'Без названия')}")
                return json_content
            else:
                logger.error("Не удалось извлечь JSON из ответа OpenAI")
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
    
    def call_ai(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        response_format: Optional[Dict[str, str]] = None,
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
            response_format: Формат ответа (например {"type": "json_object"})
            
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
                logger.info(
                    f"OpenAI call ok | model={kwargs['model']} temp={kwargs['temperature']} max_tokens={kwargs['max_tokens']} "
                    f"attempt={attempt+1} latency_ms={latency_ms} tokens_total={total_tokens} tokens_prompt={prompt_tokens} tokens_completion={completion_tokens}"
                )
                return response.choices[0].message.content.strip()
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
        backoff_seconds: float = None
    ) -> Optional[Dict[str, Any]]:
        """Вызывает модель в JSON-режиме и парсит результат в dict.
        Возвращает None, если парсинг не удался.
        Если модель не поддерживает JSON mode, делает fallback на обычный вызов.
        """
        from backend.config import settings
        if model is None:
            model = settings.OPENAI_MODEL_DEFAULT
        
        # Список моделей, которые поддерживают JSON mode
        json_mode_models = [
            "gpt-4-turbo-preview", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
        ]
        
        # Пытаемся использовать JSON mode, если модель поддерживает
        use_json_mode = any(json_model in model.lower() for json_model in json_mode_models)
        
        if use_json_mode:
            content = self.call_ai(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                retries=retries,
                backoff_seconds=backoff_seconds,
            )
        else:
            # Fallback: вызываем без JSON mode и парсим ответ
            logger.warning(f"Модель {model} не поддерживает JSON mode, используем fallback")
            content = self.call_ai(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=None,
                retries=retries,
                backoff_seconds=backoff_seconds,
            )
        
        if content is None:
            return None
        try:
            # Пытаемся распарсить JSON
            return json.loads(content)
        except Exception:
            # Fallback: попытаться вытащить JSON из текста
            from backend.ai.json_sanitizer import extract_json
            return extract_json(content, expected_key=None)

