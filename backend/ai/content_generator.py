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
                max_tokens=3000
            )
            
            content = response.choices[0].message.content.strip()
            
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
                max_tokens=4000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Логируем сырой ответ для отладки
            logger.info(f"📝 Получен JSON ответ от AI (длина: {len(content)} символов)")
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
                max_tokens=4000
            )
            
            content = response.choices[0].message.content.strip()
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
    
    def _extract_json(self, content: str) -> Optional[Dict[str, Any]]:
        """Извлекает JSON из ответа с автоматическим исправлением частых ошибок"""
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
            
            # Попытка 1: Стандартный парсинг
            try:
                parsed = json.loads(json_str)
                if 'lectures' in parsed and isinstance(parsed['lectures'], list):
                    logger.info("✅ Получена правильная структура с 'lectures'")
                    return parsed
                else:
                    logger.error(f"❌ Неизвестная структура JSON. Доступные ключи: {list(parsed.keys())}")
                    return None
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Ошибка парсинга JSON: {e}")
                logger.info(f"🔧 Пробуем исправить JSON автоматически...")
                
                # Попытка 2: Исправление частых ошибок
                fixed_json = self._fix_json_errors(json_str)
                
                try:
                    parsed = json.loads(fixed_json)
                    if 'lectures' in parsed and isinstance(parsed['lectures'], list):
                        logger.info("✅ JSON исправлен и успешно распарсен!")
                        return parsed
                    else:
                        logger.error(f"❌ Структура после исправления неправильная")
                        return None
                except json.JSONDecodeError as e2:
                    logger.error(f"❌ Не удалось исправить JSON: {e2}")
                    # Логируем проблемную часть JSON для анализа
                    logger.error(f"Проблемная часть JSON (позиция {e.pos}): ...{json_str[max(0,e.pos-50):e.pos+50]}...")
                    
                    # Сохраняем проблемный JSON в файл для анализа
                    try:
                        import os
                        from datetime import datetime
                        debug_dir = "debug_json"
                        os.makedirs(debug_dir, exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        debug_file = os.path.join(debug_dir, f"failed_json_{timestamp}.json")
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(json_str)
                        logger.info(f"💾 Проблемный JSON сохранен в: {debug_file}")
                    except Exception as save_error:
                        logger.error(f"Не удалось сохранить JSON в файл: {save_error}")
                    
                    return None
                
        except Exception as e:
            logger.error(f"Неожиданная ошибка при извлечении JSON: {e}")
            return None
    
    def _fix_json_errors(self, json_str: str) -> str:
        """Исправляет частые ошибки в JSON от AI"""
        # 1. Исправляем запятые перед закрывающими скобками
        json_str = json_str.replace(',]', ']')
        json_str = json_str.replace(',}', '}')
        
        # 2. Исправляем двойные запятые
        json_str = json_str.replace(',,', ',')
        
        # 3. Исправляем отсутствующие запятые между элементами (простой случай)
        # Это сложнее, поэтому пропускаем
        
        # 4. Исправляем одинарные кавычки на двойные (если есть)
        # Осторожно, может быть в тексте контента
        # json_str = json_str.replace("'", '"')
        
        # 5. Удаляем trailing запятые перед закрывающими скобками (повторно для надежности)
        import re
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
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
                    max_tokens=4000
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
                    max_tokens=4000
                )
            
            content = response.choices[0].message.content.strip()
            json_content = self._extract_json(content)
            
            if not json_content:
                logger.warning(f"Не удалось извлечь JSON для темы: {topic_title}")
                return None
            
            topic_material = TopicMaterial(**json_content)
            logger.info(f"✅ Материал создан: {len(topic_material.examples)} примеров")
            return topic_material
            
        except Exception as e:
            logger.error(f"Ошибка генерации материала для темы '{topic_title}': {e}")
            return None

