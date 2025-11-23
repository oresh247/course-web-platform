"""
База данных PostgreSQL для Render
"""
import os
import psycopg2
import psycopg2.extras
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class RenderDatabase:
    """Класс для работы с PostgreSQL базой данных на Render"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Инициализация базы данных
        
        Args:
            database_url: URL подключения к PostgreSQL (если не указан, берется из переменных окружения)
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        
        if not self.database_url:
            raise ValueError("DATABASE_URL не найден в переменных окружения")
        
        # Парсим URL для получения параметров подключения
        parsed_url = urlparse(self.database_url)
        
        self.connection_params = {
            'host': parsed_url.hostname,
            'port': parsed_url.port or 5432,
            'database': parsed_url.path[1:],  # убираем первый слеш
            'user': parsed_url.username,
            'password': parsed_url.password,
            'sslmode': 'require'  # Render требует SSL
        }
        
        self._init_db()
    
    def _get_connection(self):
        """Получить соединение с базой данных"""
        try:
            conn = psycopg2.connect(**self.connection_params)
            return conn
        except psycopg2.Error as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise
    
    def _init_db(self):
        """Создание таблиц в базе данных"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    
                    # Таблица курсов
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS courses (
                            id SERIAL PRIMARY KEY,
                            course_title VARCHAR(255) NOT NULL,
                            target_audience VARCHAR(255) NOT NULL,
                            duration_hours INTEGER,
                            duration_weeks INTEGER,
                            course_data JSONB NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Таблица модулей с контентом
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS module_contents (
                            id SERIAL PRIMARY KEY,
                            course_id INTEGER NOT NULL,
                            module_number INTEGER NOT NULL,
                            module_title VARCHAR(255) NOT NULL,
                            content_data JSONB NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
                            UNIQUE (course_id, module_number)
                        )
                    """)
                    
                    # Таблица уроков с детальным контентом
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS lesson_contents (
                            id SERIAL PRIMARY KEY,
                            course_id INTEGER NOT NULL,
                            module_number INTEGER NOT NULL,
                            lesson_index INTEGER NOT NULL,
                            lesson_title VARCHAR(255) NOT NULL,
                            content_data JSONB NOT NULL,
                            video_id TEXT,
                            video_download_url TEXT,
                            video_status TEXT,
                            video_generated_at TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
                            UNIQUE (course_id, module_number, lesson_index)
                        )
                    """)
                    
                    # Миграции для совместимости со старыми схемами таблицы
                    try:
                        cursor.execute("ALTER TABLE lesson_contents ADD COLUMN IF NOT EXISTS lesson_title VARCHAR(255)")
                    except psycopg2.Error:
                        pass
                    try:
                        cursor.execute("ALTER TABLE lesson_contents ALTER COLUMN lesson_title SET DEFAULT ''")
                    except psycopg2.Error:
                        pass
                    try:
                        cursor.execute("UPDATE lesson_contents SET lesson_title = '' WHERE lesson_title IS NULL")
                    except psycopg2.Error:
                        pass
                    try:
                        cursor.execute("ALTER TABLE lesson_contents ALTER COLUMN lesson_title SET NOT NULL")
                    except psycopg2.Error:
                        pass

                    # Добавляем колонки для видео, если их еще нет
                    try:
                        cursor.execute("ALTER TABLE lesson_contents ADD COLUMN IF NOT EXISTS video_id TEXT")
                    except psycopg2.Error:
                        pass
                    
                    try:
                        cursor.execute("ALTER TABLE lesson_contents ADD COLUMN IF NOT EXISTS video_download_url TEXT")
                    except psycopg2.Error:
                        pass
                    
                    try:
                        cursor.execute("ALTER TABLE lesson_contents ADD COLUMN IF NOT EXISTS video_status TEXT")
                    except psycopg2.Error:
                        pass
                    
                    try:
                        cursor.execute("ALTER TABLE lesson_contents ADD COLUMN IF NOT EXISTS video_generated_at TIMESTAMP")
                    except psycopg2.Error:
                        pass
                    
                    # Создаем индексы для улучшения производительности
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_courses_created_at 
                        ON courses (created_at DESC)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_module_contents_course_id 
                        ON module_contents (course_id)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_lesson_contents_course_id 
                        ON lesson_contents (course_id)
                    """)
                    
                    conn.commit()
                    logger.info("✅ PostgreSQL база данных инициализирована")
                    
        except psycopg2.Error as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
    
    def save_course(self, course_data: Dict[str, Any]) -> int:
        """
        Сохранить курс в базу данных
        
        Args:
            course_data: Данные курса в формате словаря
            
        Returns:
            ID созданного курса
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    
                    cursor.execute("""
                        INSERT INTO courses (
                            course_title, target_audience, duration_hours, 
                            duration_weeks, course_data, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        course_data.get('course_title', 'Без названия'),
                        course_data.get('target_audience', 'Не указано'),
                        course_data.get('duration_hours'),
                        course_data.get('duration_weeks'),
                        json.dumps(course_data, ensure_ascii=False),
                        datetime.now(),
                        datetime.now()
                    ))
                    
                    course_id = cursor.fetchone()[0]
                    conn.commit()
                    
                    logger.info(f"✅ Курс сохранен с ID: {course_id}")
                    return course_id
                    
        except psycopg2.Error as e:
            logger.error(f"Ошибка сохранения курса: {e}")
            raise
    
    def get_course(self, course_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить курс по ID
        
        Args:
            course_id: ID курса
            
        Returns:
            Данные курса или None
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    
                    cursor.execute("""
                        SELECT * FROM courses WHERE id = %s
                    """, (course_id,))
                    
                    row = cursor.fetchone()
                    
                    if row:
                        course_data = row['course_data']
                        # Если course_data является строкой, парсим JSON
                        if isinstance(course_data, str):
                            import json
                            course_data = json.loads(course_data)
                        
                        course_data['id'] = row['id']
                        course_data['created_at'] = row['created_at'].isoformat()
                        course_data['updated_at'] = row['updated_at'].isoformat()
                        return course_data
                    
                    return None
                    
        except psycopg2.Error as e:
            logger.error(f"Ошибка получения курса: {e}")
            raise
    
    def get_all_courses(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Получить список всех курсов
        
        Args:
            limit: Максимальное количество курсов
            offset: Смещение для пагинации
            
        Returns:
            Список курсов
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    
                    cursor.execute("""
                        SELECT id, course_title, target_audience, 
                               duration_hours, duration_weeks, created_at, updated_at
                        FROM courses
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
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
                            'created_at': row['created_at'].isoformat(),
                            'updated_at': row['updated_at'].isoformat()
                        })
                    
                    return courses
                    
        except psycopg2.Error as e:
            logger.error(f"Ошибка получения списка курсов: {e}")
            raise
    
    def update_course(self, course_id: int, course_data: Dict[str, Any]) -> bool:
        """
        Обновить курс
        
        Args:
            course_id: ID курса
            course_data: Новые данные курса
            
        Returns:
            True если обновление успешно
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    
                    cursor.execute("""
                        UPDATE courses 
                        SET course_title = %s, 
                            target_audience = %s, 
                            duration_hours = %s,
                            duration_weeks = %s,
                            course_data = %s,
                            updated_at = %s
                        WHERE id = %s
                    """, (
                        course_data.get('course_title', 'Без названия'),
                        course_data.get('target_audience', 'Не указано'),
                        course_data.get('duration_hours'),
                        course_data.get('duration_weeks'),
                        json.dumps(course_data, ensure_ascii=False),
                        datetime.now(),
                        course_id
                    ))
                    
                    conn.commit()
                    
                    return cursor.rowcount > 0
                    
        except psycopg2.Error as e:
            logger.error(f"Ошибка обновления курса: {e}")
            raise
    
    def delete_course(self, course_id: int) -> bool:
        """
        Удалить курс
        
        Args:
            course_id: ID курса
            
        Returns:
            True если удаление успешно
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    
                    cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
                    conn.commit()
                    
                    return cursor.rowcount > 0
                    
        except psycopg2.Error as e:
            logger.error(f"Ошибка удаления курса: {e}")
            raise
    
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
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    
                    # Проверяем, существует ли уже контент для этого модуля
                    cursor.execute("""
                        SELECT id FROM module_contents 
                        WHERE course_id = %s AND module_number = %s
                    """, (course_id, module_number))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Обновляем существующий
                        cursor.execute("""
                            UPDATE module_contents 
                            SET module_title = %s, content_data = %s
                            WHERE course_id = %s AND module_number = %s
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
                            ) VALUES (%s, %s, %s, %s)
                            RETURNING id
                        """, (
                            course_id,
                            module_number,
                            module_title,
                            json.dumps(content_data, ensure_ascii=False)
                        ))
                        record_id = cursor.fetchone()[0]
                    
                    conn.commit()
                    logger.info(f"✅ Контент модуля {module_number} сохранен (ID: {record_id})")
                    return record_id
                    
        except psycopg2.Error as e:
            logger.error(f"Ошибка сохранения контента модуля: {e}")
            raise
    
    def get_module_content(self, course_id: int, module_number: int) -> Optional[Dict[str, Any]]:
        """
        Получить контент модуля
        
        Args:
            course_id: ID курса
            module_number: Номер модуля
            
        Returns:
            Данные контента модуля или None
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    
                    cursor.execute("""
                        SELECT * FROM module_contents 
                        WHERE course_id = %s AND module_number = %s
                    """, (course_id, module_number))
                    
                    row = cursor.fetchone()
                    
                    if row:
                        content_data = row['content_data']
                        # Если content_data является строкой, парсим JSON
                        if isinstance(content_data, str):
                            import json
                            content_data = json.loads(content_data)
                        return content_data
                    
                    return None
                    
        except psycopg2.Error as e:
            logger.error(f"Ошибка получения контента модуля: {e}")
            raise
    
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
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    
                    # Проверяем существование
                    cursor.execute("""
                        SELECT id FROM lesson_contents
                        WHERE course_id = %s AND module_number = %s AND lesson_index = %s
                    """, (course_id, module_number, lesson_index))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Обновляем
                        cursor.execute("""
                            UPDATE lesson_contents
                            SET lesson_title = %s, content_data = %s
                            WHERE course_id = %s AND module_number = %s AND lesson_index = %s
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
                            ) VALUES (%s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            course_id,
                            module_number,
                            lesson_index,
                            lesson_title,
                            json.dumps(content_data, ensure_ascii=False)
                        ))
                        record_id = cursor.fetchone()[0]
                    
                    conn.commit()
                    logger.info(f"✅ Контент урока {lesson_index} сохранен (ID: {record_id})")
                    return record_id
                    
        except psycopg2.Error as e:
            logger.error(f"Ошибка сохранения контента урока: {e}")
            raise
    
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
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    
                    cursor.execute("""
                        SELECT * FROM lesson_contents
                        WHERE course_id = %s AND module_number = %s AND lesson_index = %s
                    """, (course_id, module_number, lesson_index))
                    
                    row = cursor.fetchone()
                    
                    if row:
                        content_data = row['content_data']
                        # Если content_data является строкой, парсим JSON
                        if isinstance(content_data, str):
                            import json
                            content_data = json.loads(content_data)
                        
                        # Добавляем информацию о видео, если она есть (проверяем video_id или video_download_url)
                        if row.get('video_id') or row.get('video_download_url'):
                            content_data['video_info'] = {
                                'video_id': row.get('video_id'),
                                'video_download_url': row.get('video_download_url'),
                                'video_status': row.get('video_status'),
                                'video_generated_at': row.get('video_generated_at').isoformat() if row.get('video_generated_at') else None
                            }
                        
                        return content_data
                    
                    return None
                    
        except psycopg2.Error as e:
            logger.error(f"Ошибка получения контента урока: {e}")
            return None
    
    def save_lesson_test(
        self,
        course_id: int,
        module_number: int,
        lesson_index: int,
        lesson_title: str,
        test_data: Dict[str, Any]
    ) -> int:
        """
        Сохранить тест для урока
        
        Args:
            course_id: ID курса
            module_number: Номер модуля
            lesson_index: Индекс урока
            lesson_title: Название урока
            test_data: Данные теста (LessonTest в виде dict)
            
        Returns:
            ID созданной/обновленной записи
        """
        try:
            import json
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Получаем существующий контент, если есть
                    existing_content = self.get_lesson_content(course_id, module_number, lesson_index)
                    
                    if existing_content:
                        # Обновляем существующий контент, добавляя/обновляя тест
                        existing_content['test'] = test_data
                        cursor.execute("""
                            UPDATE lesson_contents
                            SET content_data = %s
                            WHERE course_id = %s AND module_number = %s AND lesson_index = %s
                        """, (
                            json.dumps(existing_content, ensure_ascii=False),
                            course_id,
                            module_number,
                            lesson_index
                        ))
                        record_id = cursor.rowcount
                    else:
                        # Создаем новый контент только с тестом
                        content_data = {'test': test_data}
                        cursor.execute("""
                            INSERT INTO lesson_contents (
                                course_id, module_number, lesson_index, lesson_title, content_data
                            ) VALUES (%s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            course_id,
                            module_number,
                            lesson_index,
                            lesson_title,
                            json.dumps(content_data, ensure_ascii=False)
                        ))
                        record_id = cursor.fetchone()[0]
                    
                    conn.commit()
                    logger.info(f"✅ Тест для урока {lesson_index} сохранен (ID: {record_id})")
                    return record_id
                    
        except psycopg2.Error as e:
            logger.error(f"Ошибка сохранения теста: {e}")
            raise
    
    def get_lesson_test(
        self,
        course_id: int,
        module_number: int,
        lesson_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Получить тест для урока
        
        Args:
            course_id: ID курса
            module_number: Номер модуля
            lesson_index: Индекс урока
            
        Returns:
            Данные теста или None
        """
        content_data = self.get_lesson_content(course_id, module_number, lesson_index)
        if content_data and 'test' in content_data:
            return content_data['test']
        return None
    
    def get_lesson_video_info(
        self,
        course_id: int,
        module_number: int,
        lesson_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о видео для урока
        
        Args:
            course_id: ID курса
            module_number: Номер модуля
            lesson_index: Индекс урока
            
        Returns:
            Словарь с информацией о видео или None
        """
        try:
            logger.debug(f"Запрос видео информации для курса {course_id}, модуль {module_number}, урок {lesson_index}")
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT video_id, video_download_url, video_status, video_generated_at
                        FROM lesson_contents
                        WHERE course_id = %s AND module_number = %s AND lesson_index = %s
                    """, (course_id, module_number, lesson_index))
                    
                    row = cursor.fetchone()
                    
                    if row:
                        video_id = row.get('video_id')
                        video_download_url = row.get('video_download_url')
                        video_status = row.get('video_status')
                        
                        logger.debug(f"Найдена запись в БД: video_id={video_id}, has_url={bool(video_download_url)}, status={video_status}")
                        
                        if video_id or video_download_url:
                            result = {
                                'video_id': video_id,
                                'video_download_url': video_download_url,
                                'video_status': video_status,
                                'video_generated_at': row.get('video_generated_at').isoformat() if row.get('video_generated_at') else None
                            }
                            logger.debug(f"Возвращаем информацию о видео: {result}")
                            return result
                        else:
                            logger.debug(f"Запись найдена, но video_id и video_download_url пустые")
                    else:
                        logger.debug(f"Запись не найдена в БД для курса {course_id}, модуль {module_number}, урок {lesson_index}")
                    
                    return None
                    
        except psycopg2.Error as e:
            logger.error(f"Ошибка получения информации о видео для курса {course_id}, модуль {module_number}, урок {lesson_index}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def delete_lesson_content(self, course_id: int, module_number: int, lesson_index: int) -> int:
        """Удалить запись детального контента одного урока."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM lesson_contents
                        WHERE course_id = %s AND module_number = %s AND lesson_index = %s
                        """,
                        (course_id, module_number, lesson_index),
                    )
                    conn.commit()
                    return cursor.rowcount
        except psycopg2.Error as e:
            logger.error(f"Ошибка удаления контента урока: {e}")
            raise

    def delete_module_content(self, course_id: int, module_number: int) -> int:
        """Удалить запись детального контента модуля."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM module_contents
                        WHERE course_id = %s AND module_number = %s
                        """,
                        (course_id, module_number),
                    )
                    conn.commit()
                    return cursor.rowcount
        except psycopg2.Error as e:
            logger.error(f"Ошибка удаления контента модуля: {e}")
            raise

    def delete_lesson_contents_for_module(self, course_id: int, module_number: int) -> int:
        """Удалить все записи детального контента уроков для указанного модуля."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM lesson_contents
                        WHERE course_id = %s AND module_number = %s
                        """,
                        (course_id, module_number),
                    )
                    conn.commit()
                    return cursor.rowcount
        except psycopg2.Error as e:
            logger.error(f"Ошибка удаления контента уроков: {e}")
            raise
    
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
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    
                    # Сначала проверяем, существует ли запись
                    cursor.execute("""
                        SELECT id FROM lesson_contents
                        WHERE course_id = %s AND module_number = %s AND lesson_index = %s
                    """, (course_id, module_number, lesson_index))
                    
                    row = cursor.fetchone()
                    
                    if row:
                        # Обновляем существующую запись
                        update_fields = []
                        params = []
                        
                        if video_id is not None:
                            update_fields.append("video_id = %s")
                            params.append(video_id)
                        
                        if video_download_url is not None:
                            update_fields.append("video_download_url = %s")
                            params.append(video_download_url)
                        
                        if video_status is not None:
                            update_fields.append("video_status = %s")
                            params.append(video_status)
                        
                        if video_generated_at is not None:
                            update_fields.append("video_generated_at = %s")
                            params.append(video_generated_at if isinstance(video_generated_at, datetime) else datetime.fromisoformat(video_generated_at) if isinstance(video_generated_at, str) else video_generated_at)
                        
                        if update_fields:
                            params.extend([course_id, module_number, lesson_index])
                            cursor.execute(f"""
                                UPDATE lesson_contents
                                SET {', '.join(update_fields)}
                                WHERE course_id = %s AND module_number = %s AND lesson_index = %s
                            """, params)
                            conn.commit()
                            logger.info(f"Обновлена информация о видео для урока {course_id}/{module_number}/{lesson_index}")
                            return True
                    else:
                        logger.warning(f"Урок {course_id}/{module_number}/{lesson_index} не найден для обновления видео")
                        return False
                        
        except psycopg2.Error as e:
            logger.error(f"Ошибка обновления информации о видео: {e}")
            raise


# Функция для создания экземпляра базы данных
def get_database():
    """
    Получить экземпляр базы данных
    
    Возвращает PostgreSQL базу данных если доступна DATABASE_URL,
    иначе возвращает SQLite базу данных для локальной разработки
    """
    database_url = os.getenv('DATABASE_URL')
    
    if database_url and database_url.startswith('postgresql://'):
        logger.info("Используется PostgreSQL база данных (Render)")
        return RenderDatabase(database_url)
    else:
        logger.info("Используется SQLite база данных (локальная)")
        from .db import CourseDatabase
        return CourseDatabase()


# Глобальный экземпляр базы данных для совместимости с существующим кодом
db = get_database()