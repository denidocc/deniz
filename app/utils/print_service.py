"""Сервис печати чеков."""

import os
from datetime import datetime
from typing import List, Dict, Any
from flask import current_app
from app.models import Order, OrderItem, Staff

class PrintService:
    """Сервис для печати чеков."""
    
    def __init__(self):
        self.config = current_app.config
        
    def print_kitchen_receipt(self, order: Order, kitchen_items: List[OrderItem]) -> bool:
        """
        Печать чека на кухню.
        
        Args:
            order: Заказ
            kitchen_items: Позиции для кухни
            
        Returns:
            bool: Успешность печати
        """
        try:
            receipt_content = self._generate_kitchen_receipt(order, kitchen_items)
            return self._send_to_printer(receipt_content, 'kitchen')
        except Exception as e:
            current_app.logger.error(f"Kitchen receipt print error: {e}")
            return False
    
    def print_bar_receipt(self, order: Order, bar_items: List[OrderItem]) -> bool:
        """
        Печать чека в бар.
        
        Args:
            order: Заказ
            bar_items: Позиции для бара
            
        Returns:
            bool: Успешность печати
        """
        try:
            receipt_content = self._generate_bar_receipt(order, bar_items)
            return self._send_to_printer(receipt_content, 'bar')
        except Exception as e:
            current_app.logger.error(f"Bar receipt print error: {e}")
            return False
    
    def print_final_receipt(self, order: Order) -> bool:
        """
        Печать финального чека для клиента.
        
        Args:
            order: Заказ
            
        Returns:
            bool: Успешность печати
        """
        try:
            receipt_content = self._generate_final_receipt(order)
            return self._send_to_printer(receipt_content, 'receipt')
        except Exception as e:
            current_app.logger.error(f"Final receipt print error: {e}")
            return False
    
    def _generate_kitchen_receipt(self, order: Order, kitchen_items: List[OrderItem]) -> str:
        """Генерация содержимого кухонного чека."""
        waiter = Staff.query.get(order.waiter_id)
        
        receipt = []
        receipt.append("=" * 32)
        receipt.append("КУХНЯ - DENIZ")
        receipt.append("=" * 32)
        receipt.append(f"Стол: {order.table.table_number} Время: {order.created_at.strftime('%H:%M')}")
        receipt.append(f"Гостей: {order.guest_count}")
        receipt.append(f"Заказ #{order.id:04d} - КУХНЯ")
        receipt.append("-" * 32)
        
        for item in kitchen_items:
            receipt.append(f"{item.quantity}x {item.menu_item.name_ru}")
            if item.comments:
                receipt.append(f"- {item.comments}")
        
        receipt.append("-" * 32)
        receipt.append(f"Время заказа: {order.created_at.strftime('%H:%M')}")
        receipt.append(f"Официант: {waiter.name if waiter else 'Неизвестно'}")
        receipt.append("=" * 32)
        
        return "\n".join(receipt)
    
    def _generate_bar_receipt(self, order: Order, bar_items: List[OrderItem]) -> str:
        """Генерация содержимого барного чека."""
        waiter = Staff.query.get(order.waiter_id)
        
        receipt = []
        receipt.append("=" * 32)
        receipt.append("БАР - DENIZ")
        receipt.append("=" * 32)
        receipt.append(f"Стол: {order.table.table_number} Время: {order.created_at.strftime('%H:%M')}")
        receipt.append(f"Гостей: {order.guest_count}")
        receipt.append(f"Заказ #{order.id:04d} - БАР")
        receipt.append("-" * 32)
        
        for item in bar_items:
            receipt.append(f"{item.quantity}x {item.menu_item.name_ru}")
            if item.comments:
                receipt.append(f"- {item.comments}")
        
        receipt.append("-" * 32)
        receipt.append(f"Время заказа: {order.created_at.strftime('%H:%M')}")
        receipt.append(f"Официант: {waiter.name if waiter else 'Неизвестно'}")
        receipt.append("=" * 32)
        
        return "\n".join(receipt)
    
    def _generate_final_receipt(self, order: Order) -> str:
        """Генерация финального чека для клиента."""
        waiter = Staff.query.get(order.waiter_id)
        
        receipt = []
        receipt.append("=" * 32)
        receipt.append("РЕСТОРАН DENIZ")
        receipt.append("=" * 32)
        receipt.append(f"Стол: {order.table.table_number} Время: {order.created_at.strftime('%H:%M')}")
        receipt.append(f"Гостей: {order.guest_count}")
        receipt.append(f"Заказ #{order.id:04d}")
        receipt.append("-" * 32)
        
        # Группируем позиции по типам
        kitchen_items = []
        bar_items = []
        
        for item in order.items:
            if item.menu_item.preparation_type == 'kitchen':
                kitchen_items.append(item)
            elif item.menu_item.preparation_type == 'bar':
                bar_items.append(item)
        
        # Печатаем позиции кухни
        if kitchen_items:
            receipt.append("КУХНЯ:")
            for item in kitchen_items:
                receipt.append(f"{item.quantity}x {item.menu_item.name_ru} {item.unit_price:.2f}")
                if item.comments:
                    receipt.append(f"- {item.comments}")
            receipt.append("")
        
        # Печатаем позиции бара
        if bar_items:
            receipt.append("БАР:")
            for item in bar_items:
                receipt.append(f"{item.quantity}x {item.menu_item.name_ru} {item.unit_price:.2f}")
                if item.comments:
                    receipt.append(f"- {item.comments}")
            receipt.append("")
        
        receipt.append("-" * 32)
        receipt.append(f"Подытог: {order.subtotal:.2f}")
        receipt.append(f"Сервисный сбор (10%): {order.service_charge:.2f}")
        receipt.append("-" * 32)
        receipt.append(f"ИТОГО: {order.total_amount:.2f}")
        receipt.append("=" * 32)
        receipt.append(f"Время заказа: {order.created_at.strftime('%H:%M')}")
        receipt.append(f"Официант: {waiter.name if waiter else 'Неизвестно'}")
        receipt.append("=" * 32)
        
        return "\n".join(receipt)
    
    def _send_to_printer(self, content: str, printer_type: str) -> bool:
        """
        Отправка содержимого на принтер.
        
        Args:
            content: Содержимое для печати
            printer_type: Тип принтера (kitchen/bar/receipt)
            
        Returns:
            bool: Успешность печати
        """
        try:
            # В реальной системе здесь будет интеграция с ESC/POS принтерами
            # Пока просто логируем содержимое
            
            current_app.logger.info(f"Printing to {printer_type} printer:")
            current_app.logger.info(content)
            
            # Сохраняем в файл для демонстрации
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"receipt_{printer_type}_{timestamp}.txt"
            filepath = os.path.join(current_app.root_path, '..', 'receipts', filename)
            
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            current_app.logger.info(f"Receipt saved to: {filepath}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Printer error: {e}")
            return False 