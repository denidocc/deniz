"""
Утилита для создания тестовых данных.

Создает полный набор тестовых данных:
- Столы
- Смены официантов
- Заказы
- Вызовы официанта
- Назначения столов
"""

import sys
import os
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
import random

# Добавляем путь к корневой директории проекта
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models import (
    Staff, Table, StaffShift, Order, OrderItem, 
    WaiterCall, TableAssignment, MenuItem, MenuCategory
)

logger = logging.getLogger(__name__)


class TestDataSeeder:
    """Класс для создания тестовых данных."""
    
    @staticmethod
    def seed_all_data() -> Dict[str, Any]:
        """
        Создание всех тестовых данных.
        
        Returns:
            Dict[str, Any]: Результат операции
        """
        try:
            logger.info("Начинаем создание тестовых данных...")
            
            results = {
                'tables': TestDataSeeder.seed_tables(),
                'shifts': TestDataSeeder.seed_shifts(),
                'orders': TestDataSeeder.seed_orders(),
                'calls': TestDataSeeder.seed_waiter_calls(),
                'assignments': TestDataSeeder.seed_table_assignments()
            }
            
            logger.info("Создание тестовых данных завершено")
            
            # Подсчитываем общее количество созданных записей
            total_created = sum(r.get('created_count', 0) for r in results.values())
            
            return {
                "status": "success",
                "message": f"Создано {total_created} тестовых записей",
                "details": results
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка создания тестовых данных: {str(e)}")
            return {
                "status": "error",
                "message": f"Ошибка создания тестовых данных: {str(e)}"
            }
    
    @staticmethod
    def seed_tables() -> Dict[str, Any]:
        """Создание тестовых столов."""
        try:
            # Проверяем, есть ли уже столы
            existing_count = Table.query.count()
            if existing_count > 0:
                return {
                    "status": "info",
                    "message": f"Столы уже существуют ({existing_count} записей)",
                    "created_count": 0
                }
            
            logger.info("Создаем тестовые столы...")
            
            # Получаем официантов для назначения
            waiters = Staff.query.filter_by(role='waiter', is_active=True).all()
            
            # Данные для столов (используем доступные статусы: available, occupied, reserved)
            tables_data = [
                {"table_number": 1, "capacity": 2, "status": "available"},
                {"table_number": 2, "capacity": 4, "status": "occupied"},
                {"table_number": 3, "capacity": 4, "status": "available"},
                {"table_number": 4, "capacity": 6, "status": "reserved"},
                {"table_number": 5, "capacity": 2, "status": "occupied"},
                {"table_number": 6, "capacity": 4, "status": "available"},
                {"table_number": 7, "capacity": 4, "status": "available"},
                {"table_number": 8, "capacity": 2, "status": "available"},
                {"table_number": 9, "capacity": 4, "status": "available"},
                {"table_number": 10, "capacity": 6, "status": "occupied"},
                {"table_number": 11, "capacity": 2, "status": "available"},
                {"table_number": 12, "capacity": 4, "status": "reserved"},
                {"table_number": 13, "capacity": 8, "status": "available"},
                {"table_number": 14, "capacity": 6, "status": "available"},
                {"table_number": 15, "capacity": 8, "status": "occupied"},
                {"table_number": 16, "capacity": 4, "status": "available"},
                {"table_number": 17, "capacity": 10, "status": "reserved"},
                {"table_number": 18, "capacity": 6, "status": "available"}
            ]
            
            created_tables = []
            
            for table_data in tables_data:
                table = Table(
                    table_number=table_data["table_number"],
                    capacity=table_data["capacity"],
                    status=table_data["status"]
                )
                
                db.session.add(table)
                created_tables.append(table_data["table_number"])
                logger.info(f"Создан стол {table_data['table_number']} ({table_data['status']})")
            
            db.session.commit()
            
            logger.info(f"Создание столов завершено. Создано: {len(created_tables)}")
            
            return {
                "status": "success",
                "message": f"Создано {len(created_tables)} столов",
                "created_count": len(created_tables),
                "created_items": created_tables
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка создания столов: {str(e)}")
            return {
                "status": "error",
                "message": f"Ошибка создания столов: {str(e)}",
                "created_count": 0
            }
    
    @staticmethod
    def seed_shifts() -> Dict[str, Any]:
        """Создание тестовых смен."""
        try:
            # Проверяем, есть ли уже смены
            existing_count = StaffShift.query.count()
            if existing_count > 0:
                return {
                    "status": "info",
                    "message": f"Смены уже существуют ({existing_count} записей)",
                    "created_count": 0
                }
            
            logger.info("Создаем тестовые смены...")
            
            # Получаем официантов
            waiters = Staff.query.filter_by(role='waiter').all()
            if not waiters:
                return {
                    "status": "error",
                    "message": "Не найдены официанты для создания смен",
                    "created_count": 0
                }
            
            created_shifts = []
            now = datetime.utcnow()
            
            # Создаем смены за последние 7 дней
            for day_offset in range(7):
                shift_date = now - timedelta(days=day_offset)
                
                for waiter in waiters:
                    # Не все официанты работают каждый день
                    if random.random() > 0.7:  # 70% вероятность работы
                        continue
                    
                    # Случайное время начала смены (8:00 - 10:00)
                    start_hour = random.randint(8, 10)
                    start_time = shift_date.replace(
                        hour=start_hour, 
                        minute=random.randint(0, 59),
                        second=0,
                        microsecond=0
                    )
                    
                    # Продолжительность смены 6-10 часов
                    shift_duration = random.randint(6, 10)
                    end_time = start_time + timedelta(hours=shift_duration)
                    
                    # Для текущего дня - возможна активная смена
                    is_active = (day_offset == 0 and random.random() > 0.5)
                    
                    shift = StaffShift(
                        staff_id=waiter.id,
                        shift_date=start_time.date(),
                        shift_start=start_time,
                        shift_end=None if is_active else end_time,
                        is_active=is_active,
                        total_orders=random.randint(5, 25) if not is_active else random.randint(0, 15),
                        total_revenue=random.uniform(500, 3000) if not is_active else random.uniform(0, 1500)
                    )
                    
                    db.session.add(shift)
                    created_shifts.append({
                        'waiter': waiter.name,
                        'date': start_time.date(),
                        'active': is_active
                    })
                    
                    logger.info(f"Создана смена для {waiter.name} на {start_time.date()}")
            
            db.session.commit()
            
            logger.info(f"Создание смен завершено. Создано: {len(created_shifts)}")
            
            return {
                "status": "success",
                "message": f"Создано {len(created_shifts)} смен",
                "created_count": len(created_shifts),
                "created_items": created_shifts
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка создания смен: {str(e)}")
            return {
                "status": "error",
                "message": f"Ошибка создания смен: {str(e)}",
                "created_count": 0
            }
    
    @staticmethod
    def seed_orders() -> Dict[str, Any]:
        """Создание тестовых заказов."""
        try:
            # Проверяем, есть ли уже заказы
            existing_count = Order.query.count()
            if existing_count > 0:
                return {
                    "status": "info",
                    "message": f"Заказы уже существуют ({existing_count} записей)",
                    "created_count": 0
                }
            
            logger.info("Создаем тестовые заказы...")
            
            # Получаем данные для заказов
            tables = Table.query.all()
            menu_items = MenuItem.query.all()
            waiters = Staff.query.filter_by(role='waiter', is_active=True).all()
            
            if not tables or not menu_items or not waiters:
                return {
                    "status": "error",
                    "message": "Не найдены столы, блюда меню или официанты для создания заказов",
                    "created_count": 0
                }
            
            created_orders = []
            statuses = ['новый', 'принят', 'готовится', 'готов', 'доставлен']
            
            # Создаем 20-30 заказов
            for i in range(random.randint(20, 30)):
                table = random.choice(tables)
                
                # Используем официанта, назначенного столу через TableAssignment, или случайного
                waiter = table.get_assigned_waiter()
                
                # Если у стола нет назначенного официанта, выбираем случайного (80% вероятность)
                if not waiter and random.random() < 0.8:
                    waiter = random.choice(waiters)
                
                order = Order(
                    table_id=table.id,
                    waiter_id=waiter.id if waiter else None,
                    status=random.choice(statuses),
                    subtotal=0,  # Будет пересчитано после добавления позиций
                    service_charge=0,
                    total_amount=0,  # Будет пересчитано после добавления позиций
                    guest_count=random.randint(1, table.capacity),
                    created_at=datetime.utcnow() - timedelta(
                        hours=random.randint(0, 12),
                        minutes=random.randint(0, 59)
                    )
                )
                
                db.session.add(order)
                db.session.flush()  # Получаем ID заказа
                
                # Добавляем позиции в заказ
                total_amount = 0
                num_items = random.randint(2, 6)
                
                for _ in range(num_items):
                    menu_item = random.choice(menu_items)
                    quantity = random.randint(1, 3)
                    price = menu_item.price  # Используем цену блюда
                    
                    order_item = OrderItem(
                        order_id=order.id,
                        menu_item_id=menu_item.id,
                        quantity=quantity,
                        unit_price=price,
                        total_price=price * quantity,
                        preparation_type='normal'  # Тип приготовления
                    )
                    
                    db.session.add(order_item)
                    total_amount += order_item.total_price
                
                # Обновляем общую сумму заказа
                from decimal import Decimal
                order.subtotal = total_amount
                order.service_charge = total_amount * Decimal('0.1')  # 10% сервисный сбор
                order.total_amount = total_amount * Decimal('1.1')
                
                created_orders.append({
                    'id': order.id,
                    'table': table.table_number,
                    'status': order.status,
                    'amount': total_amount
                })
                
                logger.info(f"Создан заказ #{order.id} для стола {table.table_number}")
            
            db.session.commit()
            
            logger.info(f"Создание заказов завершено. Создано: {len(created_orders)}")
            
            return {
                "status": "success",
                "message": f"Создано {len(created_orders)} заказов",
                "created_count": len(created_orders),
                "created_items": created_orders
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка создания заказов: {str(e)}")
            return {
                "status": "error",
                "message": f"Ошибка создания заказов: {str(e)}",
                "created_count": 0
            }
    
    @staticmethod
    def seed_waiter_calls() -> Dict[str, Any]:
        """Создание тестовых вызовов официанта."""
        try:
            # Проверяем, есть ли уже вызовы
            existing_count = WaiterCall.query.count()
            if existing_count > 0:
                return {
                    "status": "info",
                    "message": f"Вызовы уже существуют ({existing_count} записей)",
                    "created_count": 0
                }
            
            logger.info("Создаем тестовые вызовы официанта...")
            
            # Получаем столы
            tables = Table.query.all()
            if not tables:
                return {
                    "status": "error",
                    "message": "Не найдены столы для создания вызовов",
                    "created_count": 0
                }
            
            created_calls = []
            statuses = ['pending', 'responded']
            
            # Создаем 10-15 вызовов
            for i in range(random.randint(10, 15)):
                table = random.choice(tables)
                
                call = WaiterCall(
                    table_id=table.id,
                    status=random.choice(statuses),
                    created_at=datetime.utcnow() - timedelta(
                        minutes=random.randint(1, 180)  # От 1 минуты до 3 часов назад
                    )
                )
                
                # Для отвеченных вызовов добавляем время ответа
                if call.status == 'responded':
                    call.responded_at = call.created_at + timedelta(
                        minutes=random.randint(2, 30)
                    )
                
                db.session.add(call)
                created_calls.append({
                    'table': table.table_number,
                    'status': call.status
                })
                
                logger.info(f"Создан вызов для стола {table.table_number} ({call.status})")
            
            db.session.commit()
            
            logger.info(f"Создание вызовов завершено. Создано: {len(created_calls)}")
            
            return {
                "status": "success",
                "message": f"Создано {len(created_calls)} вызовов",
                "created_count": len(created_calls),
                "created_items": created_calls
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка создания вызовов: {str(e)}")
            return {
                "status": "error",
                "message": f"Ошибка создания вызовов: {str(e)}",
                "created_count": 0
            }
    
    @staticmethod
    def seed_table_assignments() -> Dict[str, Any]:
        """Создание назначений столов официантам."""
        try:
            # Проверяем, есть ли уже назначения
            existing_count = TableAssignment.query.count()
            if existing_count > 0:
                return {
                    "status": "info",
                    "message": f"Назначения уже существуют ({existing_count} записей)",
                    "created_count": 0
                }
            
            logger.info("Создаем назначения столов...")
            
            # Получаем активные смены и столы
            active_shifts = StaffShift.query.filter_by(is_active=True).all()
            tables = Table.query.all()
            
            if not active_shifts or not tables:
                return {
                    "status": "info",
                    "message": "Нет активных смен или столов для назначений",
                    "created_count": 0
                }
            
            created_assignments = []
            
            # Распределяем столы между официантами
            tables_per_waiter = len(tables) // len(active_shifts)
            remaining_tables = len(tables) % len(active_shifts)
            
            table_index = 0
            for i, shift in enumerate(active_shifts):
                # Количество столов для этого официанта
                tables_count = tables_per_waiter
                if i < remaining_tables:
                    tables_count += 1
                
                # Назначаем столы
                for j in range(tables_count):
                    if table_index < len(tables):
                        table = tables[table_index]
                        
                        assignment = TableAssignment(
                            waiter_id=shift.staff_id,
                            table_id=table.id,
                            shift_id=shift.id,
                            assigned_at=shift.shift_start + timedelta(minutes=random.randint(0, 30)),
                            is_active=True
                        )
                        
                        db.session.add(assignment)
                        created_assignments.append({
                            'waiter': shift.staff.name,
                            'table': table.table_number
                        })
                        
                        logger.info(f"Назначен стол {table.table_number} официанту {shift.staff.name}")
                        table_index += 1
            
            db.session.commit()
            
            logger.info(f"Создание назначений завершено. Создано: {len(created_assignments)}")
            
            return {
                "status": "success",
                "message": f"Создано {len(created_assignments)} назначений",
                "created_count": len(created_assignments),
                "created_items": created_assignments
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка создания назначений: {str(e)}")
            return {
                "status": "error",
                "message": f"Ошибка создания назначений: {str(e)}",
                "created_count": 0
            }
    
    @staticmethod
    def clear_all_test_data() -> Dict[str, Any]:
        """Очистка всех тестовых данных."""
        try:
            logger.info("Начинаем очистку тестовых данных...")
            
            # Порядок важен из-за внешних ключей
            OrderItem.query.delete()
            Order.query.delete()
            WaiterCall.query.delete()
            TableAssignment.query.delete()
            StaffShift.query.delete()
            Table.query.delete()
            
            db.session.commit()
            
            logger.info("Очистка тестовых данных завершена")
            
            return {
                "status": "success",
                "message": "Все тестовые данные удалены"
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка очистки данных: {str(e)}")
            return {
                "status": "error",
                "message": f"Ошибка очистки данных: {str(e)}"
            }


def main():
    """Основная функция для запуска создания тестовых данных."""
    app = create_app()
    
    with app.app_context():
        print("\n🎲 Создание тестовых данных для DENIZ Restaurant")
        print("=" * 50)
        
        # Опция очистки данных
        clear_data = input("Очистить существующие данные? (y/N): ").lower().strip()
        if clear_data == 'y':
            print("\n🗑️  Очищаем существующие данные...")
            result = TestDataSeeder.clear_all_test_data()
            print(f"{result['status'].upper()}: {result['message']}")
        
        print("\n📊 Создаем тестовые данные...")
        result = TestDataSeeder.seed_all_data()
        
        print(f"\n{result['status'].upper()}: {result['message']}")
        
        if result['status'] == 'success' and 'details' in result:
            print("\n📋 Детали создания:")
            for category, details in result['details'].items():
                print(f"  {category.capitalize()}: {details['message']}")
        
        print("\n✨ Готово! Тестовые данные созданы.")
        print("\n🔧 Теперь можно тестировать:")
        print("  - Смены официантов")
        print("  - Столы и их статусы") 
        print("  - Заказы с позициями")
        print("  - Вызовы официанта")
        print("  - Назначения столов")


if __name__ == "__main__":
    main()