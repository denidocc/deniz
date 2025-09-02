#!/usr/bin/env python3
"""Скрипт для очистки базы данных от всех данных, кроме блюд и пользователей."""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию в PATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app import create_app, db
from app.models import (
    Order, OrderItem, Table, TableAssignment, WaiterCall,
    DailyReport, AuditLog, SystemSetting, BonusCard, Banner
)

def clear_database():
    """Очистка базы данных от всех данных, кроме блюд и пользователей."""
    app = create_app()
    
    with app.app_context():
        try:
            print("🗑️  Начинаю очистку базы данных...")
            
            # Подсчет записей перед удалением
            print("\n📊 Текущее количество записей:")
            print(f"  - Заказы: {Order.query.count()}")
            print(f"  - Позиции заказов: {OrderItem.query.count()}")
            print(f"  - Столы: {Table.query.count()}")
            print(f"  - Назначения столов: {TableAssignment.query.count()}")
            print(f"  - Вызовы официанта: {WaiterCall.query.count()}")
            print(f"  - Дневные отчеты: {DailyReport.query.count()}")
            print(f"  - Аудит логи: {AuditLog.query.count()}")
            print(f"  - Системные настройки: {SystemSetting.query.count()}")
            print(f"  - Бонусные карты: {BonusCard.query.count()}")
            print(f"  - Баннеры: {Banner.query.count()}")
            
            # Подтверждение
            confirm = input("\n⚠️  Вы уверены, что хотите удалить ВСЕ эти данные? (yes/no): ")
            if confirm.lower() != 'yes':
                print("❌ Операция отменена.")
                return
            
            print("\n🧹 Удаляю данные...")
            
            # Удаление в правильном порядке (сначала зависимые таблицы)
            
            # 1. Позиции заказов
            print("  - Удаляю позиции заказов...")
            OrderItem.query.delete()
            
            # 2. Заказы
            print("  - Удаляю заказы...")
            Order.query.delete()
            
            # 3. Назначения столов
            print("  - Удаляю назначения столов...")
            TableAssignment.query.delete()
            
            # 4. Вызовы официанта
            print("  - Удаляю вызовы официанта...")
            WaiterCall.query.delete()
            
            # 5. Столы (сброс статусов)
            print("  - Сбрасываю статусы столов...")
            tables = Table.query.all()
            for table in tables:
                table.status = 'available'
            db.session.commit()
            
            # 6. Дневные отчеты
            print("  - Удаляю дневные отчеты...")
            DailyReport.query.delete()
            
            # 7. Аудит логи
            print("  - Удаляю аудит логи...")
            AuditLog.query.delete()
            
            # 8. Системные настройки
            print("  - Удаляю системные настройки...")
            SystemSetting.query.delete()
            
            # 9. Бонусные карты
            print("  - Удаляю бонусные карты...")
            BonusCard.query.delete()
            
            # 10. Баннеры
            print("  - Удаляю баннеры...")
            Banner.query.delete()
            
            # Фиксация изменений
            db.session.commit()
            
            print("\n✅ База данных очищена!")
            
            # Подсчет записей после очистки
            print("\n📊 Количество записей после очистки:")
            print(f"  - Заказы: {Order.query.count()}")
            print(f"  - Позиции заказов: {OrderItem.query.count()}")
            print(f"  - Столы: {Table.query.count()}")
            print(f"  - Назначения столов: {TableAssignment.query.count()}")
            print(f"  - Вызовы официанта: {WaiterCall.query.count()}")
            print(f"  - Дневные отчеты: {DailyReport.query.count()}")
            print(f"  - Аудит логи: {AuditLog.query.count()}")
            print(f"  - Системные настройки: {SystemSetting.query.count()}")
            print(f"  - Бонусные карты: {BonusCard.query.count()}")
            print(f"  - Баннеры: {Banner.query.count()}")
            
            print("\n🎯 Данные сохранены:")
            print("  - Пользователи (staff)")
            print("  - Категории меню (menu_categories)")
            print("  - Блюда (menu_items)")
            print("  - Размеры порций (menu_item_sizes)")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка при очистке базы данных: {e}")
            raise

def main():
    """Главная функция."""
    print("🧹 Скрипт очистки базы данных DENIZ Restaurant")
    print("=" * 50)
    
    try:
        clear_database()
    except KeyboardInterrupt:
        print("\n❌ Операция прервана пользователем.")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
