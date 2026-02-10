"""
Тестовый скрипт для проверки обработки переносов строк в SCORM экспорте.

Проверяет, что символы \n правильно преобразуются в HTML переносы строк.
"""
import sys
import os
import logging
import zipfile
from io import BytesIO

# Добавляем корневую директорию в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.models.domain import Course, Module, Lesson
from backend.services.export.scorm import export_course_scorm, create_lesson_html

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_newlines_in_content():
    """Тестирует обработку переносов строк в контенте слайда."""
    
    # Создаем тестовый курс с контентом, содержащим переносы строк
    course = Course(
        course_title="Тестовый курс",
        target_audience="Разработчики",
        modules=[
            Module(
                module_number=1,
                module_title="Тестовый модуль",
                module_goal="Проверка переносов строк",
                lessons=[
                    Lesson(
                        lesson_title="Тестовый урок",
                        lesson_goal="Проверка",
                        format="lecture",
                        estimated_time_minutes=15,
                        content_outline=["Пункт 1", "Пункт 2"],
                        assessment="Тест"
                    )
                ]
            )
        ]
    )
    
    # Тестовый контент с переносами строк
    content_data = {
        "slides": [
            {
                "title": "Тестовый слайд с кодом",
                "content": "Первая строка\nВторая строка\nТретья строка",
                "slide_type": "python",
                "code_example": "from selenium import webdriver\n\ndriver = webdriver.Chrome()\ndriver.get('http://example.com')\nassert 'Example Domain' in driver.title\ndriver.quit()"
            },
            {
                "title": "Слайд с параграфами",
                "content": "Первый параграф.\n\nВторой параграф.\n\nТретий параграф.",
                "slide_type": "content"
            }
        ]
    }
    
    # Создаем HTML для урока
    module = course.modules[0]
    lesson = module.lessons[0]
    
    logger.info("Создание HTML для урока с переносами строк...")
    html_content = create_lesson_html(
        course=course,
        module=module,
        lesson=lesson,
        lesson_index=0,
        content_data=content_data,
        include_video=False,
        video_filename=None,
        test_data=None,
        scorm_version="1.2"
    )
    
    # Проверяем, что переносы строк обработаны правильно
    logger.info("\n" + "="*80)
    logger.info("ПРОВЕРКА ОБРАБОТКИ ПЕРЕНОСОВ СТРОК")
    logger.info("="*80)
    
    # 1. Проверяем, что в обычном тексте \n заменены на <br>
    if "Первая строка<br>Вторая строка<br>Третья строка" in html_content:
        logger.info("✅ ТЕСТ 1 ПРОЙДЕН: Одиночные переносы строк заменены на <br>")
    else:
        logger.error("❌ ТЕСТ 1 ПРОВАЛЕН: Одиночные переносы строк НЕ заменены на <br>")
        # Проверяем, что в контенте нет необработанных \n
        if "Первая строка\\nВторая строка" in html_content:
            logger.error("   Найдены экранированные \\n вместо <br>")
        elif "Первая строка\nВторая строка" in html_content:
            logger.error("   Найдены необработанные символы переноса строки")
    
    # 2. Проверяем, что двойные переносы \n\n создают новые параграфы
    if "<p>Первый параграф.</p>" in html_content and "<p>Второй параграф.</p>" in html_content:
        logger.info("✅ ТЕСТ 2 ПРОЙДЕН: Двойные переносы строк создают отдельные параграфы")
    else:
        logger.error("❌ ТЕСТ 2 ПРОВАЛЕН: Двойные переносы строк НЕ создают отдельные параграфы")
    
    # 3. Проверяем, что код в <pre> блоке сохраняет переносы строк
    if "from selenium import webdriver" in html_content and "driver = webdriver.Chrome()" in html_content:
        logger.info("✅ ТЕСТ 3 ПРОЙДЕН: Код содержит правильные элементы")
        
        # Проверяем, что нет экранированных \n в коде
        if "webdriver\\n\\ndriver" in html_content or "webdriver\\ndriver" in html_content:
            logger.error("❌ ТЕСТ 3 ПРОВАЛЕН: В коде найдены экранированные \\n")
        else:
            logger.info("✅ ТЕСТ 3 ДОПОЛНИТЕЛЬНО: В коде нет экранированных \\n")
    else:
        logger.error("❌ ТЕСТ 3 ПРОВАЛЕН: Код не найден или поврежден")
    
    # 4. Проверяем общую структуру HTML
    if "<pre><code" in html_content and "</code></pre>" in html_content:
        logger.info("✅ ТЕСТ 4 ПРОЙДЕН: HTML содержит правильные блоки кода")
    else:
        logger.error("❌ ТЕСТ 4 ПРОВАЛЕН: HTML не содержит блоки кода")
    
    logger.info("="*80 + "\n")
    
    # Сохраняем HTML для ручной проверки
    output_path = "/tmp/test_scorm_lesson.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    logger.info(f"HTML сохранен в {output_path} для ручной проверки")
    
    return html_content


def test_scorm_export():
    """Тестирует полный экспорт SCORM с переносами строк."""
    
    logger.info("\n" + "="*80)
    logger.info("ТЕСТ ПОЛНОГО SCORM ЭКСПОРТА")
    logger.info("="*80)
    
    # Создаем тестовый курс
    course = Course(
        course_title="Тестовый SCORM курс",
        target_audience="Разработчики",
        modules=[
            Module(
                module_number=1,
                module_title="Модуль 1",
                module_goal="Тест",
                lessons=[
                    Lesson(
                        lesson_title="Урок 1",
                        lesson_goal="Проверка экспорта",
                        format="lecture",
                        estimated_time_minutes=15,
                        content_outline=["Пункт 1"],
                        assessment="Тест"
                    )
                ]
            )
        ]
    )
    
    try:
        # Экспортируем курс в SCORM без видео
        logger.info("Экспорт курса в SCORM 1.2...")
        scorm_data = export_course_scorm(
            course=course,
            course_id=999,  # Тестовый ID
            include_videos=False,
            scorm_version="1.2"
        )
        
        logger.info(f"✅ SCORM пакет создан, размер: {len(scorm_data)} байт")
        
        # Проверяем содержимое ZIP
        zip_buffer = BytesIO(scorm_data)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            file_list = zf.namelist()
            logger.info(f"Файлы в архиве: {', '.join(file_list)}")
            
            # Проверяем наличие обязательных файлов
            required_files = [
                'imsmanifest.xml',
                'scripts/SCORM_API_wrapper.js',
                'lessons/lesson_1_0.html',
                'index.html'
            ]
            
            for required_file in required_files:
                if required_file in file_list:
                    logger.info(f"✅ Файл {required_file} присутствует")
                else:
                    logger.error(f"❌ Файл {required_file} ОТСУТСТВУЕТ")
        
        # Сохраняем архив для ручной проверки
        output_path = "/tmp/test_scorm_export.zip"
        with open(output_path, 'wb') as f:
            f.write(scorm_data)
        logger.info(f"\n✅ SCORM архив сохранен в {output_path}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при экспорте SCORM: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    logger.info("Запуск тестов обработки переносов строк в SCORM экспорте\n")
    
    # Тест 1: Проверка обработки переносов в HTML
    test_newlines_in_content()
    
    # Тест 2: Полный экспорт SCORM
    test_scorm_export()
    
    logger.info("\n✅ Все тесты завершены")
