#!/usr/bin/env python3
"""
Скрипт управления DENIZ Restaurant.

Использование:
    python manage.py init-db      # Инициализация БД
    python manage.py seed-db      # Заполнение тестовыми данными
    python manage.py reset-db     # Пересоздание БД
    python manage.py status       # Статус системы
    python manage.py create-admin username password  # Создание администратора
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в PATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from app import create_app
from app.utils.admin_tools import cli

def main():
    """Главная функция."""
    app = create_app()
    with app.app_context():
        cli()

if __name__ == '__main__':
    main() 