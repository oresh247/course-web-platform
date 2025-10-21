"""
OpenAI Client с поддержкой прокси
Адаптировано из TGBotCreateCourse проекта
"""
import openai
import json
import logging
import httpx
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Клиент для работы с OpenAI API с поддержкой прокси"""
    
    def __init__(self):
        # Получаем API ключ из переменных окружения
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
        
        # Настраиваем прокси из .env или используем прямое подключение
        proxy_url = os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')
        
        if proxy_url:
            logger.info(f"Используем прокси для OpenAI API")
            http_client = httpx.Client(
                verify=False, 
                timeout=120.0,  # Увеличенный таймаут для веб-версии
                proxies=proxy_url
            )
        else:
            logger.info("Прямое подключение к OpenAI API")
            http_client = httpx.Client(verify=False, timeout=120.0)
        
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
        """
        Генерирует структуру курса с помощью ChatGPT API
        
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
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": COURSE_GENERATION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"Получен ответ от OpenAI ({len(content)} символов)")
            
            # Извлекаем JSON из ответа
            json_content = self._extract_json_from_response(content)
            
            if json_content:
                logger.info(f"✅ Структура курса создана: {json_content.get('course_title', 'Без названия')}")
                return json_content
            else:
                logger.error("Не удалось извлечь JSON из ответа OpenAI")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при обращении к OpenAI API: {e}")
            return None
    
    def _extract_json_from_response(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Извлекает JSON из ответа ChatGPT
        
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
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 3000,
        response_format: Optional[Dict[str, str]] = None
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
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Ошибка при вызове OpenAI API: {e}")
            return None

