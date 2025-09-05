"""Инструменты для административного управления."""

from flask import current_app
from app import db
from app.models import Staff, SystemSetting
from typing import Dict, Any, List
import click
import os

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
            
            # Заполнение меню тестовыми данными
            from .menu_seeder import MenuSeeder
            menu_result = MenuSeeder.seed_menu()
            current_app.logger.info(f"Заполнение меню: {menu_result['message']}")
            
            # Заполнение бонусных карт
            from .bonus_card_seeder import BonusCardSeeder
            bonus_result = BonusCardSeeder.seed_bonus_cards()
            current_app.logger.info(f"Заполнение бонусных карт: {bonus_result['message']}")
            
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
            from sqlalchemy import text
            db.session.execute(text('SELECT 1')).scalar()
            db_status = "connected"
            db_type = "PostgreSQL"
        except Exception:
            db_status = "disconnected"
            db_type = "Unknown"
        
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
                "type": db_type,
                "users_count": user_count,
                "active_users_count": active_user_count,
            },
            "environment": current_app.config.get('ENV', 'unknown'),
            "debug": current_app.debug
        }
    
    @staticmethod
    def get_disk_space() -> str:
        """Получение информации о месте на диске."""
        try:
            import shutil
            import os
            
            # Получаем путь к корневой папке проекта
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            # Получаем информацию о диске
            total, used, free = shutil.disk_usage(project_root)
            
            # Конвертируем в ГБ
            free_gb = free // (1024**3)
            total_gb = total // (1024**3)
            
            return f"{free_gb} ГБ из {total_gb} ГБ"
        except Exception as e:
            current_app.logger.error(f"Error getting disk space: {e}")
            return "—"
    
    @staticmethod
    def get_uptime() -> str:
        """Получение времени работы сервера."""
        try:
            import time
            from datetime import datetime, timedelta
            
            # Время старта из переменной окружения или файла
            start_time_file = os.path.join(os.path.dirname(__file__), '..', '..', '.start_time')
            
            if os.path.exists(start_time_file):
                with open(start_time_file, 'r') as f:
                    start_time = float(f.read().strip())
            else:
                # Если файла нет, используем текущее время (приложение только запустилось)
                start_time = time.time()
                with open(start_time_file, 'w') as f:
                    f.write(str(start_time))
            
            # Вычисляем время работы
            uptime_seconds = time.time() - start_time
            uptime_delta = timedelta(seconds=int(uptime_seconds))
            
            # Форматируем время
            days = uptime_delta.days
            hours, remainder = divmod(uptime_delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}д {hours}ч {minutes}м"
            elif hours > 0:
                return f"{hours}ч {minutes}м"
            else:
                return f"{minutes}м"
                
        except Exception as e:
            current_app.logger.error(f"Error getting uptime: {e}")
            return "—"

# CLI команды
@click.group()
def cli():
    """Команды управления базой данных DENIZ Restaurant."""
    pass

@cli.command()
def init_db():
    """Инициализация базы данных."""
    result = DatabaseManager.init_database()
    click.echo(f"Статус: {result['status']}")
    click.echo(f"Сообщение: {result['message']}")

@cli.command()
def seed_db():
    """Заполнение базы данных тестовыми данными."""
    result = DatabaseManager.seed_database()
    click.echo(f"Статус: {result['status']}")
    click.echo(f"Сообщение: {result['message']}")

@cli.command()
def reset_db():
    """Пересоздание базы данных."""
    if click.confirm('Вы уверены, что хотите пересоздать базу данных?'):
        db.drop_all()
        click.echo("Все таблицы удалены")
        
        result = DatabaseManager.init_database()
        click.echo(f"Инициализация: {result['message']}")
        
        seed_result = DatabaseManager.seed_database()
        click.echo(f"Заполнение: {seed_result['message']}")

@cli.command()
@click.argument('username')
@click.argument('password')
@click.option('--email', help='Email администратора')
def create_admin(username, password, email):
    """Создание администратора."""
    result = DatabaseManager.create_admin_user(username, password, email)
    click.echo(f"Статус: {result['status']}")
    click.echo(f"Сообщение: {result['message']}")

@cli.command()
def status():
    """Статус системы."""
    info = SystemInfo.get_system_status()
    click.echo("=== Статус системы DENIZ Restaurant ===")
    click.echo(f"База данных: {info['database']['status']}")
    click.echo(f"Пользователей: {info['database']['users_count']}")
    click.echo(f"Активных пользователей: {info['database']['active_users_count']}")
    click.echo(f"Окружение: {info['environment']}")
    click.echo(f"Debug режим: {info['debug']}")

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        cli() 