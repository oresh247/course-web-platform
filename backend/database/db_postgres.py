"""
База данных PostgreSQL для хранения курсов (через SQLAlchemy)
"""
import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

Base = declarative_base()


class CourseModel(Base):
    """Модель курса"""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_title = Column(String(500), nullable=False)
    target_audience = Column(String(100), nullable=False)
    duration_hours = Column(Integer)
    duration_weeks = Column(Integer)
    course_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModuleContentModel(Base):
    """Модель детального контента модуля"""
    __tablename__ = "module_contents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    module_number = Column(Integer, nullable=False)
    content_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class LessonContentModel(Base):
    """Модель детального контента урока"""
    __tablename__ = "lesson_contents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    module_number = Column(Integer, nullable=False)
    lesson_index = Column(Integer, nullable=False)
    content_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CourseDatabase:
    """Класс для работы с PostgreSQL базой данных"""
    
    def __init__(self, database_url: str = None):
        """
        Инициализация базы данных
        
        Args:
            database_url: URL подключения к PostgreSQL (или SQLite для локальной разработки)
        """
        if database_url is None:
            # Для локальной разработки используем SQLite
            database_url = os.getenv("DATABASE_URL", "sqlite:///courses.db")
        
        # Render использует postgres://, но SQLAlchemy требует postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Создаем таблицы
        Base.metadata.create_all(self.engine)
        logger.info("✅ База данных инициализирована")
    
    def _get_session(self) -> Session:
        """Получить сессию базы данных"""
        return self.SessionLocal()
    
    def save_course(self, course_data: Dict[str, Any]) -> int:
        """
        Сохранить курс в базу данных
        
        Args:
            course_data: Словарь с данными курса
            
        Returns:
            ID сохраненного курса
        """
        session = self._get_session()
        try:
            course = CourseModel(
                course_title=course_data.get("course_title", ""),
                target_audience=course_data.get("target_audience", ""),
                duration_hours=course_data.get("duration_hours"),
                duration_weeks=course_data.get("duration_weeks"),
                course_data=json.dumps(course_data, ensure_ascii=False)
            )
            session.add(course)
            session.commit()
            course_id = course.id
            logger.info(f"✅ Курс сохранен с ID: {course_id}")
            return course_id
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Ошибка сохранения курса: {e}")
            raise
        finally:
            session.close()
    
    def get_course(self, course_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить курс по ID
        
        Args:
            course_id: ID курса
            
        Returns:
            Словарь с данными курса или None
        """
        session = self._get_session()
        try:
            course = session.query(CourseModel).filter(CourseModel.id == course_id).first()
            if course:
                data = json.loads(course.course_data)
                # Убедимся что course_id всегда есть и правильный
                data["course_id"] = course.id
                data["id"] = course.id  # Добавим и id для совместимости
                return data
            return None
        finally:
            session.close()
    
    def get_all_courses(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Получить список всех курсов
        
        Args:
            limit: Максимальное количество курсов
            offset: Смещение для пагинации
            
        Returns:
            Список курсов
        """
        session = self._get_session()
        try:
            courses = session.query(CourseModel).order_by(
                CourseModel.created_at.desc()
            ).limit(limit).offset(offset).all()
            
            result = []
            for course in courses:
                data = json.loads(course.course_data)
                # Убедимся что course_id всегда есть и правильный
                data["course_id"] = course.id
                data["id"] = course.id  # Добавим и id для совместимости
                result.append(data)
            return result
        finally:
            session.close()
    
    def update_course(self, course_id: int, course_data: Dict[str, Any]) -> bool:
        """
        Обновить данные курса
        
        Args:
            course_id: ID курса
            course_data: Новые данные курса
            
        Returns:
            True если обновление успешно, False если курс не найден
        """
        session = self._get_session()
        try:
            course = session.query(CourseModel).filter(CourseModel.id == course_id).first()
            if course:
                course.course_title = course_data.get("course_title", course.course_title)
                course.target_audience = course_data.get("target_audience", course.target_audience)
                course.duration_hours = course_data.get("duration_hours", course.duration_hours)
                course.duration_weeks = course_data.get("duration_weeks", course.duration_weeks)
                course.course_data = json.dumps(course_data, ensure_ascii=False)
                course.updated_at = datetime.utcnow()
                session.commit()
                logger.info(f"✅ Курс {course_id} обновлен")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Ошибка обновления курса: {e}")
            raise
        finally:
            session.close()
    
    def delete_course(self, course_id: int) -> bool:
        """
        Удалить курс
        
        Args:
            course_id: ID курса
            
        Returns:
            True если удаление успешно, False если курс не найден
        """
        session = self._get_session()
        try:
            course = session.query(CourseModel).filter(CourseModel.id == course_id).first()
            if course:
                # Удаляем связанный контент
                session.query(ModuleContentModel).filter(
                    ModuleContentModel.course_id == course_id
                ).delete()
                session.query(LessonContentModel).filter(
                    LessonContentModel.course_id == course_id
                ).delete()
                # Удаляем курс
                session.delete(course)
                session.commit()
                logger.info(f"✅ Курс {course_id} удален")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Ошибка удаления курса: {e}")
            raise
        finally:
            session.close()
    
    def save_module_content(self, course_id: int, module_number: int, module_title: str, content_data: Dict[str, Any]) -> bool:
        """Сохранить детальный контент модуля
        
        Args:
            course_id: ID курса
            module_number: Номер модуля
            module_title: Название модуля
            content_data: Данные контента модуля
        """
        session = self._get_session()
        try:
            # Удаляем старый контент если есть
            session.query(ModuleContentModel).filter(
                ModuleContentModel.course_id == course_id,
                ModuleContentModel.module_number == module_number
            ).delete()
            
            # Добавляем новый
            module_content = ModuleContentModel(
                course_id=course_id,
                module_number=module_number,
                content_data=json.dumps(content_data, ensure_ascii=False)
            )
            session.add(module_content)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Ошибка сохранения контента модуля: {e}")
            raise
        finally:
            session.close()
    
    def get_module_content(self, course_id: int, module_number: int) -> Optional[Dict[str, Any]]:
        """Получить детальный контент модуля"""
        session = self._get_session()
        try:
            content = session.query(ModuleContentModel).filter(
                ModuleContentModel.course_id == course_id,
                ModuleContentModel.module_number == module_number
            ).first()
            
            if content:
                return json.loads(content.content_data)
            return None
        finally:
            session.close()
    
    def save_lesson_content(self, course_id: int, module_number: int, lesson_index: int, content: Dict[str, Any]) -> bool:
        """Сохранить детальный контент урока"""
        session = self._get_session()
        try:
            # Удаляем старый контент если есть
            session.query(LessonContentModel).filter(
                LessonContentModel.course_id == course_id,
                LessonContentModel.module_number == module_number,
                LessonContentModel.lesson_index == lesson_index
            ).delete()
            
            # Добавляем новый
            lesson_content = LessonContentModel(
                course_id=course_id,
                module_number=module_number,
                lesson_index=lesson_index,
                content_data=json.dumps(content, ensure_ascii=False)
            )
            session.add(lesson_content)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Ошибка сохранения контента урока: {e}")
            raise
        finally:
            session.close()
    
    def get_lesson_content(self, course_id: int, module_number: int, lesson_index: int) -> Optional[Dict[str, Any]]:
        """Получить детальный контент урока"""
        session = self._get_session()
        try:
            content = session.query(LessonContentModel).filter(
                LessonContentModel.course_id == course_id,
                LessonContentModel.module_number == module_number,
                LessonContentModel.lesson_index == lesson_index
            ).first()
            
            if content:
                return json.loads(content.content_data)
            return None
        finally:
            session.close()


# Глобальный экземпляр базы данных
db = CourseDatabase(os.getenv("DATABASE_URL"))

