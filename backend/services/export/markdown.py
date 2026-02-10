import logging
from typing import Dict, Any, Optional, List

from backend.models.domain import Course, Module
from backend.database import db
from backend.services.export import normalize_newlines

logger = logging.getLogger(__name__)


def _format_slide_content(slide_content: str) -> str:
    """Форматирует контент слайда для Markdown.

    Нормализует переносы строк и возвращает текст, готовый для вставки в Markdown.

    Args:
        slide_content: Сырой текст контента слайда.

    Returns:
        str: Отформатированный текст.
    """
    if not slide_content:
        return ""
    normalized = normalize_newlines(slide_content)
    # Разделяем на параграфы по двойным переносам
    paragraphs = normalized.split("\n\n")
    result_parts: list[str] = []
    for para in paragraphs:
        stripped = para.strip()
        if stripped:
            result_parts.append(stripped)
    return "\n\n".join(result_parts)


def _format_code_example(code_example: str, slide_type: str = "python") -> str:
    """Форматирует пример кода для Markdown.

    Args:
        code_example: Сырой текст примера кода.
        slide_type: Тип слайда / язык кода.

    Returns:
        str: Блок кода в формате Markdown.
    """
    if not code_example:
        return ""
    normalized = normalize_newlines(code_example)
    # Определяем язык для подсветки синтаксиса
    lang = slide_type if slide_type and slide_type != "content" else "python"
    return f"```{lang}\n{normalized}\n```"


def _format_test_markdown(test_data: Dict[str, Any]) -> str:
    """Форматирует тест в Markdown.

    Args:
        test_data: Данные теста (questions, passing_score_percent).

    Returns:
        str: Тест в формате Markdown.
    """
    if not test_data:
        return ""

    questions = test_data.get("questions", [])
    if not questions:
        return ""

    passing_score = test_data.get("passing_score_percent", 70)
    md = "#### 📝 Тест для проверки знаний\n\n"
    md += f"_Проходной балл: {passing_score}%_\n\n"

    for q_idx, question in enumerate(questions, 1):
        question_text = question.get("question_text", "")
        md += f"**Вопрос {q_idx}.** {question_text}\n\n"

        options = question.get("options", [])
        for opt in options:
            option_text = opt.get("option_text", "")
            is_correct = opt.get("is_correct", False)
            marker = "✅" if is_correct else "⬚"
            md += f"- {marker} {option_text}\n"
        md += "\n"

        explanation = question.get("explanation", "")
        if explanation:
            md += f"> 💡 **Объяснение:** {explanation}\n\n"

    return md


