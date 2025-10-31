from typing import Dict, Any
from backend.models.domain import Course, Module


def export_course_markdown(course: Course) -> str:
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
        for i, lesson in enumerate(module.lessons, 1):
            md += f"### {i}. {lesson.lesson_title}\n\n"
            md += f"**Цель урока:** {lesson.lesson_goal}\n\n"
            md += f"**Формат:** {lesson.format} | **Время:** {lesson.estimated_time_minutes} мин\n\n"
            md += f"**План контента:**\n"
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
            md += f"#### Слайд {j}: {slide_title}\n\n"
            if slide_content:
                md += f"{slide_content}\n\n"
            if slide.get('code_example'):
                md += f"```python\n{slide['code_example']}\n```\n\n"
            if slide.get('visual_description'):
                md += f"📊 **Визуализация:** {slide['visual_description']}\n\n"
            if slide.get('notes'):
                md += f"📝 _Заметки преподавателя: {slide['notes']}_\n\n"
        md += "---\n\n"
    return md


def export_lesson_markdown(course: Course, module: Module, lesson, content_data: dict) -> str:
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
        md += f"#### Слайд {j}: {slide_title}\n\n"
        if slide_content:
            md += f"{slide_content}\n\n"
        if slide.get('code_example'):
            md += f"```python\n{slide['code_example']}\n```\n\n"
        if slide.get('notes'):
            md += f"📝 _{slide['notes']}_\n\n"
    if content_data.get('key_takeaways'):
        md += "---\n\n**Ключевые выводы:**\n"
        for key in content_data['key_takeaways']:
            md += f"- {key}\n"
        md += "\n"
    return md


