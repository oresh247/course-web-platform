"""
База данных SQLite для хранения курсов
"""
import sqlite3
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CourseDatabase:
    """Класс для работы с базой данных курсов"""
    
    def __init__(self, db_path: str = "courses.db"):
        """
        Инициализация базы данных
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Создание таблиц в базе данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица курсов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_title TEXT NOT NULL,
                    target_audience TEXT NOT NULL,
                    duration_hours INTEGER,
                    duration_weeks INTEGER,
                    course_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица модулей с контентом
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS module_contents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER NOT NULL,
                    module_number INTEGER NOT NULL,
                    module_title TEXT NOT NULL,
                    content_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
                    UNIQUE (course_id, module_number)
                )
            """)
            
            # Таблица уроков с детальным контентом
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lesson_contents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER NOT NULL,
                    module_number INTEGER NOT NULL,
                    lesson_index INTEGER NOT NULL,
                    lesson_title TEXT NOT NULL,
                    content_data TEXT NOT NULL,
                    video_id TEXT,
                    video_download_url TEXT,
                    video_status TEXT,
                    video_generated_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
                    UNIQUE (course_id, module_number, lesson_index)
                )
            """)
            
            # Добавляем колонки для видео, если их еще нет (для существующих БД)
            try:
                cursor.execute("ALTER TABLE lesson_contents ADD COLUMN video_id TEXT")
            except sqlite3.OperationalError:
                pass  # Колонка уже существует
            
            try:
                cursor.execute("ALTER TABLE lesson_contents ADD COLUMN video_download_url TEXT")
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute("ALTER TABLE lesson_contents ADD COLUMN video_status TEXT")
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute("ALTER TABLE lesson_contents ADD COLUMN video_generated_at TIMESTAMP")
            except sqlite3.OperationalError:
                pass
            
            conn.commit()
            logger.info("✅ База данных инициализирована")
    
    def save_course(self, course_data: Dict[str, Any]) -> int:
        """
        Сохранить курс в базу данных
        
        Args:
            course_data: Данные курса в формате словаря
            
        Returns:
            ID созданного курса
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO courses (
                    course_title, target_audience, duration_hours, 
                    duration_weeks, course_data, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                course_data.get('course_title', 'Без названия'),
                course_data.get('target_audience', 'Не указано'),
                course_data.get('duration_hours'),
                course_data.get('duration_weeks'),
                json.dumps(course_data, ensure_ascii=False),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            course_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"✅ Курс сохранен с ID: {course_id}")
            return course_id
    
    def get_course(self, course_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить курс по ID
        
        Args:
            course_id: ID курса
            
        Returns:
            Данные курса или None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM courses WHERE id = ?
            """, (course_id,))
            
            row = cursor.fetchone()
            
            if row:
                course_data = json.loads(row['course_data'])
                course_data['id'] = row['id']
                course_data['created_at'] = row['created_at']
                course_data['updated_at'] = row['updated_at']
                return course_data
            
            return None
    
    def get_all_courses(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Получить список всех курсов
        
        Args:
            limit: Максимальное количество курсов
            offset: Смещение для пагинации
            
        Returns:
            Список курсов
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, course_title, target_audience, 
                       duration_hours, duration_weeks, created_at, updated_at
                FROM courses
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            rows = cursor.fetchall()
            
            courses = []
            for row in rows:
                courses.append({
                    'id': row['id'],
                    'course_title': row['course_title'],
                    'target_audience': row['target_audience'],
                    'duration_hours': row['duration_hours'],
                    'duration_weeks': row['duration_weeks'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return courses
    
    def update_course(self, course_id: int, course_data: Dict[str, Any]) -> bool:
        """
        Обновить курс
        
        Args:
            course_id: ID курса
            course_data: Новые данные курса
            
        Returns:
            True если обновление успешно
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE courses 
                SET course_title = ?, 
                    target_audience = ?, 
                    duration_hours = ?,
                    duration_weeks = ?,
                    course_data = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                course_data.get('course_title', 'Без названия'),
                course_data.get('target_audience', 'Не указано'),
                course_data.get('duration_hours'),
                course_data.get('duration_weeks'),
                json.dumps(course_data, ensure_ascii=False),
                datetime.now().isoformat(),
                course_id
            ))
            
            conn.commit()
            
            return cursor.rowcount > 0
    
    def delete_course(self, course_id: int) -> bool:
        """
        Удалить курс
        
        Args:
            course_id: ID курса
            
        Returns:
            True если удаление успешно
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def save_module_content(
        self, 
        course_id: int, 
        module_number: int, 
        module_title: str,
        content_data: Dict[str, Any]
    ) -> int:
        """
        Сохранить контент модуля (лекции и слайды)
        
        Args:
            course_id: ID курса
            module_number: Номер модуля
            module_title: Название модуля
            content_data: Данные контента модуля
            
        Returns:
            ID созданной записи
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Проверяем, существует ли уже контент для этого модуля
            cursor.execute("""
                SELECT id FROM module_contents 
                WHERE course_id = ? AND module_number = ?
            """, (course_id, module_number))
            
            existing = cursor.fetchone()
            
            if existing:
                # Обновляем существующий
                cursor.execute("""
                    UPDATE module_contents 
                    SET module_title = ?, content_data = ?
                    WHERE course_id = ? AND module_number = ?
                """, (
                    module_title,
                    json.dumps(content_data, ensure_ascii=False),
                    course_id,
                    module_number
                ))
                record_id = existing[0]
            else:
                # Создаем новый
                cursor.execute("""
                    INSERT INTO module_contents (
                        course_id, module_number, module_title, content_data
                    ) VALUES (?, ?, ?, ?)
                """, (
                    course_id,
                    module_number,
                    module_title,
                    json.dumps(content_data, ensure_ascii=False)
                ))
                record_id = cursor.lastrowid
            
            conn.commit()
            logger.info(f"✅ Контент модуля {module_number} сохранен (ID: {record_id})")
            return record_id
    
    def get_module_content(self, course_id: int, module_number: int) -> Optional[Dict[str, Any]]:
        """
        Получить контент модуля
        
        Args:
            course_id: ID курса
            module_number: Номер модуля
            
        Returns:
            Данные контента модуля или None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM module_contents 
                WHERE course_id = ? AND module_number = ?
            """, (course_id, module_number))
            
            row = cursor.fetchone()
            
            if row:
                content_data = json.loads(row['content_data'])
                return content_data
            
            return None

    def delete_module_content(self, course_id: int, module_number: int) -> int:
        """Удалить запись детального контента модуля.

        Returns количество удалённых строк.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM module_contents
                WHERE course_id = ? AND module_number = ?
                """,
                (course_id, module_number),
            )
            conn.commit()
            return cursor.rowcount
    
    def update_lesson_video_info(
        self,
        course_id: int,
        module_number: int,
        lesson_index: int,
        video_id: Optional[str] = None,
        video_download_url: Optional[str] = None,
        video_status: Optional[str] = None,
        video_generated_at: Optional[datetime] = None
    ) -> bool:
        """
        Обновляет информацию о видео для урока
        
        Args:
            course_id: ID курса
            module_number: Номер модуля
            lesson_index: Индекс урока
            video_id: ID видео в HeyGen
            video_download_url: URL для скачивания видео
            video_status: Статус видео
            video_generated_at: Дата генерации видео
            
        Returns:
            True если обновление прошло успешно
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Сначала проверяем, существует ли запись
            cursor.execute("""
                SELECT id FROM lesson_contents
                WHERE course_id = ? AND module_number = ? AND lesson_index = ?
            """, (course_id, module_number, lesson_index))
            
            row = cursor.fetchone()
            
            if row:
                # Обновляем существующую запись
                update_fields = []
                params = []
                
                if video_id is not None:
                    update_fields.append("video_id = ?")
                    params.append(video_id)
                
                if video_download_url is not None:
                    update_fields.append("video_download_url = ?")
                    params.append(video_download_url)
                
                if video_status is not None:
                    update_fields.append("video_status = ?")
                    params.append(video_status)
                
                if video_generated_at is not None:
                    update_fields.append("video_generated_at = ?")
                    params.append(video_generated_at.isoformat() if isinstance(video_generated_at, datetime) else video_generated_at)
                
                if update_fields:
                    params.extend([course_id, module_number, lesson_index])
                    cursor.execute(f"""
                        UPDATE lesson_contents
                        SET {', '.join(update_fields)}
                        WHERE course_id = ? AND module_number = ? AND lesson_index = ?
                    """, params)
                    conn.commit()
                    logger.info(f"Обновлена информация о видео для урока {course_id}/{module_number}/{lesson_index}")
                    return True
            else:
                logger.warning(f"Урок {course_id}/{module_number}/{lesson_index} не найден для обновления видео")
                return False

    def save_lesson_content(
        self,
        course_id: int,
        module_number: int,
        lesson_index: int,
        lesson_title: str,
        content_data: Dict[str, Any]
    ) -> int:
        """
        Сохранить детальный контент урока
        
        Args:
            course_id: ID курса
            module_number: Номер модуля
            lesson_index: Индекс урока
            lesson_title: Название урока
            content_data: Данные контента урока
            
        Returns:
            ID созданной записи
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Проверяем существование
            cursor.execute("""
                SELECT id FROM lesson_contents
                WHERE course_id = ? AND module_number = ? AND lesson_index = ?
            """, (course_id, module_number, lesson_index))
            
            existing = cursor.fetchone()
            
            if existing:
                # Обновляем
                cursor.execute("""
                    UPDATE lesson_contents
                    SET lesson_title = ?, content_data = ?
                    WHERE course_id = ? AND module_number = ? AND lesson_index = ?
                """, (
                    lesson_title,
                    json.dumps(content_data, ensure_ascii=False),
                    course_id,
                    module_number,
                    lesson_index
                ))
                record_id = existing[0]
            else:
                # Создаем новый
                cursor.execute("""
                    INSERT INTO lesson_contents (
                        course_id, module_number, lesson_index, lesson_title, content_data
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    course_id,
                    module_number,
                    lesson_index,
                    lesson_title,
                    json.dumps(content_data, ensure_ascii=False)
                ))
                record_id = cursor.lastrowid
            
            conn.commit()
            logger.info(f"✅ Контент урока {lesson_index} сохранен (ID: {record_id})")
            return record_id
    
    def get_lesson_content(
        self,
        course_id: int,
        module_number: int,
        lesson_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Получить детальный контент урока
        
        Args:
            course_id: ID курса
            module_number: Номер модуля
            lesson_index: Индекс урока
            
        Returns:
            Данные контента урока или None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM lesson_contents
                WHERE course_id = ? AND module_number = ? AND lesson_index = ?
            """, (course_id, module_number, lesson_index))
            
            row = cursor.fetchone()
            
            if row:
                content_data = json.loads(row['content_data'])
                
                # Добавляем информацию о видео, если она есть
                if row.get('video_id'):
                    content_data['video_info'] = {
                        'video_id': row['video_id'],
                        'video_download_url': row.get('video_download_url'),
                        'video_status': row.get('video_status'),
                        'video_generated_at': row.get('video_generated_at')
                    }
                
                return content_data
            
            return None

    def delete_lesson_content(self, course_id: int, module_number: int, lesson_index: int) -> int:
        """Удалить запись детального контента одного урока."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM lesson_contents
                WHERE course_id = ? AND module_number = ? AND lesson_index = ?
                """,
                (course_id, module_number, lesson_index),
            )
            conn.commit()
            return cursor.rowcount

    def delete_lesson_contents_for_module(self, course_id: int, module_number: int) -> int:
        """Удалить все записи детального контента уроков для указанного модуля.

        Returns количество удалённых строк.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM lesson_contents
                WHERE course_id = ? AND module_number = ?
                """,
                (course_id, module_number),
            )
            conn.commit()
            return cursor.rowcount


# Глобальный экземпляр базы данных
db = CourseDatabase()

