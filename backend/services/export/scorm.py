"""
SCORM 1.2 экспорт курсов с детальным контентом (слайды).

SCORM (Sharable Content Object Reference Model) - стандарт для электронного обучения,
который позволяет курсам работать в различных LMS (Learning Management Systems).

Структура SCORM пакета:
- imsmanifest.xml - манифест курса
- HTML файлы для каждого урока/слайда
- SCORM API JavaScript
- Видео файлы (опционально)
- ZIP архив
"""
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO
from typing import Dict, Any, List, Optional
from datetime import datetime
import html as html_module
import json
import logging
import httpx

from backend.models.domain import Course, Module
from backend.database import db

logger = logging.getLogger(__name__)

# Импортируем HeyGen сервис для получения URL видео, если его нет в БД
try:
    from backend.services.heygen_service import HeyGenService
    heygen_service = None  # Будет инициализирован при необходимости
except ImportError:
    logger.warning("HeyGenService не доступен, получение URL из API будет пропущено")
    heygen_service = None


def escape_xml(text: str) -> str:
    """Экранирует XML специальные символы"""
    return html_module.escape(text, quote=False)


def create_scorm_manifest(course: Course, course_id: int, video_files: Dict[str, str] = None) -> str:
    """Создает imsmanifest.xml для SCORM 1.2"""
    
    # Создаем корневой элемент manifest
    manifest = ET.Element("manifest")
    manifest.set("identifier", f"course_{course_id}")
    manifest.set("version", "1.0")
    manifest.set("xmlns", "http://www.imsproject.org/xsd/imscp_rootv1p1p2")
    manifest.set("xmlns:adlcp", "http://www.adlnet.org/xsd/adlcp_rootv1p2")
    manifest.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    manifest.set("xsi:schemaLocation", 
                 "http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd "
                 "http://www.imsglobal.org/xsd/imsmd_rootv1p2p1 imsmd_rootv1p2p1.xsd "
                 "http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd")
    
    # Метаданные
    metadata = ET.SubElement(manifest, "metadata")
    schema = ET.SubElement(metadata, "schema")
    schema.text = "ADL SCORM"
    schemaversion = ET.SubElement(metadata, "schemaversion")
    schemaversion.text = "1.2"
    
    # Организация
    organizations = ET.SubElement(manifest, "organizations")
    organizations.set("default", "TOC1")
    
    organization = ET.SubElement(organizations, "organization")
    organization.set("identifier", "TOC1")
    org_title = ET.SubElement(organization, "title")
    org_title.text = escape_xml(course.course_title)
    
    # Элементы курса (модули и уроки)
    items = ET.SubElement(organization, "items")
    
    # Ресурсы
    resources = ET.SubElement(manifest, "resources")
    
    item_counter = 1
    resource_counter = 1
    
    # Проходим по модулям
    for module in course.modules:
        module_item = ET.SubElement(items, "item")
        module_item.set("identifier", f"MODULE_{module.module_number}")
        module_title = ET.SubElement(module_item, "title")
        module_title.text = escape_xml(f"Модуль {module.module_number}: {module.module_title}")
        
        module_items = ET.SubElement(module_item, "items")
        
        # Проходим по урокам
        for lesson_idx, lesson in enumerate(module.lessons):
            lesson_item = ET.SubElement(module_items, "item")
            lesson_identifier = f"LESSON_{module.module_number}_{lesson_idx}"
            lesson_item.set("identifier", lesson_identifier)
            lesson_item.set("identifierref", f"RES_{resource_counter}")
            
            lesson_title = ET.SubElement(lesson_item, "title")
            lesson_title.text = escape_xml(f"{lesson_idx + 1}. {lesson.lesson_title}")
            
            # Создаем ресурс для урока
            resource = ET.SubElement(resources, "resource")
            resource.set("identifier", f"RES_{resource_counter}")
            resource.set("type", "webcontent")
            resource.set("adlcp:scormtype", "sco")
            resource.set("href", f"lessons/lesson_{module.module_number}_{lesson_idx}.html")
            
            # Файл HTML урока
            file_elem = ET.SubElement(resource, "file")
            file_elem.set("href", f"lessons/lesson_{module.module_number}_{lesson_idx}.html")
            
            # Добавляем видео файл, если он есть
            video_key = f"{module.module_number}_{lesson_idx}"
            if video_files and video_key in video_files:
                video_file_elem = ET.SubElement(resource, "file")
                video_file_elem.set("href", f"videos/{video_files[video_key]}")
            
            # Зависимости (SCORM API)
            dependency = ET.SubElement(resource, "dependency")
            dependency.set("identifierref", "API_JS")
            
            resource_counter += 1
            item_counter += 1
    
    # Ресурс SCORM API
    api_resource = ET.SubElement(resources, "resource")
    api_resource.set("identifier", "API_JS")
    api_resource.set("type", "webcontent")
    api_resource.set("href", "scripts/SCORM_API_wrapper.js")
    
    # Файл SCORM API
    api_file = ET.SubElement(api_resource, "file")
    api_file.set("href", "scripts/SCORM_API_wrapper.js")
    
    # Форматируем XML
    ET.indent(manifest, space="  ")
    xml_str = ET.tostring(manifest, encoding='utf-8', xml_declaration=True).decode('utf-8')
    
    return xml_str


