#!/usr/bin/env python3
"""Тестовый скрипт для проверки системы печати."""

import os
import sys
from datetime import datetime

# Добавляем корневую директорию в PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Order, OrderItem, MenuItem, Table, Staff
from app.utils.print_service import PrintService

def create_test_order():
    """Создание тестового заказа."""
    app = create_app()
    
    with app.app_context():
        # Создаем тестовые данные
        table = Table.query.first()
        if not table:
            table = Table(table_number=1, status='available')
            db.session.add(table)
            db.session.flush()
        
        waiter = Staff.query.filter_by(role='waiter').first()
        if not waiter:
            waiter = Staff(name='Тестовый официант', role='waiter', login='test_waiter')
            waiter.set_password('password')
            db.session.add(waiter)
            db.session.flush()
        
        # Создаем заказ
        order = Order(
            table_id=table.id,
            waiter_id=waiter.id,
            guest_count=4,
            status='новый',
            subtotal=1350.00,
            service_charge=135.00,
            total_amount=1485.00,
            language='ru'
        )
        db.session.add(order)
        db.session.flush()
        
        # Создаем позиции заказа
        kitchen_items = [
            {'name': 'Борщ классический', 'price': 300.00, 'preparation_type': 'kitchen'},
            {'name': 'Стейк из говядины', 'price': 850.00, 'preparation_type': 'kitchen'}
        ]
        
        bar_items = [
            {'name': 'Кола 0.5л', 'price': 100.00, 'preparation_type': 'bar'},
            {'name': 'Кофе эспрессо', 'price': 100.00, 'preparation_type': 'bar'}
        ]
        
        all_items = kitchen_items + bar_items
        
        # Создаем категории если их нет
        from app.models import MenuCategory
        
        kitchen_category = MenuCategory.query.filter_by(name_ru='Горячие блюда').first()
        if not kitchen_category:
            kitchen_category = MenuCategory(
                name_ru='Горячие блюда',
                name_en='Hot Dishes',
                sort_order=1,
                is_active=True
            )
            db.session.add(kitchen_category)
            db.session.flush()
        
        bar_category = MenuCategory.query.filter_by(name_ru='Напитки').first()
        if not bar_category:
            bar_category = MenuCategory(
                name_ru='Напитки',
                name_en='Beverages',
                sort_order=2,
                is_active=True
            )
            db.session.add(bar_category)
            db.session.flush()
        
        for i, item_data in enumerate(all_items):
            # Создаем или находим блюдо
            menu_item = MenuItem.query.filter_by(name_ru=item_data['name']).first()
            if not menu_item:
                category_id = kitchen_category.id if item_data['preparation_type'] == 'kitchen' else bar_category.id
                menu_item = MenuItem(
                    category_id=category_id,
                    name_ru=item_data['name'],
                    price=item_data['price'],
                    preparation_type=item_data['preparation_type'],
                    is_active=True
                )
                db.session.add(menu_item)
                db.session.flush()
            
            # Создаем позицию заказа
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=menu_item.id,
                quantity=2 if i < 2 else 1,  # 2x для первых двух блюд
                unit_price=item_data['price'],
                total_price=item_data['price'] * (2 if i < 2 else 1),
                preparation_type=item_data['preparation_type'],
                comments='Без сметаны' if i == 0 else 'Средней прожарки' if i == 1 else None
            )
            db.session.add(order_item)
        
        db.session.commit()
        print(f"✅ Тестовый заказ создан: #{order.id}")
        return order

def test_print_service():
    """Тестирование сервиса печати."""
    app = create_app()
    
    with app.app_context():
        # Создаем тестовый заказ
        order = create_test_order()
        
        # Тестируем сервис печати
        print_service = PrintService()
        
        print("\n🍽️ Тестирование печати кухонного чека:")
        kitchen_items = [item for item in order.items if item.menu_item.preparation_type == 'kitchen']
        kitchen_success = print_service.print_kitchen_receipt(order, kitchen_items)
        print(f"Результат: {'✅ Успешно' if kitchen_success else '❌ Ошибка'}")
        
        print("\n🍹 Тестирование печати барного чека:")
        bar_items = [item for item in order.items if item.menu_item.preparation_type == 'bar']
        bar_success = print_service.print_bar_receipt(order, bar_items)
        print(f"Результат: {'✅ Успешно' if bar_success else '❌ Ошибка'}")
        
        print("\n🧾 Тестирование печати финального чека:")
        final_success = print_service.print_final_receipt(order)
        print(f"Результат: {'✅ Успешно' if final_success else '❌ Ошибка'}")
        
        print(f"\n📁 Чеки сохранены в директории: {os.path.join(os.getcwd(), 'receipts')}")

if __name__ == '__main__':
    print("🧪 Тестирование системы печати чеков")
    print("=" * 50)
    
    try:
        test_print_service()
        print("\n✅ Тестирование завершено успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc() 