def export_course_markdown(course: Course, course_id: int = None) -> str:
    """Генерирует полный Markdown для всего курса с детальным контентом.

    Выгружает весь курс аналогично SCORM (без видео): все модули, слайды
    с контентом и примерами кода, а также все тесты.

    Args:
        course: Объект курса.
        course_id: ID курса в БД для получения детального контента.
            Если не указан, выгружается только структура курса.

    Returns:
        str: Полный Markdown курса.
    """
    md = f"# {course.course_title}\n\n"
    md += f"**Целевая аудитория:** {course.target_audience}\n\n"
    if course.duration_weeks:
        md += f"**Длительность:** {course.duration_weeks} недель\n\n"
    if course.duration_hours:
        md += f"**Всего часов:** {course.duration_hours}\n\n"
    md += "---\n\n"

    for module in course.modules:
        md += f"## Модуль {module.module_number}: {module.module_title}\n\n"
        md += f"**Цель модуля:** {module.module_goal}\n\n"

        for lesson_idx, lesson in enumerate(module.lessons):
            lesson_num = lesson_idx + 1
            md += f"### {lesson_num}. {lesson.lesson_title}\n\n"
            md += f"**Цель урока:** {lesson.lesson_goal}\n\n"
            md += f"**Формат:** {lesson.format} | **Время:** {lesson.estimated_time_minutes} мин\n\n"

            # Получаем детальный контент урока из БД
            content_data = None
            if course_id is not None:
                try:
                    content_data = db.get_lesson_content(
                        course_id, module.module_number, lesson_idx
                    )
                except Exception as e:
                    logger.debug(
                        f"Контент урока {module.module_number}/{lesson_idx} не найден: {e}"
                    )

            if content_data and content_data.get("slides"):
                # Цели обучения
                learning_objectives = content_data.get("learning_objectives", [])
                if learning_objectives:
                    md += "**Цели обучения:**\n"
                    for obj in learning_objectives:
                        md += f"- {obj}\n"
                    md += "\n"

                # Слайды
                slides = content_data.get("slides", [])
                for s_idx, slide in enumerate(slides, 1):
                    slide_title = (
                        slide.get("slide_title")
                        or slide.get("title", f"Слайд {s_idx}")
                    )
                    slide_content = (
                        slide.get("slide_content") or slide.get("content", "")
                    )
                    slide_type = slide.get("slide_type", "content")
                    code_example = slide.get("code_example")
                    notes = slide.get("notes")
                    visual = slide.get("visual_description")

                    md += f"#### Слайд {s_idx}: {slide_title}\n\n"

                    if slide_content:
                        md += f"{_format_slide_content(slide_content)}\n\n"

                    if code_example:
                        md += f"{_format_code_example(code_example, slide_type)}\n\n"

                    if visual:
                        md += f"📊 **Визуализация:** {visual}\n\n"

                    if notes:
                        md += f"📝 _{notes}_\n\n"

                # Ключевые выводы
                key_takeaways = content_data.get("key_takeaways", [])
                if key_takeaways:
                    md += "**Ключевые выводы:**\n"
                    for key in key_takeaways:
                        md += f"- {key}\n"
                    md += "\n"

                # Тест
                test_data = content_data.get("test")
                if not test_data and course_id is not None:
                    try:
                        test_data = db.get_lesson_test(
                            course_id, module.module_number, lesson_idx
                        )
                    except Exception as e:
                        logger.debug(
                            f"Тест урока {module.module_number}/{lesson_idx} не найден: {e}"
                        )

                if test_data:
                    md += _format_test_markdown(test_data)

            else:
                # Нет детального контента — выводим план
                md += "**План контента:**\n"
                for item in lesson.content_outline:
                    md += f"- {item}\n"
                md += f"\n**Оценка:** {lesson.assessment}\n\n"

        md += "---\n\n"

    return md


def export_course_text(course: Course) -> str:
    txt = f"{course.course_title}\n"
    txt += "=" * len(course.course_title) + "\n\n"
    txt += f"Целевая аудитория: {course.target_audience}\n"
    if course.duration_weeks:
        txt += f"Длительность: {course.duration_weeks} недель\n"
    if course.duration_hours:
        txt += f"Всего часов: {course.duration_hours}\n"
    txt += "\n" + "-" * 80 + "\n\n"
    for module in course.modules:
        txt += f"\nМОДУЛЬ {module.module_number}: {module.module_title}\n"
        txt += "-" * 40 + "\n"
        txt += f"Цель модуля: {module.module_goal}\n\n"
        for i, lesson in enumerate(module.lessons, 1):
            txt += f"  {i}. {lesson.lesson_title}\n"
            txt += f"     Цель: {lesson.lesson_goal}\n"
            txt += f"     Формат: {lesson.format} | Время: {lesson.estimated_time_minutes} мин\n"
            txt += f"     План контента:\n"
            for item in lesson.content_outline:
                txt += f"       - {item}\n"
            txt += f"     Оценка: {lesson.assessment}\n\n"
        txt += "\n"
    return txt


