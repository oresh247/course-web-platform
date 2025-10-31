from backend.models.domain import Course, Module


def export_course_html(course: Course) -> str:
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{course.course_title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{ margin: 0 0 10px 0; }}
        .meta {{ display: flex; gap: 20px; flex-wrap: wrap; }}
        .meta-item {{ background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 5px; }}
        .module {{ background: white; padding: 30px; margin-bottom: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .module h2 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-top: 0; }}
        .module-goal {{ background: #f0f4ff; padding: 15px; border-left: 4px solid #667eea; margin: 15px 0; }}
        .lesson {{ margin: 20px 0; padding: 20px; background: #fafafa; border-radius: 5px; }}
        .lesson h3 {{ color: #764ba2; margin-top: 0; }}
        .lesson-meta {{ color: #666; margin: 10px 0; }}
        .lesson-meta span {{ background: #e0e0e0; padding: 3px 10px; border-radius: 3px; margin-right: 10px; }}
        .content-outline {{ background: white; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .content-outline ul {{ margin: 5px 0; padding-left: 20px; }}
        .assessment {{ background: #fff9e6; padding: 10px; border-left: 3px solid #ffd700; margin-top: 10px; }}
        @media print {{ body {{ background: white; }} .module {{ page-break-inside: avoid; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{course.course_title}</h1>
        <div class="meta">
            <div class="meta-item">👥 {course.target_audience}</div>
"""
    if course.duration_weeks:
        html += f'            <div class="meta-item">📅 {course.duration_weeks} недель</div>\n'
    if course.duration_hours:
        html += f'            <div class="meta-item">⏱️ {course.duration_hours} часов</div>\n'
    html += """        </div>
    </div>
"""
    for module in course.modules:
        html += f"""
    <div class="module">
        <h2>Модуль {module.module_number}: {module.module_title}</h2>
        <div class="module-goal">
            <strong>🎯 Цель модуля:</strong> {module.module_goal}
        </div>
"""
        for i, lesson in enumerate(module.lessons, 1):
            html += f"""
        <div class="lesson">
            <h3>{i}. {lesson.lesson_title}</h3>
            <p><strong>Цель урока:</strong> {lesson.lesson_goal}</p>
            <div class="lesson-meta">
                <span>📚 {lesson.format}</span>
                <span>⏱️ {lesson.estimated_time_minutes} мин</span>
            </div>
            <div class="content-outline">
                <strong>План контента:</strong>
                <ul>
"""
            for item in lesson.content_outline:
                html += f"                    <li>{item}</li>\n"
            html += """                </ul>
            </div>
            <div class="assessment">
                <strong>✅ Оценка:</strong> {lesson.assessment}
            </div>
        </div>
"""
        html += "    </div>\n"
    html += """
</body>
</html>"""
    return html


def export_module_html(course: Course, module: Module, content_data: dict) -> str:
    # Взято из исходной реализации с минимальными изменениями
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>{module.module_title} - Детальный контент</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #667eea; color: white; padding: 30px; border-radius: 8px; }}
        .lecture {{ background: #f9f9f9; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        .slide {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #667eea; }}
        .code {{ background: #282c34; color: #abb2bf; padding: 15px; border-radius: 4px; overflow-x: auto; }}
        .visual {{ background: #e8f5e9; padding: 10px; border-left: 4px solid #4caf50; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{course.course_title}</h1>
        <h2>Модуль {module.module_number}: {module.module_title}</h2>
        <p><strong>Цель:</strong> {module.module_goal}</p>
    </div>
"""
    lectures = content_data.get('lectures', [])
    for i, lecture in enumerate(lectures, 1):
        html += f"""
    <div class="lecture">
        <h3>Лекция {i}: {lecture.get('lecture_title', 'Без названия')}</h3>
"""
        if lecture.get('learning_objectives'):
            html += """        <div style="background: #f0f4ff; padding: 10px; margin: 10px 0; border-left: 3px solid #667eea;">
            <strong>Цели обучения:</strong>
            <ul>
"""
            for obj in lecture['learning_objectives']:
                html += f"                <li>{obj}</li>\n"
            html += """            </ul>
        </div>
"""
        if lecture.get('key_takeaways'):
            html += """        <div style="background: #fff9e6; padding: 10px; margin: 10px 0; border-left: 3px solid #ffd700;">
            <strong>Ключевые выводы:</strong>
            <ul>
"""
            for key in lecture['key_takeaways']:
                html += f"                <li>{key}</li>\n"
            html += """            </ul>
        </div>
"""
        slides = lecture.get('slides', [])
        for j, slide in enumerate(slides, 1):
            slide_title = slide.get('slide_title') or slide.get('title', 'Без названия')
            slide_content = slide.get('slide_content') or slide.get('content', '')
            html += f"""
        <div class="slide">
            <h4>Слайд {j}: {slide_title}</h4>
"""
            if slide_content:
                html += f"            <p>{slide_content}</p>\n"
            if slide.get('code_example'):
                html += f"""
            <div class="code">
                <pre><code>{slide['code_example']}</code></pre>
            </div>
"""
            if slide.get('visual_description'):
                html += f"""
            <div class="visual">
                <strong>📊 Визуализация:</strong> {slide['visual_description']}
            </div>
"""
            html += "        </div>\n"
        html += "    </div>\n"
    html += """
</body>
</html>"""
    return html


def export_lesson_html(course: Course, module: Module, lesson, content_data: dict) -> str:
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>{lesson.lesson_title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #667eea; color: white; padding: 25px; border-radius: 8px; margin-bottom: 20px; }}
        .objectives {{ background: #f0f4ff; padding: 15px; margin: 15px 0; border-left: 4px solid #667eea; }}
        .slide {{ background: #f9f9f9; padding: 20px; margin: 15px 0; border-radius: 8px; }}
        .slide h3 {{ color: #667eea; margin-top: 0; }}
        .code {{ background: #282c34; color: #abb2bf; padding: 15px; border-radius: 4px; overflow-x: auto; margin: 10px 0; }}
        .notes {{ background: #f0f0f0; padding: 10px; margin-top: 10px; font-style: italic; font-size: 0.9em; }}
        .takeaways {{ background: #fff9e6; padding: 15px; margin: 20px 0; border-left: 4px solid #ffd700; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{course.course_title}</h1>
        <h2>Модуль {module.module_number}: {module.module_title}</h2>
        <h3>{lesson.lesson_title}</h3>
        <p><strong>Цель:</strong> {lesson.lesson_goal}</p>
        <p><strong>Формат:</strong> {lesson.format} | <strong>Время:</strong> {lesson.estimated_time_minutes} мин</p>
    </div>
"""
    if content_data.get('learning_objectives'):
        html += """    <div class="objectives">
        <strong>Цели обучения:</strong>
        <ul>
"""
        for obj in content_data['learning_objectives']:
            html += f"            <li>{obj}</li>\n"
        html += """        </ul>
    </div>
"""
    slides = content_data.get('slides', [])
    for j, slide in enumerate(slides, 1):
        slide_title = slide.get('slide_title') or slide.get('title', 'Без названия')
        slide_content = slide.get('slide_content') or slide.get('content', '')
        html += f"""    <div class="slide">
        <h3>Слайд {j}: {slide_title}</h3>
"""
        if slide_content:
            html += f"        <p>{slide_content.replace(chr(10), '<br>')}</p>\n"
        if slide.get('code_example'):
            html += f"""        <div class="code">
            <pre><code>{slide['code_example']}</code></pre>
        </div>
"""
        if slide.get('notes'):
            html += f"""        <div class="notes">
            <strong>📝 Заметки:</strong> {slide['notes']}
        </div>
"""
        html += "    </div>\n"
    if content_data.get('key_takeaways'):
        html += """    <div class="takeaways">
        <strong>Ключевые выводы:</strong>
        <ul>
"""
        for key in content_data['key_takeaways']:
            html += f"            <li>{key}</li>\n"
        html += """        </ul>
    </div>
"""
    html += """
</body>
</html>"""
    return html


