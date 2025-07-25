"""Инструменты для административного управления."""

from flask import current_app
from app import db
from app.models import Staff, SystemSetting
from typing import Dict, Any, List

class DatabaseManager:
    """Менеджер для работы с базой данных."""
    
    @staticmethod
    def init_database() -> Dict[str, Any]:
        """Инициализация базы данных."""
        try:
            db.create_all()
            current_app.logger.info("База данных инициализирована")
            return {"status": "success", "message": "База данных инициализирована"}
        except Exception as e:
            current_app.logger.error(f"Ошибка инициализации БД: {e}")
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def seed_database() -> Dict[str, Any]:
        """Заполнение базы данных начальными данными."""
        try:
            # Проверка существования пользователей
            if Staff.query.count() > 0:
                return {"status": "info", "message": "Данные уже существуют"}
            
            # Создание стандартных пользователей
            users = [
                Staff(name='Администратор', login='admin', role='admin'),
                Staff(name='Официант 1', login='waiter1', role='waiter'),
                Staff(name='Официант 2', login='waiter2', role='waiter'),
                Staff(name='Официант 3', login='waiter3', role='waiter'),
                Staff(name='Кухня', login='kitchen', role='kitchen'),
                Staff(name='Бар', login='bar', role='bar'),
            ]
            
            # Установка паролей
            for user in users:
                if user.role == 'waiter':
                    user.set_password('deniz2025')
                elif user.role == 'admin':
                    user.set_password('admin123')
                elif user.role in ['kitchen', 'bar']:
                    user.set_password(f'{user.role}123')
            
            db.session.add_all(users)
            db.session.commit()
            
            # Инициализация системных настроек
            SystemSetting.initialize_default_settings()
            
            current_app.logger.info("Начальные данные добавлены")
            return {"status": "success", "message": "Начальные данные добавлены"}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Ошибка заполнения БД: {e}")
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def create_admin_user(username: str, password: str, email: str = None) -> Dict[str, Any]:
        """Создание администратора."""
        try:
            # Проверка существования пользователя
            if Staff.find_by_login(username):
                return {"status": "error", "message": "Пользователь уже существует"}
            
            # Создание пользователя
            user = Staff(
                name=username,
                login=username,
                role='admin',
                is_active=True
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            current_app.logger.info(f"Администратор {username} создан")
            return {"status": "success", "message": f"Администратор {username} создан"}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Ошибка создания администратора: {e}")
            return {"status": "error", "message": str(e)}

class SystemInfo:
    """Информация о системе."""
    
    @staticmethod
    def get_system_status() -> Dict[str, Any]:
        """Получение статуса системы."""
        try:
            # Проверка подключения к БД
            db.session.execute(db.text('SELECT 1')).scalar()
            db_status = "connected"
        except Exception:
            db_status = "disconnected"
        
        # Подсчет пользователей
        try:
            user_count = Staff.query.count()
            active_user_count = Staff.query.filter_by(is_active=True).count()
        except Exception:
            user_count = 0
            active_user_count = 0
        
        return {
            "database": {
                "status": db_status,
                "users_count": user_count,
                "active_users_count": active_user_count,
            },
            "environment": current_app.config.get('ENV', 'unknown'),
            "debug": current_app.debug
        } 