def export_module_markdown(course: Course, module: Module, content_data: dict) -> str:
    """Markdown экспорт детального контента модуля.

    Args:
        course: Объект курса.
        module: Объект модуля.
        content_data: Детальный контент модуля (lectures).

    Returns:
        str: Markdown представление модуля.
    """
    md = f"# {course.course_title}\n\n"
    md += f"## Модуль {module.module_number}: {module.module_title}\n\n"
    md += f"**Цель модуля:** {module.module_goal}\n\n"
    md += "---\n\n"
    lectures = content_data.get('lectures', [])
    for i, lecture in enumerate(lectures, 1):
        md += f"### Лекция {i}: {lecture.get('lecture_title', 'Без названия')}\n\n"
        if lecture.get('learning_objectives'):
            md += "**Цели обучения:**\n"
            for obj in lecture['learning_objectives']:
                md += f"- {obj}\n"
            md += "\n"
        if lecture.get('key_takeaways'):
            md += "**Ключевые выводы:**\n"
            for key in lecture['key_takeaways']:
                md += f"- {key}\n"
            md += "\n"
        slides = lecture.get('slides', [])
        for j, slide in enumerate(slides, 1):
            slide_title = slide.get('slide_title') or slide.get('title', 'Без названия')
            slide_content = slide.get('slide_content') or slide.get('content', '')
            slide_type = slide.get('slide_type', 'content')
            md += f"#### Слайд {j}: {slide_title}\n\n"
            if slide_content:
                md += f"{_format_slide_content(slide_content)}\n\n"
            if slide.get('code_example'):
                md += f"{_format_code_example(slide['code_example'], slide_type)}\n\n"
            if slide.get('visual_description'):
                md += f"📊 **Визуализация:** {slide['visual_description']}\n\n"
            if slide.get('notes'):
                md += f"📝 _Заметки преподавателя: {slide['notes']}_\n\n"
        md += "---\n\n"
    return md


def export_lesson_markdown(course: Course, module: Module, lesson, content_data: dict) -> str:
    """Markdown экспорт детального контента урока.

    Args:
        course: Объект курса.
        module: Объект модуля.
        lesson: Объект урока.
        content_data: Детальный контент урока (slides, test и т.д.).

    Returns:
        str: Markdown представление урока.
    """
    md = f"# {course.course_title}\n\n"
    md += f"## Модуль {module.module_number}: {module.module_title}\n\n"
    md += f"### Урок: {lesson.lesson_title}\n\n"
    md += f"**Цель урока:** {lesson.lesson_goal}\n\n"
    md += f"**Формат:** {lesson.format} | **Время:** {lesson.estimated_time_minutes} мин\n\n"
    md += "---\n\n"
    if content_data.get('learning_objectives'):
        md += "**Цели обучения:**\n"
        for obj in content_data['learning_objectives']:
            md += f"- {obj}\n"
        md += "\n"
    slides = content_data.get('slides', [])
    for j, slide in enumerate(slides, 1):
        slide_title = slide.get('slide_title') or slide.get('title', 'Без названия')
        slide_content = slide.get('slide_content') or slide.get('content', '')
        slide_type = slide.get('slide_type', 'content')
        md += f"#### Слайд {j}: {slide_title}\n\n"
        if slide_content:
            md += f"{_format_slide_content(slide_content)}\n\n"
        if slide.get('code_example'):
            md += f"{_format_code_example(slide['code_example'], slide_type)}\n\n"
        if slide.get('visual_description'):
            md += f"📊 **Визуализация:** {slide['visual_description']}\n\n"
        if slide.get('notes'):
            md += f"📝 _{slide['notes']}_\n\n"
    if content_data.get('key_takeaways'):
        md += "---\n\n**Ключевые выводы:**\n"
        for key in content_data['key_takeaways']:
            md += f"- {key}\n"
        md += "\n"

    # Тест
    test_data = content_data.get('test')
    if test_data:
        md += "---\n\n"
        md += _format_test_markdown(test_data)

    return md