def create_scorm_api_js() -> str:
    """Создает SCORM API JavaScript wrapper"""
    return """/*
SCORM API Wrapper для SCORM 1.2
Обеспечивает взаимодействие с LMS через SCORM API
*/

var API = null;
var API_1484_11 = null;

function findAPI(win) {
    var findAttempts = 0;
    var findAttemptLimit = 500;
    var traceMsgPrefix = "SCORM.API.findAPI.";
    
    while ((win.API == null || win.API_1484_11 == null) && (win.parent != null) && (win.parent != win)) {
        findAttempts++;
        if (findAttempts > findAttemptLimit) {
            return null;
        }
        win = win.parent;
    }
    return win.API;
}

function getAPI() {
    var theAPI = findAPI(window);
    if ((theAPI == null) && (window.top != null) && (window.top.opener != null)) {
        theAPI = findAPI(window.top.opener);
    }
    if (theAPI == null) {
        theAPI = findAPI(window.top);
    }
    return theAPI;
}

function SCORM_API_Initialize(parameter) {
    API = getAPI();
    if (API == null) {
        return "false";
    }
    var result = API.LMSInitialize(parameter);
    return String(result);
}

function SCORM_API_GetValue(parameter) {
    if (API == null) {
        return "";
    }
    var result = API.LMSGetValue(parameter);
    return String(result);
}

function SCORM_API_SetValue(parameter, value) {
    if (API == null) {
        return "false";
    }
    var result = API.LMSSetValue(parameter, value);
    return String(result);
}

function SCORM_API_Commit(parameter) {
    if (API == null) {
        return "false";
    }
    var result = API.LMSCommit(parameter);
    return String(result);
}

function SCORM_API_GetLastError() {
    if (API == null) {
        return "0";
    }
    var result = API.LMSGetLastError();
    return String(result);
}

function SCORM_API_GetErrorString(errorCode) {
    if (API == null) {
        return "";
    }
    var result = API.LMSGetErrorString(errorCode);
    return String(result);
}

function SCORM_API_GetDiagnostic(errorCode) {
    if (API == null) {
        return "";
    }
    var result = API.LMSGetDiagnostic(errorCode);
    return String(result);
}

function SCORM_API_Terminate(parameter) {
    if (API == null) {
        return "false";
    }
    var result = API.LMSTerminate(parameter);
    return String(result);
}

// Инициализация при загрузке страницы
window.addEventListener('load', function() {
    SCORM_API_Initialize("");
    SCORM_API_SetValue("cmi.core.lesson_status", "incomplete");
});

// Сохранение прогресса при закрытии
window.addEventListener('beforeunload', function() {
    SCORM_API_SetValue("cmi.core.lesson_status", "completed");
    SCORM_API_Commit("");
    SCORM_API_Terminate("");
});
"""


