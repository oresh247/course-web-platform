"""
Генератор учебного контента для модулей курса
"""
import logging
import json
from typing import Optional, Dict, Any, List

from backend.models.domain import (
    Module, Lecture, Slide, ModuleContent,
    Lesson, LessonContent, TopicMaterial, GeneratedLecture
)
from backend.config import settings
from backend.ai.cache import make_cache_key, get as cache_get, set as cache_set
from backend.ai.openai_client import OpenAIClient
from backend.ai.interfaces import AIChatClient
from backend.ai.json_sanitizer import extract_json
from backend.ai.prompts import (
    MODULE_CONTENT_SYSTEM_PROMPT,
    MODULE_CONTENT_PROMPT_TEMPLATE,
    TOPIC_MATERIAL_SYSTEM_PROMPT,
    TOPIC_MATERIAL_PROMPT_TEMPLATE,
    format_lessons_list,
    format_content_outline,
    LESSON_DETAILED_SYSTEM_PROMPT,
    LESSON_DETAILED_PROMPT_TEMPLATE
)

logger = logging.getLogger(__name__)


class ContentGenerator:
    """Класс для генерации учебного контента модулей"""
    
    def __init__(self, ai_client: AIChatClient | None = None):
        self.openai_client: AIChatClient = ai_client or OpenAIClient()
    
    def generate_lesson_detailed_content(
        self,
        lesson,
        module: Module,
        course_title: str,
        target_audience: str
    ) -> Optional[Dict[str, Any]]:
        """
        Генерирует детальный контент для одного урока (слайды)
        
        Args:
            lesson: Урок (Lesson object)
            module: Модуль
            course_title: Название курса
            target_audience: Целевая аудитория
            
        Returns:
            Словарь с детальным контентом урока или None
        """
        logger.info(f"Генерируем детальный контент для урока: {lesson.lesson_title}")
        
        try:
            prompt = LESSON_DETAILED_PROMPT_TEMPLATE.format(
                course_title=course_title,
                target_audience=target_audience,
                module_title=module.module_title,
                lesson_title=lesson.lesson_title,
                lesson_goal=lesson.lesson_goal,
                lesson_format=lesson.format,
                lesson_time=lesson.estimated_time_minutes,
                content_outline=format_content_outline(lesson.content_outline),
            )

            # Кэш-ключ по содержанию запроса
            cache_key = make_cache_key(
                "lesson_detailed",
                settings.PROMPT_VERSION,
                LESSON_DETAILED_SYSTEM_PROMPT,
                prompt,
                settings.OPENAI_MODEL_DETAILED_CONTENT,
                str(0.3),
            )
            if settings.AI_CACHE_ENABLED:
                cached = cache_get(cache_key)
                if cached is not None:
                    logger.info("cache hit: lesson_detailed")
                    return cached

            content_json = self.openai_client.call_ai_json(
                system_prompt=LESSON_DETAILED_SYSTEM_PROMPT,
                user_prompt=prompt,
                model=settings.OPENAI_MODEL_DETAILED_CONTENT,
                temperature=0.3,
                max_tokens=settings.OPENAI_MAX_TOKENS_LESSON_DETAILED,
            )
            if not content_json:
                logger.warning("❌ JSON mode вернул пустой результат для урока")
                return None
            # Валидация pydantic
            try:
                _ = GeneratedLecture(**content_json)
            except Exception as e:
                logger.warning(f"❌ Невалидная структура лекции: {e}")
                return None
            if 'slides' in content_json and isinstance(content_json['slides'], list):
                logger.info(f"✅ Контент урока сгенерирован: {len(content_json['slides'])} слайдов")
                if settings.AI_CACHE_ENABLED:
                    cache_set(cache_key, content_json, settings.AI_CACHE_TTL_SECONDS)
                return content_json
            logger.warning(f"❌ Неправильная структура урока. Ключи: {list(content_json.keys())}")
            return None
                
        except Exception as e:
            logger.error(f"Ошибка генерации контента урока: {e}")
            return None
    
    def generate_module_content(
        self, 
        module: Module, 
        course_title: str, 
        target_audience: str
    ) -> Optional[ModuleContent]:
        """
        Генерирует полный контент для модуля включая лекции и слайды
        
        Args:
            module: Модуль курса
            course_title: Название курса
            target_audience: Целевая аудитория
            
        Returns:
            ModuleContent с лекциями и слайдами или None
        """
        logger.info(f"Генерируем контент для модуля: {module.module_title}")
        
        # Попытка 1: JSON mode
        result = self._try_json_mode(module, course_title, target_audience)
        if result:
            return result
        
        # Попытка 2: Обычный текстовый режим
        result = self._try_text_mode(module, course_title, target_audience)
        if result:
            return result
        
        # Fallback: Тестовый контент
        logger.warning("📌 Все методы генерации провалились, используем тестовый контент")
        return self._get_test_module_content(module)
    
    def _try_json_mode(
        self, 
        module: Module, 
        course_title: str, 
        target_audience: str
    ) -> Optional[ModuleContent]:
        """Попытка генерации через JSON mode"""
        try:
            logger.info("🔧 Пробуем JSON mode...")
            
            prompt = MODULE_CONTENT_PROMPT_TEMPLATE.format(
                course_title=course_title,
                target_audience=target_audience,
                module_number=module.module_number,
                module_title=module.module_title,
                module_goal=module.module_goal,
                lessons_list=format_lessons_list(module.lessons),
                num_lessons=len(module.lessons)
            )
            
            # Кэш-ключ по содержанию запроса
            cache_key = make_cache_key(
                "module_json_mode",
                settings.PROMPT_VERSION,
                MODULE_CONTENT_SYSTEM_PROMPT + "|json",
                prompt,
                settings.OPENAI_MODEL_DETAILED_CONTENT,
                str(0.3),
            )
            if settings.AI_CACHE_ENABLED:
                cached = cache_get(cache_key)
                if cached is not None:
                    logger.info("cache hit: module_json_mode")
                    try:
                        return ModuleContent(**cached)
                    except Exception:
                        pass

            json_content = self.openai_client.call_ai_json(
                system_prompt=MODULE_CONTENT_SYSTEM_PROMPT + "\n\nВЫВОД ТОЛЬКО В JSON ФОРМАТЕ!",
                user_prompt=prompt,
                model=settings.OPENAI_MODEL_DETAILED_CONTENT,
                temperature=0.3,
                max_tokens=settings.OPENAI_MAX_TOKENS_MODULE_CONTENT,
            )
            
            if json_content and "lectures" in json_content:
                # Добавляем обязательные поля
                for lecture in json_content["lectures"]:
                    lecture["module_number"] = module.module_number
                    lecture["module_title"] = module.module_title
                
                total_slides = sum(len(lecture.get("slides", [])) for lecture in json_content["lectures"])
                total_duration = sum(lecture.get("duration_minutes", 0) for lecture in json_content["lectures"])
                
                json_content["total_slides"] = total_slides
                json_content["estimated_duration_minutes"] = total_duration
                
                module_content = ModuleContent(**json_content)
                logger.info(f"✅ JSON mode успешно: {len(module_content.lectures)} лекций, {total_slides} слайдов")
                if settings.AI_CACHE_ENABLED:
                    cache_set(cache_key, json_content, settings.AI_CACHE_TTL_SECONDS)
                return module_content
            else:
                logger.warning("❌ JSON mode вернул неправильную структуру")
                return None
                
        except Exception as e:
            logger.warning(f"❌ JSON mode не сработал: {e}")
            return None
    
    def _try_text_mode(
        self, 
        module: Module, 
        course_title: str, 
        target_audience: str
    ) -> Optional[ModuleContent]:
        """Попытка генерации в обычном текстовом режиме"""
        try:
            logger.info("🔧 Пробуем обычный текстовый режим...")
            
            prompt = MODULE_CONTENT_PROMPT_TEMPLATE.format(
                course_title=course_title,
                target_audience=target_audience,
                module_number=module.module_number,
                module_title=module.module_title,
                module_goal=module.module_goal,
                lessons_list=format_lessons_list(module.lessons),
                num_lessons=len(module.lessons)
            )
            
            # Кэш-ключ по содержанию запроса
            cache_key = make_cache_key(
                "module_text_mode",
                settings.PROMPT_VERSION,
                MODULE_CONTENT_SYSTEM_PROMPT,
                prompt,
                "gpt-4",
                str(0.3),
            )
            if settings.AI_CACHE_ENABLED:
                cached = cache_get(cache_key)
                if cached is not None:
                    logger.info("cache hit: module_text_mode")
                    try:
                        return ModuleContent(**cached)
                    except Exception:
                        pass

            content = self.openai_client.call_ai(
                system_prompt=MODULE_CONTENT_SYSTEM_PROMPT,
                user_prompt=prompt,
                model="gpt-4",
                temperature=0.3,
                max_tokens=settings.OPENAI_MAX_TOKENS_LESSON_DETAILED,
            )
            if not content:
                return None
            json_content = extract_json(content, expected_key="lectures")
            
            if json_content and "lectures" in json_content:
                # Добавляем обязательные поля
                for lecture in json_content["lectures"]:
                    lecture["module_number"] = module.module_number
                    lecture["module_title"] = module.module_title
                
                total_slides = sum(len(lecture.get("slides", [])) for lecture in json_content["lectures"])
                total_duration = sum(lecture.get("duration_minutes", 0) for lecture in json_content["lectures"])
                
                json_content["total_slides"] = total_slides
                json_content["estimated_duration_minutes"] = total_duration
                
                module_content = ModuleContent(**json_content)
                logger.info(f"✅ Текстовый режим успешно: {len(module_content.lectures)} лекций, {total_slides} слайдов")
                if settings.AI_CACHE_ENABLED:
                    cache_set(cache_key, json_content, settings.AI_CACHE_TTL_SECONDS)
                return module_content
            else:
                logger.warning("❌ Текстовый режим вернул неправильную структуру")
                return None
                
        except Exception as e:
            logger.warning(f"❌ Текстовый режим не сработал: {e}")
            return None
    
    def _extract_json(self, content: str, expected_key: str = "lectures") -> Optional[Dict[str, Any]]:
        # Делегируем общему санитайзеру для переиспользования
        return extract_json(content, expected_key=expected_key)
    
    def _save_failed_json(self, original_json: str, fixed_json: str, error: Exception):
        """Сохраняет проблемный JSON в файл для отладки"""
        try:
            import os
            from datetime import datetime
            debug_dir = "debug_json"
            os.makedirs(debug_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            debug_file = os.path.join(debug_dir, f"failed_json_{timestamp}.txt")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"ERROR: {error}\n")
                f.write(f"{'='*80}\n")
                f.write(f"ORIGINAL JSON:\n")
                f.write(f"{'='*80}\n")
                f.write(original_json)
                f.write(f"\n{'='*80}\n")
                f.write(f"FIXED JSON:\n")
                f.write(f"{'='*80}\n")
                f.write(fixed_json)
            
            logger.info(f"💾 Проблемный JSON сохранен в: {debug_file}")
        except Exception as save_error:
            logger.error(f"Не удалось сохранить JSON в файл: {save_error}")
                    
    def _attempt_close_json(self, json_str: str) -> str:
        """Пытается закрыть обрезанный JSON
        
        Если JSON был обрезан из-за max_tokens, пытаемся закрыть его корректно,
        чтобы хотя бы получить часть данных.
        """
        try:
            # Подсчитываем открытые/закрытые скобки
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            open_brackets = json_str.count('[')
            close_brackets = json_str.count(']')
            
            # Проверяем, находимся ли мы внутри строки (незакрытая кавычка)
            # Упрощенная проверка: считаем неэкранированные кавычки
            quote_count = json_str.count('"') - json_str.count('\\"')
            in_string = (quote_count % 2) == 1
            
            # Если находимся внутри строки, закрываем её
            if in_string:
                json_str += '"'
                logger.info("🔧 Закрыли незавершенную строку")
            
            # Если последний символ - запятая, удаляем её
            json_str = json_str.rstrip()
            if json_str.endswith(','):
                json_str = json_str[:-1]
                logger.info("🔧 Удалили trailing запятую")
            
            # Закрываем массивы
            if open_brackets > close_brackets:
                for _ in range(open_brackets - close_brackets):
                    json_str += ']'
                logger.info(f"🔧 Закрыли {open_brackets - close_brackets} массивов")
            
            # Закрываем объекты
            if open_braces > close_braces:
                for _ in range(open_braces - close_braces):
                    json_str += '}'
                logger.info(f"🔧 Закрыли {open_braces - close_braces} объектов")
            
            return json_str
                
        except Exception as e:
            logger.warning(f"Ошибка при попытке закрыть JSON: {e}")
            return json_str
    
    def _fix_json_errors(self, json_str: str, error: json.JSONDecodeError) -> str:
        """Исправляет частые ошибки в JSON от AI
        
        Args:
            json_str: Строка JSON с ошибками
            error: Ошибка парсинга JSON для контекста
        """
        import re
        
        # 1. Исправляем trailing запятые перед закрывающими скобками
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # 2. Исправляем двойные запятые
        json_str = json_str.replace(',,', ',')
        
        # 3. Исправляем отсутствующие запятые между строками (частая ошибка AI)
        # Паттерн: "text"\n    "text" -> "text",\n    "text"
        json_str = re.sub(r'"\s*\n\s*"', '",\n        "', json_str)
        
        # 4. Исправляем отсутствующие запятые между объектами в массиве
        # Паттерн: }\n    { -> },\n    {
        json_str = re.sub(r'}\s*\n\s*{', '},\n        {', json_str)
        
        # 5. Исправляем отсутствующие запятые после закрывающих скобок перед полями
        # Паттерн: }\n    "field" -> },\n    "field"
        json_str = re.sub(r'}\s*\n\s*"', '},\n        "', json_str)
        # Паттерн: ]\n    "field" -> ],\n    "field"
        json_str = re.sub(r']\s*\n\s*"', '],\n        "', json_str)
        
        # 6. Исправляем отсутствующие запятые между значениями массива
        # Паттерн: "text1"\n    "text2" внутри массива
        # Это уже покрыто в пункте 3
        
        # 7. Удаляем BOM и другие невидимые символы
        json_str = json_str.replace('\ufeff', '')
        
        # 8. Исправляем неэкранированные переносы строк в строковых значениях
        # Это сложно и может сломать валидный JSON, поэтому пропускаем
        
        # 9. Если ошибка указывает на конкретную позицию, пытаемся исправить локально
        if hasattr(error, 'pos') and error.pos:
            # Проверяем контекст вокруг ошибки
            pos = error.pos
            if pos > 0 and pos < len(json_str):
                before = json_str[max(0, pos-5):pos]
                after = json_str[pos:min(len(json_str), pos+5)]
                
                # Если перед ошибкой закрывающая кавычка и пробелы, а после - кавычка
                if before.rstrip().endswith('"') and after.lstrip().startswith('"'):
                    # Вставляем запятую
                    json_str = json_str[:pos] + ',' + json_str[pos:]
                    logger.info(f"🔧 Добавлена запятая на позиции {pos}")
        
        return json_str
    
    def _get_test_module_content(self, module: Module) -> ModuleContent:
        """Возвращает тестовый контент для демонстрации"""
        lectures = []
        
        for i, lesson in enumerate(module.lessons, 1):
            slides = [
                Slide(
                    slide_number=1,
                    title=f"{lesson.lesson_title}",
                    content=f"Добро пожаловать на урок по {lesson.lesson_title}",
                    slide_type="title",
                    notes="Приветствие и введение в тему"
                ),
                Slide(
                    slide_number=2,
                    title="Цели урока",
                    content=f"• {lesson.lesson_goal}\n• Практическое применение\n• Закрепление материала",
                    slide_type="content",
                    notes="Расскажите о целях урока"
                ),
                Slide(
                    slide_number=3,
                    title="Теоретическая часть",
                    content="• Основные концепции\n• Важные термины\n• Принципы работы",
                    slide_type="content",
                    notes="Объясните теорию с примерами"
                ),
                Slide(
                    slide_number=4,
                    title="Пример кода",
                    content="Рассмотрим практический пример",
                    slide_type="code",
                    code_example="# Пример кода\nprint('Hello, World!')",
                    notes="Разберите код построчно"
                ),
                Slide(
                    slide_number=5,
                    title="Итоги",
                    content=f"• Изучили {lesson.lesson_title}\n• Разобрали примеры\n• Готовы к практике",
                    slide_type="summary",
                    notes="Подведите итоги урока"
                )
            ]
            
            lecture = Lecture(
                lecture_title=lesson.lesson_title,
                module_number=module.module_number,
                module_title=module.module_title,
                duration_minutes=lesson.estimated_time_minutes,
                slides=slides,
                learning_objectives=[lesson.lesson_goal],
                key_takeaways=[f"Основы {lesson.lesson_title}"]
            )
            
            lectures.append(lecture)
        
        return ModuleContent(
            module_number=module.module_number,
            module_title=module.module_title,
            lectures=lectures,
            total_slides=sum(len(lecture.slides) for lecture in lectures),
            estimated_duration_minutes=sum(lecture.duration_minutes for lecture in lectures)
        )
    
    def generate_topic_material(
        self,
        topic_number: int,
        topic_title: str,
        lesson: Lesson,
        module_number: int,
        course_title: str,
        module_title: str,
        target_audience: str
    ) -> Optional[TopicMaterial]:
        """Генерирует детальный материал для одной темы"""
        try:
            prompt = TOPIC_MATERIAL_PROMPT_TEMPLATE.format(
                course_title=course_title,
                target_audience=target_audience,
                module_title=module_title,
                lesson_title=lesson.lesson_title,
                lesson_goal=lesson.lesson_goal,
                topic_number=topic_number,
                topic_title=topic_title
            )
            
            # Пробуем JSON mode с оберткой клиента
            json_content = self.openai_client.call_ai_json(
                system_prompt=TOPIC_MATERIAL_SYSTEM_PROMPT,
                user_prompt=prompt,
                model=settings.OPENAI_MODEL_DETAILED_CONTENT,
                temperature=0.7,
                max_tokens=settings.OPENAI_MAX_TOKENS_TOPIC_MATERIAL,
            )
            if not json_content:
                # Обычный режим + санитайзер
                content = self.openai_client.call_ai(
                    system_prompt=TOPIC_MATERIAL_SYSTEM_PROMPT,
                    user_prompt=prompt,
                    model="gpt-4",
                    temperature=0.7,
                    max_tokens=settings.OPENAI_MAX_TOKENS_LESSON_DETAILED,
                )
                if not content:
                    return None
                json_content = extract_json(content, expected_key=None)
            
            if not json_content:
                logger.warning(f"Не удалось извлечь JSON для темы: {topic_title}")
                return None
            
            topic_material = TopicMaterial(**json_content)
            logger.info(f"✅ Материал создан: {len(topic_material.examples)} примеров")
            return topic_material
            
        except Exception as e:
            logger.error(f"Ошибка генерации материала для темы '{topic_title}': {e}")
            return None

