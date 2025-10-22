"""
Генератор учебного контента для модулей курса
Адаптировано из TGBotCreateCourse проекта
"""
import logging
import json
from typing import Optional, Dict, Any, List

from backend.models.domain import (
    Module, Lecture, Slide, ModuleContent, 
    Lesson, LessonContent, TopicMaterial
)
from backend.ai.openai_client import OpenAIClient
from backend.ai.prompts import (
    MODULE_CONTENT_SYSTEM_PROMPT,
    MODULE_CONTENT_PROMPT_TEMPLATE,
    TOPIC_MATERIAL_SYSTEM_PROMPT,
    TOPIC_MATERIAL_PROMPT_TEMPLATE,
    format_lessons_list
)

logger = logging.getLogger(__name__)


class ContentGenerator:
    """Класс для генерации учебного контента модулей"""
    
    def __init__(self):
        self.openai_client = OpenAIClient()
    
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
            prompt = f"""Создай ДЕТАЛЬНУЮ лекцию со слайдами для одного урока IT-курса.

КОНТЕКСТ:
- Курс: {course_title}
- Аудитория: {target_audience}
- Модуль: {module.module_title}
- Урок: {lesson.lesson_title}
- Цель урока: {lesson.lesson_goal}
- Формат: {lesson.format}
- Время: {lesson.estimated_time_minutes} минут

ПЛАН КОНТЕНТА УРОКА:
{chr(10).join('- ' + item for item in lesson.content_outline)}

ЗАДАЧА:
Создай одну ЛЕКЦИЮ с 6-10 СЛАЙДАМИ, покрывающими все пункты плана контента.

ТРЕБОВАНИЯ:
- Каждый слайд должен содержать ПОЛНЫЙ учебный материал (2-3 абзаца объяснений)
- Для технических тем обязательно добавляй примеры кода в code_example
- Добавь learning_objectives (3-4 цели) и key_takeaways (3-4 вывода)

ФОРМАТ JSON:
{{
  "lecture_title": "{lesson.lesson_title}",
  "duration_minutes": {lesson.estimated_time_minutes},
  "learning_objectives": ["цель 1", "цель 2", "цель 3"],
  "key_takeaways": ["вывод 1", "вывод 2", "вывод 3"],
  "slides": [
    {{
      "slide_number": 1,
      "title": "Заголовок слайда",
      "content": "ПОЛНЫЙ детальный учебный материал с объяснениями...",
      "slide_type": "content",
      "code_example": null,
      "notes": "Краткие методические указания"
    }}
  ]
}}

Верни ТОЛЬКО JSON!"""
            
            response = self.openai_client.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Ты эксперт по созданию детального образовательного контента. Создаешь полноценные учебные материалы. ВЫВОДИ ТОЛЬКО JSON!"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=6000  # Увеличено с 3000 для детального контента урока
            )
            
            content = response.choices[0].message.content.strip()
            
            # Проверяем, не был ли ответ обрезан
            finish_reason = response.choices[0].finish_reason
            if finish_reason == "length":
                logger.warning(f"⚠️ Ответ урока был обрезан из-за лимита токенов!")
            
            logger.debug(f"Ответ урока (длина: {len(content)}, finish_reason: {finish_reason})")
            
            # Для урока парсим JSON напрямую (не используем _extract_json для модулей)
            try:
                # Удаляем markdown блоки если есть
                content = content.replace('```json', '').replace('```', '').strip()
                
                # Ищем JSON блок
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    lesson_content = json.loads(json_str)
                    
                    if 'slides' in lesson_content and isinstance(lesson_content['slides'], list):
                        logger.info(f"✅ Контент урока сгенерирован: {len(lesson_content['slides'])} слайдов")
                        return lesson_content
                    else:
                        logger.warning(f"❌ Неправильная структура урока. Ключи: {list(lesson_content.keys())}")
                        return None
                else:
                    logger.warning("❌ JSON блок не найден в ответе для урока")
                    return None
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ Ошибка парсинга JSON урока: {e}")
                return None
            except Exception as e:
                logger.error(f"❌ Неожиданная ошибка при парсинге урока: {e}")
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
            
            response = self.openai_client.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": MODULE_CONTENT_SYSTEM_PROMPT + "\n\nВЫВОД ТОЛЬКО В JSON ФОРМАТЕ!"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=8000  # Увеличено с 4000 для более детального контента
            )
            
            content = response.choices[0].message.content.strip()
            
            # Проверяем, не был ли ответ обрезан из-за лимита токенов
            finish_reason = response.choices[0].finish_reason
            if finish_reason == "length":
                logger.warning(f"⚠️ Ответ был обрезан из-за лимита токенов! Увеличьте max_tokens.")
            
            # Логируем сырой ответ для отладки
            logger.info(f"📝 Получен JSON ответ от AI (длина: {len(content)} символов, finish_reason: {finish_reason})")
            logger.debug(f"Полный ответ: {content}")
            
            json_content = self._extract_json(content)
            
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
            
            response = self.openai_client.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": MODULE_CONTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=8000  # Увеличено с 4000 для более детального контента
            )
            
            content = response.choices[0].message.content.strip()
            
            # Проверяем, не был ли ответ обрезан из-за лимита токенов
            finish_reason = response.choices[0].finish_reason
            if finish_reason == "length":
                logger.warning(f"⚠️ Ответ был обрезан из-за лимита токенов! Увеличьте max_tokens.")
            
            logger.info(f"📝 Получен ответ от AI (длина: {len(content)} символов, finish_reason: {finish_reason})")
            
            json_content = self._extract_json(content)
            
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
                return module_content
            else:
                logger.warning("❌ Текстовый режим вернул неправильную структуру")
                return None
                
        except Exception as e:
            logger.warning(f"❌ Текстовый режим не сработал: {e}")
            return None
    
    def _extract_json(self, content: str, expected_key: str = "lectures") -> Optional[Dict[str, Any]]:
        """Извлекает JSON из ответа с автоматическим исправлением частых ошибок
        
        Args:
            content: Текст ответа от AI
            expected_key: Ожидаемый ключ в корне JSON (по умолчанию "lectures")
        """
        try:
            # Удаляем markdown блоки если есть
            content = content.replace('```json', '').replace('```', '').strip()
            
            # Ищем JSON блок
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx == -1 or end_idx <= start_idx:
                logger.error("JSON блок не найден в ответе")
                return None
            
            json_str = content[start_idx:end_idx]
            
            # Проверяем, не обрезан ли JSON (неполный ответ из-за max_tokens)
            is_truncated = not json_str.rstrip().endswith('}')
            if is_truncated:
                logger.warning("⚠️ JSON выглядит обрезанным (не заканчивается на })")
                # Попытка закрыть JSON автоматически
                json_str = self._attempt_close_json(json_str)
            
            # Попытка 1: Стандартный парсинг
            try:
                parsed = json.loads(json_str)
                if expected_key and expected_key in parsed:
                    logger.info(f"✅ Получена правильная структура с '{expected_key}'")
                    return parsed
                elif not expected_key:
                    # Если ключ не указан, возвращаем любую валидную структуру
                    logger.info(f"✅ Получен валидный JSON с ключами: {list(parsed.keys())}")
                    return parsed
                else:
                    logger.warning(f"⚠️ Отсутствует ожидаемый ключ '{expected_key}'. Доступные ключи: {list(parsed.keys())}")
                    # Возвращаем anyway - может быть полезно
                    return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Ошибка парсинга JSON: {e}")
                logger.info(f"🔧 Пробуем исправить JSON автоматически...")
                
                # Попытка 2: Исправление частых ошибок
                fixed_json = self._fix_json_errors(json_str, e)
                
                try:
                    parsed = json.loads(fixed_json)
                    if expected_key and expected_key in parsed:
                        logger.info("✅ JSON исправлен и успешно распарсен!")
                        return parsed
                    elif not expected_key:
                        logger.info(f"✅ JSON исправлен. Ключи: {list(parsed.keys())}")
                        return parsed
                    else:
                        logger.warning(f"⚠️ JSON исправлен, но отсутствует ключ '{expected_key}'")
                        return parsed
                except json.JSONDecodeError as e2:
                    logger.error(f"❌ Не удалось исправить JSON: {e2}")
                    # Логируем проблемную часть JSON для анализа
                    error_pos = e2.pos if hasattr(e2, 'pos') else e.pos
                    context_start = max(0, error_pos - 100)
                    context_end = min(len(json_str), error_pos + 100)
                    logger.error(f"Проблемная часть JSON (позиция {error_pos}): ...{json_str[context_start:context_end]}...")
                    
                    # Сохраняем проблемный JSON в файл для анализа
                    self._save_failed_json(json_str, fixed_json, e2)
                    
                    return None
                
        except Exception as e:
            logger.error(f"Неожиданная ошибка при извлечении JSON: {e}")
            return None
    
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
            
            # Пробуем JSON mode
            try:
                response = self.openai_client.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": TOPIC_MATERIAL_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    max_tokens=6000  # Увеличено с 4000 для детального материала темы
                )
                logger.info("✅ Используем JSON mode для генерации темы")
            except Exception as e:
                logger.warning(f"JSON mode не сработал: {e}")
                # Обычный режим
                response = self.openai_client.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": TOPIC_MATERIAL_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=6000  # Увеличено с 4000 для детального материала темы
                )
            
            content = response.choices[0].message.content.strip()
            # Для материала темы не проверяем конкретный ключ
            json_content = self._extract_json(content, expected_key=None)
            
            if not json_content:
                logger.warning(f"Не удалось извлечь JSON для темы: {topic_title}")
                return None
            
            topic_material = TopicMaterial(**json_content)
            logger.info(f"✅ Материал создан: {len(topic_material.examples)} примеров")
            return topic_material
            
        except Exception as e:
            logger.error(f"Ошибка генерации материала для темы '{topic_title}': {e}")
            return None