def create_lesson_html(
    course: Course,
    module: Module,
    lesson,
    lesson_index: int,
    content_data: Dict[str, Any] = None,
    include_video: bool = False,
    video_filename: Optional[str] = None,
    test_data: Dict[str, Any] = None
) -> str:
    """Создает HTML страницу для урока со слайдами"""
    
    slides_html = ""
    navigation_html = ""
    
    if content_data and "slides" in content_data:
        slides = content_data.get("slides", [])
        for idx, slide in enumerate(slides):
            slide_id = f"slide_{idx}"
            slide_title = escape_xml(slide.get("title", f"Слайд {idx + 1}"))
            slide_content = slide.get("content", "")
            slide_type = slide.get("slide_type", "content")
            code_example = slide.get("code_example")
            
            # Форматируем контент слайда
            content_html = ""
            if slide_content:
                # Заменяем переносы строк на <br> и параграфы
                paragraphs = slide_content.split("\\n\\n")
                for para in paragraphs:
                    if para.strip():
                        # Выносим replace за пределы f-string, так как нельзя использовать \ в f-string выражениях
                        para_processed = para.replace('\\n', '<br>')
                        content_html += f"<p>{escape_xml(para_processed)}</p>"
            
            # Добавляем пример кода, если есть
            if code_example:
                content_html += f'<pre><code class="language-{slide_type}">{escape_xml(code_example)}</code></pre>'
            
            slides_html += f"""
            <div class="slide" id="{slide_id}" style="display: {'block' if idx == 0 else 'none'};">
                <h3>{slide_title}</h3>
                <div class="slide-content">
                    {content_html}
                </div>
            </div>
            """
            
            navigation_html += f'<button class="nav-btn" onclick="showSlide({idx})">{idx + 1}</button>'
    
    # Если нет детального контента, показываем базовую информацию
    if not slides_html:
        slides_html = f"""
        <div class="slide" id="slide_0" style="display: block;">
            <h3>{escape_xml(lesson.lesson_title)}</h3>
            <div class="slide-content">
                <p><strong>Цель урока:</strong> {escape_xml(lesson.lesson_goal)}</p>
                <p><strong>Формат:</strong> {escape_xml(str(lesson.format))}</p>
                <p><strong>Время:</strong> {lesson.estimated_time_minutes} минут</p>
                <h4>План контента:</h4>
                <ul>
        """
        for item in lesson.content_outline:
            slides_html += f"<li>{escape_xml(item)}</li>"
        slides_html += """
                </ul>
            </div>
        </div>
        """
        navigation_html = '<button class="nav-btn active" onclick="showSlide(0)">1</button>'
    
    # Добавляем блок с видео, если оно включено
    video_html = ""
    if include_video and video_filename:
        video_html = f"""
    <div class="video-container">
        <h3>🎬 Видео урока</h3>
        <video controls width="100%" style="max-width: 800px; border-radius: 5px;">
            <source src="../videos/{video_filename}" type="video/mp4">
            Ваш браузер не поддерживает воспроизведение видео.
        </video>
    </div>
"""
    
    # Добавляем блок с тестом, если он есть
    test_html = ""
    test_js = ""
    if test_data and test_data.get("questions"):
        questions = test_data.get("questions", [])
        passing_score = test_data.get("passing_score_percent", 70)
        
        # Генерируем HTML для теста
        test_questions_html = ""
        for q_idx, question in enumerate(questions):
            question_text = escape_xml(question.get("question_text", ""))
            options = question.get("options", [])
            explanation = escape_xml(question.get("explanation", "")) if question.get("explanation") else ""
            
            options_html = ""
            for opt_idx, option in enumerate(options):
                option_text = escape_xml(option.get("option_text", ""))
                is_correct = option.get("is_correct", False)
                options_html += f"""
                <label class="test-option">
                    <input type="radio" name="question_{q_idx}" value="{opt_idx}" data-correct="{str(is_correct).lower()}">
                    {option_text}
                </label>
                """
            
            test_questions_html += f"""
            <div class="test-question" id="test_question_{q_idx}">
                <h4>Вопрос {q_idx + 1}: {question_text}</h4>
                <div class="test-options">
                    {options_html}
                </div>
                <div class="test-explanation" id="explanation_{q_idx}" style="display: none;">
                    <strong>Объяснение:</strong> {explanation}
                </div>
            </div>
            """
        
        test_html = f"""
    <div class="test-container" id="testContainer" style="display: none;">
        <h3>📝 Тест для проверки знаний</h3>
        <div id="testContent">
            {test_questions_html}
        </div>
        <div class="test-controls">
            <button onclick="checkTest()" class="test-btn">Проверить ответы</button>
            <button onclick="resetTest()" class="test-btn">Начать заново</button>
        </div>
        <div id="testResults" style="display: none;"></div>
    </div>
    <div class="test-toggle">
        <button onclick="toggleTest()" class="test-btn-primary">Пройти тест</button>
    </div>
"""
        
        # Генерируем JavaScript для теста
        test_js = f"""
        let testAnswers = {{}};
        let testChecked = false;
        
        function toggleTest() {{
            const container = document.getElementById('testContainer');
            const toggleBtn = document.querySelector('.test-toggle button');
            if (container.style.display === 'none') {{
                container.style.display = 'block';
                toggleBtn.textContent = 'Скрыть тест';
            }} else {{
                container.style.display = 'none';
                toggleBtn.textContent = 'Пройти тест';
            }}
        }}
        
        function checkTest() {{
            if (testChecked) {{
                resetTest();
                return;
            }}
            
            const questions = {len(questions)};
            let correct = 0;
            let total = 0;
            const results = [];
            
            for (let i = 0; i < questions; i++) {{
                const selected = document.querySelector(`input[name="question_${{i}}"]:checked`);
                if (selected) {{
                    total++;
                    const isCorrect = selected.dataset.correct === 'true';
                    if (isCorrect) {{
                        correct++;
                    }}
                    results.push({{
                        question: i,
                        correct: isCorrect,
                        selected: selected.value
                    }});
                    
                    // Показываем объяснение
                    const explanation = document.getElementById(`explanation_${{i}}`);
                    if (explanation) {{
                        explanation.style.display = 'block';
                    }}
                    
                    // Подсвечиваем правильный/неправильный ответ
                    const questionDiv = document.getElementById(`test_question_${{i}}`);
                    const allOptions = questionDiv.querySelectorAll('.test-option');
                    allOptions.forEach(opt => {{
                        const radio = opt.querySelector('input');
                        if (radio.dataset.correct === 'true') {{
                            opt.style.backgroundColor = '#d4edda';
                            opt.style.borderColor = '#28a745';
                        }} else if (radio.checked && radio.dataset.correct === 'false') {{
                            opt.style.backgroundColor = '#f8d7da';
                            opt.style.borderColor = '#dc3545';
                        }}
                    }});
                }}
            }}
            
            const score = total > 0 ? Math.round((correct / total) * 100) : 0;
            const passed = score >= {passing_score};
            
            const resultsHtml = `
                <div class="test-results">
                    <h4>${{passed ? '✅ Тест пройден!' : '❌ Тест не пройден'}}</h4>
                    <p>Правильных ответов: ${{correct}} из ${{total}} (${{score}}%)</p>
                    <p>Для прохождения необходимо: {passing_score}%</p>
                </div>
            `;
            
            document.getElementById('testResults').innerHTML = resultsHtml;
            document.getElementById('testResults').style.display = 'block';
            
            // Сохраняем результат в SCORM
            if (typeof SCORM_API_SetValue === 'function') {{
                SCORM_API_SetValue('cmi.core.score.raw', String(score));
                SCORM_API_SetValue('cmi.core.score.max', '100');
                SCORM_API_SetValue('cmi.core.score.min', '0');
                SCORM_API_SetValue('cmi.core.lesson_status', passed ? 'passed' : 'failed');
                SCORM_API_Commit('');
            }}
            
            testChecked = true;
            document.querySelector('.test-controls button').textContent = 'Начать заново';
        }}
        
        function resetTest() {{
            testChecked = false;
            testAnswers = {{}};
            
            // Сбрасываем все радиокнопки
            document.querySelectorAll('input[type="radio"]').forEach(radio => {{
                radio.checked = false;
            }});
            
            // Скрываем объяснения
            document.querySelectorAll('.test-explanation').forEach(exp => {{
                exp.style.display = 'none';
            }});
            
            // Сбрасываем подсветку
            document.querySelectorAll('.test-option').forEach(opt => {{
                opt.style.backgroundColor = '';
                opt.style.borderColor = '';
            }});
            
            // Скрываем результаты
            document.getElementById('testResults').style.display = 'none';
            
            document.querySelector('.test-controls button').textContent = 'Проверить ответы';
        }}
        """
    
    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape_xml(lesson.lesson_title)}</title>
    <script src="../scripts/SCORM_API_wrapper.js"></script>
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
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .header .meta {{
            margin-top: 10px;
            font-size: 14px;
            opacity: 0.9;
        }}
        .video-container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            text-align: center;
        }}
        .video-container h3 {{
            color: #667eea;
            margin-top: 0;
            margin-bottom: 20px;
        }}
        .slide-container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            min-height: 400px;
        }}
        .slide h3 {{
            color: #667eea;
            margin-top: 0;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .slide-content {{
            margin-top: 20px;
        }}
        .slide-content p {{
            margin: 15px 0;
        }}
        .slide-content pre {{
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #667eea;
        }}
        .slide-content code {{
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }}
        .navigation {{
            text-align: center;
            margin-top: 20px;
        }}
        .nav-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 15px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }}
        .nav-btn:hover {{
            background: #5568d3;
        }}
        .nav-btn.active {{
            background: #764ba2;
        }}
        .prev-next {{
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
        }}
        .prev-next button {{
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }}
        .prev-next button:hover {{
            background: #5568d3;
        }}
        .prev-next button:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}
        .test-container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .test-container h3 {{
            color: #667eea;
            margin-top: 0;
        }}
        .test-question {{
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            background: #fafafa;
        }}
        .test-question h4 {{
            color: #333;
            margin-bottom: 15px;
        }}
        .test-options {{
            margin-top: 15px;
        }}
        .test-option {{
            display: block;
            padding: 12px;
            margin: 8px 0;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .test-option:hover {{
            border-color: #667eea;
            background: #f0f0ff;
        }}
        .test-option input {{
            margin-right: 10px;
        }}
        .test-explanation {{
            margin-top: 15px;
            padding: 15px;
            background: #e7f3ff;
            border-left: 4px solid #667eea;
            border-radius: 5px;
            font-style: italic;
            color: #555;
        }}
        .test-controls {{
            text-align: center;
            margin-top: 30px;
        }}
        .test-btn, .test-btn-primary {{
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 0 10px;
        }}
        .test-btn:hover, .test-btn-primary:hover {{
            background: #5568d3;
        }}
        .test-toggle {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .test-results {{
            margin-top: 30px;
            padding: 20px;
            background: #f0f0f0;
            border-radius: 5px;
            text-align: center;
        }}
        .test-results h4 {{
            font-size: 20px;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{escape_xml(lesson.lesson_title)}</h1>
        <div class="meta">
            Модуль {module.module_number}: {escape_xml(module.module_title)} | 
            Формат: {escape_xml(str(lesson.format))} | 
            Время: {lesson.estimated_time_minutes} мин
        </div>
    </div>
    
    {video_html}
    
    {test_html}
    
    <div class="slide-container">
        {slides_html}
    </div>
    
    <div class="navigation">
        {navigation_html}
    </div>
    
    <div class="prev-next">
        <button id="prevBtn" onclick="previousSlide()">← Предыдущий</button>
        <button id="nextBtn" onclick="nextSlide()">Следующий →</button>
    </div>
    
    <script>
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        const totalSlides = slides.length;
        
        function showSlide(index) {{
            if (index < 0 || index >= totalSlides) return;
            
            // Скрываем все слайды
            slides.forEach(slide => slide.style.display = 'none');
            
            // Показываем выбранный слайд
            slides[index].style.display = 'block';
            
            // Обновляем активную кнопку
            document.querySelectorAll('.nav-btn').forEach((btn, i) => {{
                btn.classList.toggle('active', i === index);
            }});
            
            currentSlide = index;
            
            // Обновляем кнопки навигации
            document.getElementById('prevBtn').disabled = (index === 0);
            document.getElementById('nextBtn').disabled = (index === totalSlides - 1);
            
            // Сохраняем прогресс в SCORM
            if (typeof SCORM_API_SetValue === 'function') {{
                SCORM_API_SetValue('cmi.core.lesson_location', String(index));
            }}
        }}
        
        function nextSlide() {{
            if (currentSlide < totalSlides - 1) {{
                showSlide(currentSlide + 1);
            }}
        }}
        
        function previousSlide() {{
            if (currentSlide > 0) {{
                showSlide(currentSlide - 1);
            }}
        }}
        
        // Инициализация при загрузке
        window.addEventListener('load', function() {{
            showSlide(0);
            if (typeof SCORM_API_Initialize === 'function') {{
                SCORM_API_Initialize('');
            }}
        }});
        
        // Сохранение прогресса при закрытии
        window.addEventListener('beforeunload', function() {{
            if (typeof SCORM_API_SetValue === 'function') {{
                SCORM_API_SetValue('cmi.core.lesson_status', 'completed');
                SCORM_API_Commit('');
                SCORM_API_Terminate('');
            }}
        }});
        
        {test_js}
    </script>
</body>
</html>
"""
    return html_content


def download_video(video_url: str, timeout: int = 300) -> Optional[bytes]:
    """
    Скачивает видео по URL
    
    Args:
        video_url: URL видео для скачивания
        timeout: Таймаут в секундах
        
    Returns:
        bytes: Содержимое видео или None при ошибке
    """
    try:
        logger.info(f"Скачивание видео: {video_url}")
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(video_url)
            response.raise_for_status()
            logger.info(f"Видео успешно скачано, размер: {len(response.content)} байт")
            return response.content
    except Exception as e:
        logger.error(f"Ошибка скачивания видео {video_url}: {e}")
        return None


def download_video_via_heygen_api(video_id: str, heygen_service) -> Optional[bytes]:
    """
    Скачивает видео через HeyGen API с правильной аутентификацией
    
    Args:
        video_id: ID видео в HeyGen
        heygen_service: Экземпляр HeyGenService
        
    Returns:
        bytes: Содержимое видео или None при ошибке
    """
    import tempfile
    import os
    
    try:
        logger.info(f"Скачивание видео {video_id} через HeyGen API...")
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Используем метод download_video из heygen_service
            success = heygen_service.download_video(video_id, tmp_path)
            if success:
                # Читаем файл в память
                with open(tmp_path, 'rb') as f:
                    video_data = f.read()
                logger.info(f"Видео {video_id} успешно скачано через API, размер: {len(video_data)} байт")
                return video_data
            else:
                logger.error(f"Не удалось скачать видео {video_id} через HeyGen API")
                return None
        finally:
            # Удаляем временный файл
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный файл {tmp_path}: {e}")
    except Exception as e:
        logger.error(f"Ошибка скачивания видео {video_id} через HeyGen API: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return None


def export_course_scorm(course: Course, course_id: int, include_videos: bool = False) -> bytes:
    """
    Экспортирует курс в формат SCORM 1.2 (ZIP архив)
    
    Args:
        course: Объект курса
        course_id: ID курса в базе данных
        include_videos: Включать ли видео в пакет
        
    Returns:
        bytes: ZIP архив с SCORM пакетом
    """
    zip_buffer = BytesIO()
    video_files = {}  # Словарь для хранения информации о видео файлах
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        
        # 2. Создаем папку scripts и добавляем SCORM API
        scorm_api_js = create_scorm_api_js()
        zip_file.writestr("scripts/SCORM_API_wrapper.js", scorm_api_js.encode('utf-8'))
        
        # 3. Создаем HTML файлы для каждого урока и скачиваем видео (если нужно)
        for module in course.modules:
            for lesson_idx, lesson in enumerate(module.lessons):
                # Получаем детальный контент урока из базы данных
                content_data = db.get_lesson_content(course_id, module.module_number, lesson_idx)
                
                # Проверяем наличие видео
                video_filename = None
                if include_videos:
                    logger.info(f"🔍 Проверка видео для урока {module.module_number}_{lesson_idx} (курс {course_id})")
                    
                    # ВСЕГДА пытаемся получить информацию о видео напрямую из базы данных
                    # Это гарантирует, что мы получим актуальную информацию, даже если content_data устарел
                    video_info = None
                    try:
                        video_info_from_db = db.get_lesson_video_info(course_id, module.module_number, lesson_idx)
                        if video_info_from_db:
                            video_info = video_info_from_db
                            logger.info(f"✅ Видео информация получена из БД для урока {module.module_number}_{lesson_idx}: {video_info}")
                        else:
                            logger.warning(f"⚠️ Видео информация не найдена в БД для урока {module.module_number}_{lesson_idx}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка получения видео из БД для урока {module.module_number}_{lesson_idx}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                    
                    # Если не получили из БД, пробуем из content_data
                    if not video_info and content_data:
                        video_info = content_data.get('video_info', {})
                        if video_info:
                            logger.info(f"✅ Видео информация получена из content_data для урока {module.module_number}_{lesson_idx}")
                    
                    if not video_info:
                        logger.warning(f"⚠️ Видео информация отсутствует для урока {module.module_number}_{lesson_idx}")
                    else:
                        video_url = video_info.get('video_download_url') if video_info else None
                        video_status = video_info.get('video_status') if video_info else None
                        video_id = video_info.get('video_id') if video_info else None
                        
                        logger.info(f"📊 Информация о видео для урока {module.module_number}_{lesson_idx}: "
                                  f"video_id={video_id}, status={video_status}, "
                                  f"has_url={bool(video_url)}, url_length={len(video_url) if video_url else 0}")
                        
                        # Проверяем наличие URL
                        if not video_url or not video_url.strip():
                            # Если нет URL, но есть video_id, пытаемся получить URL из HeyGen API
                            if video_id:
                                logger.info(f"🔄 Для урока {module.module_number}_{lesson_idx} нет video_download_url, но есть video_id={video_id}. "
                                          f"Пытаемся получить URL из HeyGen API...")
                                try:
                                    # Инициализируем HeyGen сервис при необходимости
                                    global heygen_service
                                    if heygen_service is None:
                                        try:
                                            from backend.services.heygen_service import HeyGenService
                                            heygen_service = HeyGenService()
                                            logger.info("HeyGen сервис инициализирован для получения URL видео")
                                        except (ValueError, ImportError) as e:
                                            logger.warning(f"⚠️ Не удалось инициализировать HeyGen сервис (возможно, нет API ключа): {e}")
                                            heygen_service = False  # Помечаем, что сервис недоступен
                                    
                                    # Пытаемся получить URL из API, если сервис доступен
                                    if heygen_service and heygen_service is not False:
                                        # Сначала проверяем статус и получаем download_url напрямую
                                        try:
                                            video_status_info = heygen_service.get_video_status(video_id)
                                            api_url = video_status_info.get('download_url') if video_status_info else None
                                            api_status = video_status_info.get('status') if video_status_info else None
                                            
                                            logger.info(f"📊 Статус видео из HeyGen API для video_id={video_id}: status={api_status}, has_download_url={bool(api_url)}")
                                            
                                            if api_url:
                                                video_url = api_url
                                                logger.info(f"✅ Получен video_download_url из HeyGen API для урока {module.module_number}_{lesson_idx}: {api_url[:100]}...")
                                                
                                                # Обновляем URL и статус в базе данных для будущих запросов
                                                try:
                                                    db.update_lesson_video_info(
                                                        course_id=course_id,
                                                        module_number=module.module_number,
                                                        lesson_index=lesson_idx,
                                                        video_download_url=api_url,
                                                        video_status=api_status if api_status else video_status
                                                    )
                                                    logger.info(f"✅ Обновлен video_download_url и статус в БД для урока {module.module_number}_{lesson_idx}")
                                                except Exception as e:
                                                    logger.warning(f"⚠️ Не удалось обновить video_download_url в БД: {e}")
                                            elif api_status == 'completed':
                                                # Если статус completed, но нет URL, используем fallback URL от HeyGen
                                                fallback_url = f"https://resource2.heygen.ai/video/transcode/{video_id}/1280x720.mp4"
                                                video_url = fallback_url
                                                logger.info(f"✅ Используем fallback URL для готового видео (статус=completed): {fallback_url[:100]}...")
                                                
                                                # Обновляем URL в базе данных
                                                try:
                                                    db.update_lesson_video_info(
                                                        course_id=course_id,
                                                        module_number=module.module_number,
                                                        lesson_index=lesson_idx,
                                                        video_download_url=fallback_url,
                                                        video_status='completed'
                                                    )
                                                    logger.info(f"✅ Обновлен video_download_url (fallback) в БД для урока {module.module_number}_{lesson_idx}")
                                                except Exception as e:
                                                    logger.warning(f"⚠️ Не удалось обновить video_download_url в БД: {e}")
                                            else:
                                                logger.warning(f"⚠️ HeyGen API не вернул download_url для video_id={video_id} (статус: {api_status})")
                                        except Exception as e:
                                            logger.warning(f"⚠️ Ошибка при получении статуса видео из HeyGen API для video_id={video_id}: {e}")
                                    else:
                                        logger.debug(f"HeyGen сервис недоступен, пропускаем получение URL из API")
                                except Exception as e:
                                    logger.warning(f"⚠️ Ошибка при получении URL из HeyGen API для video_id={video_id}: {e}")
                                    import traceback
                                    logger.debug(traceback.format_exc())
                            
                            if not video_url or not video_url.strip():
                                logger.warning(f"❌ Для урока {module.module_number}_{lesson_idx} нет video_download_url или он пустой "
                                             f"(video_id={video_id}, status={video_status}). Видео будет пропущено.")
                        
                        # ВАЖНО: После получения URL из API (или если он уже был), пытаемся скачать видео
                        # Проверяем, есть ли video_id или video_url для скачивания
                        if video_id or (video_url and video_url.strip()):
                            # Исключаем только явно failed статусы
                            failed_statuses = ['failed', 'error', 'cancelled', 'timeout']
                            
                            if video_status and video_status.lower() in [s.lower() for s in failed_statuses]:
                                # Если статус явно указывает на ошибку, пропускаем
                                logger.warning(f"⚠️ Для урока {module.module_number}_{lesson_idx} статус видео '{video_status}' указывает на ошибку. Видео будет пропущено.")
                            else:
                                video_data = None
                                
                                # Приоритет: если есть video_id, используем HeyGen API (правильная аутентификация)
                                if video_id and heygen_service and heygen_service is not False:
                                    try:
                                        logger.info(f"📥 Скачивание видео для урока {module.module_number}_{lesson_idx} "
                                                  f"через HeyGen API (video_id={video_id}, status={video_status})...")
                                        video_data = download_video_via_heygen_api(video_id, heygen_service)
                                    except Exception as e:
                                        logger.warning(f"⚠️ Ошибка при скачивании через HeyGen API для video_id={video_id}: {e}")
                                        # Пробуем fallback - прямое скачивание по URL, если он есть
                                        if video_url and video_url.strip():
                                            logger.info(f"📥 Пробуем прямое скачивание по URL как fallback...")
                                            video_data = download_video(video_url)
                                
                                # Если не получилось через API или нет video_id, пробуем прямое скачивание по URL
                                if not video_data and video_url and video_url.strip():
                                    logger.info(f"📥 Начинаем прямое скачивание видео для урока {module.module_number}_{lesson_idx} "
                                              f"из {video_url[:100]}... (status={video_status}, video_id={video_id})")
                                    video_data = download_video(video_url)
                                
                                if video_data:
                                    # Определяем расширение файла
                                    video_ext = 'mp4'  # По умолчанию MP4
                                    if video_url:
                                        if '.mp4' in video_url.lower():
                                            video_ext = 'mp4'
                                        elif '.webm' in video_url.lower():
                                            video_ext = 'webm'
                                    
                                    video_filename = f"lesson_{module.module_number}_{lesson_idx}.{video_ext}"
                                    video_path = f"videos/{video_filename}"
                                    
                                    # Сохраняем видео в ZIP
                                    zip_file.writestr(video_path, video_data)
                                    video_files[f"{module.module_number}_{lesson_idx}"] = video_filename
                                    logger.info(f"✅ Видео успешно добавлено в пакет: {video_path} "
                                              f"(размер: {len(video_data)} байт, {len(video_data) / 1024 / 1024:.2f} MB, "
                                              f"статус был: {video_status})")
                                else:
                                    logger.error(f"❌ Не удалось скачать видео для урока {module.module_number}_{lesson_idx} "
                                               f"(статус: {video_status}, video_id: {video_id}, has_url: {bool(video_url)})")
                        else:
                            logger.warning(f"⚠️ Для урока {module.module_number}_{lesson_idx} нет video_id и video_url. Видео будет пропущено.")
                    
                    # Итоговая статистика для урока
                    if video_filename:
                        logger.info(f"✅ Урок {module.module_number}_{lesson_idx}: видео включено в пакет")
                    else:
                        logger.warning(f"⚠️ Урок {module.module_number}_{lesson_idx}: видео НЕ включено в пакет")
                
                # Получаем тест для урока, если он есть
                test_data = None
                if content_data and 'test' in content_data:
                    test_data = content_data['test']
                else:
                    # Пробуем получить тест напрямую из БД
                    try:
                        test_data = db.get_lesson_test(course_id, module.module_number, lesson_idx)
                    except Exception as e:
                        logger.debug(f"Тест для урока {module.module_number}_{lesson_idx} не найден: {e}")
                
                # Создаем HTML для урока
                lesson_html = create_lesson_html(
                    course=course,
                    module=module,
                    lesson=lesson,
                    lesson_index=lesson_idx,
                    content_data=content_data,
                    include_video=include_videos and video_filename is not None,
                    video_filename=video_filename,
                    test_data=test_data
                )
                
                # Сохраняем в ZIP
                lesson_path = f"lessons/lesson_{module.module_number}_{lesson_idx}.html"
                zip_file.writestr(lesson_path, lesson_html.encode('utf-8'))
        
        # 4. Логируем итоговую статистику по видео
        logger.info(f"📊 Итоговая статистика SCORM экспорта для курса {course_id}:")
        logger.info(f"   Всего уроков: {sum(len(m.lessons) for m in course.modules)}")
        logger.info(f"   Уроков с видео в пакете: {len(video_files)}")
        if video_files:
            logger.info(f"   Видео файлы: {list(video_files.values())}")
        else:
            logger.warning(f"   ⚠️ Видео файлы отсутствуют в пакете!")
        
        # 5. Добавляем стартовую страницу курса
        start_page = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape_xml(course.course_title)}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        h1 {{
            color: #667eea;
            margin-top: 0;
        }}
        .meta {{
            color: #666;
            margin: 20px 0;
        }}
        .modules {{
            margin-top: 30px;
        }}
        .module {{
            margin: 20px 0;
            padding: 20px;
            background: #f5f5f5;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        .module h2 {{
            color: #764ba2;
            margin-top: 0;
        }}
        .lessons {{
            margin-top: 15px;
        }}
        .lesson-link {{
            display: block;
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-radius: 3px;
            text-decoration: none;
            color: #333;
            transition: background 0.3s;
        }}
        .lesson-link:hover {{
            background: #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{escape_xml(course.course_title)}</h1>
        <div class="meta">
            <p><strong>Аудитория:</strong> {escape_xml(course.target_audience)}</p>
"""
        if course.duration_weeks:
            start_page += f"            <p><strong>Длительность:</strong> {course.duration_weeks} недель</p>\n"
        if course.duration_hours:
            start_page += f"            <p><strong>Часов в неделю:</strong> {course.duration_hours}</p>\n"
        
        start_page += """        </div>
        <div class="modules">
            <h2>Содержание курса</h2>
"""
        
        for module in course.modules:
            start_page += f"""
            <div class="module">
                <h2>Модуль {module.module_number}: {escape_xml(module.module_title)}</h2>
                <p>{escape_xml(module.module_goal)}</p>
                <div class="lessons">
"""
            for lesson_idx, lesson in enumerate(module.lessons):
                lesson_path = f"lessons/lesson_{module.module_number}_{lesson_idx}.html"
                start_page += f"""
                    <a href="{lesson_path}" class="lesson-link">
                        {lesson_idx + 1}. {escape_xml(lesson.lesson_title)}
                    </a>
"""
            start_page += """                </div>
            </div>
"""
        
        start_page += """        </div>
    </div>
</body>
</html>
"""
        zip_file.writestr("index.html", start_page.encode('utf-8'))
        
        # 1. Создаем imsmanifest.xml (после того, как все файлы добавлены)
        manifest_xml = create_scorm_manifest(course, course_id, video_files)
        zip_file.writestr("imsmanifest.xml", manifest_xml.encode('utf-8'))
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

