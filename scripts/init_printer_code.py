#!/usr/bin/env python3
"""Скрипт для добавления настройки printer_code в базу данных."""

import sys
from pathlib import Path

# Добавляем корневую директорию в PATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app import create_app, db
from app.models import SystemSetting

def main():
    """Добавление настройки printer_code."""
    print("🔧 Инициализация настройки printer_code...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Проверяем, существует ли настройка
            existing = SystemSetting.query.filter_by(setting_key='printer_code').first()
            
            if existing:
                print(f"✅ Настройка printer_code уже существует: {existing.setting_value}")
            else:
                # Добавляем настройку
                SystemSetting.set_setting('printer_code', '1234', 'Код доступа к настройкам принтеров')
                print("✅ Настройка printer_code добавлена со значением: 1234")
            
            # Инициализируем все недостающие настройки
            print("🔧 Инициализация всех настроек по умолчанию...")
            SystemSetting.initialize_default_settings()
            print("✅ Все настройки проверены и добавлены при необходимости")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
