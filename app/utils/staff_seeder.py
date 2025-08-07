"""
Утилита для создания тестовых пользователей персонала.

Создает администратора и официантов для тестирования авторизации.
"""

import sys
import os
from typing import Dict, Any
import logging

# Добавляем путь к корневой директории проекта
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models import Staff

logger = logging.getLogger(__name__)


class StaffSeeder:
    """Класс для создания тестовых пользователей."""
    
    @staticmethod
    def seed_staff() -> Dict[str, Any]:
        """
        Создание тестовых пользователей персонала.
        
        Returns:
            Dict[str, Any]: Результат операции
        """
        try:
            # Проверяем, есть ли уже пользователи
            existing_count = Staff.query.count()
            if existing_count > 0:
                return {
                    "status": "info",
                    "message": f"Пользователи уже существуют ({existing_count} записей)"
                }
            
            logger.info("Начинаем создание тестовых пользователей...")
            
            # Список пользователей для создания
            staff_data = [
                {
                    "name": "Администратор",
                    "role": "admin", 
                    "login": "admin",
                    "password": "admin123"
                },
                {
                    "name": "Официант 1",
                    "role": "waiter",
                    "login": "waiter1", 
                    "password": "deniz2025"
                },
                {
                    "name": "Официант 2", 
                    "role": "waiter",
                    "login": "waiter2",
                    "password": "deniz2025"
                },
                {
                    "name": "Официант 3",
                    "role": "waiter", 
                    "login": "waiter3",
                    "password": "deniz2025"
                },
                {
                    "name": "Кухня",
                    "role": "kitchen",
                    "login": "kitchen",
                    "password": "deniz2025"
                },
                {
                    "name": "Бар",
                    "role": "bar",
                    "login": "bar", 
                    "password": "deniz2025"
                }
            ]
            
            created_users = []
            
            for user_data in staff_data:
                # Проверяем, не существует ли уже пользователь
                existing_user = Staff.query.filter_by(login=user_data["login"]).first()
                if existing_user:
                    logger.info(f"Пользователь {user_data['login']} уже существует, пропускаем")
                    continue
                
                # Создаем нового пользователя
                user = Staff(
                    name=user_data["name"],
                    role=user_data["role"],
                    login=user_data["login"],
                    is_active=True
                )
                user.set_password(user_data["password"])
                
                db.session.add(user)
                created_users.append(user_data["login"])
                logger.info(f"Создан пользователь: {user_data['login']} ({user_data['role']})")
            
            # Сохраняем изменения
            db.session.commit()
            
            logger.info(f"Создание пользователей завершено. Создано: {len(created_users)}")
            
            return {
                "status": "success", 
                "message": f"Успешно создано {len(created_users)} пользователей: {', '.join(created_users)}",
                "created_count": len(created_users),
                "created_users": created_users
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка создания пользователей: {str(e)}")
            return {
                "status": "error",
                "message": f"Ошибка создания пользователей: {str(e)}"
            }
    
    @staticmethod
    def get_test_credentials() -> Dict[str, Any]:
        """
        Получить тестовые учетные данные.
        
        Returns:
            Dict[str, Any]: Тестовые учетные данные
        """
        return {
            "admin": {"login": "admin", "password": "admin123", "role": "admin"},
            "waiters": [
                {"login": "waiter1", "password": "deniz2025", "role": "waiter"},
                {"login": "waiter2", "password": "deniz2025", "role": "waiter"},
                {"login": "waiter3", "password": "deniz2025", "role": "waiter"}
            ],
            "kitchen": {"login": "kitchen", "password": "deniz2025", "role": "kitchen"},
            "bar": {"login": "bar", "password": "deniz2025", "role": "bar"}
        }


def main():
    """Основная функция для запуска создания пользователей."""
    app = create_app()
    
    with app.app_context():
        result = StaffSeeder.seed_staff()
        print(f"\n{result['status'].upper()}: {result['message']}")
        
        if result['status'] == 'success':
            print("\n📋 Тестовые учетные данные:")
            credentials = StaffSeeder.get_test_credentials()
            
            print(f"👑 Администратор: {credentials['admin']['login']} / {credentials['admin']['password']}")
            print("👨‍💼 Официанты:")
            for waiter in credentials['waiters']:
                print(f"   - {waiter['login']} / {waiter['password']}")
            print(f"👨‍🍳 Кухня: {credentials['kitchen']['login']} / {credentials['kitchen']['password']}")
            print(f"🍸 Бар: {credentials['bar']['login']} / {credentials['bar']['password']}")


if __name__ == "__main__":
    main()