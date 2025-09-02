#!/usr/bin/env python3
"""Скрипт для заполнения справочника статусов заказов."""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в PATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app import create_app, db
from app.models.c_order_status import C_OrderStatus

def seed_order_statuses():
    """Заполнение справочника статусов заказов."""
    app = create_app()
    
    with app.app_context():
        try:
            # Проверяем, есть ли уже статусы
            if C_OrderStatus.query.count() > 0:
                print("✅ Справочник статусов уже заполнен")
                return
            
            # Создаем статусы
            statuses = [
                {
                    'name': 'Новый заказ',
                    'code': 'pending',
                    'description': 'Заказ создан, ожидает подтверждения',
                    'color': '#28a745',
                    'icon': '🟢',
                    'sort_order': 1,
                    'can_transition_to': '["confirmed", "cancelled"]'
                },
                {
                    'name': 'Подтвержден',
                    'code': 'confirmed',
                    'description': 'Заказ подтвержден, отправлен на печать',
                    'color': '#ffc107',
                    'icon': '✅',
                    'sort_order': 2,
                    'can_transition_to': '["completed", "cancelled"]'
                },
                {
                    'name': 'Завершен',
                    'code': 'completed',
                    'description': 'Заказ оплачен и завершен',
                    'color': '#6c757d',
                    'icon': '⚫',
                    'sort_order': 3,
                    'can_transition_to': '[]'
                },
                {
                    'name': 'Отменен',
                    'code': 'cancelled',
                    'description': 'Заказ отменен',
                    'color': '#dc3545',
                    'icon': '❌',
                    'sort_order': 4,
                    'can_transition_to': '[]'
                }
            ]
            
            for status_data in statuses:
                status = C_OrderStatus(**status_data)
                db.session.add(status)
            
            db.session.commit()
            print(f"✅ Добавлено {len(statuses)} статусов заказов")
            
            # Выводим созданные статусы
            for status in C_OrderStatus.query.order_by(C_OrderStatus.sort_order).all():
                print(f"  📋 {status.name} ({status.code}) - {status.icon} {status.color}")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка при заполнении справочника: {e}")
            raise

if __name__ == '__main__':
    seed_order_statuses()
