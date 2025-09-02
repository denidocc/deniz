"""Сервис печати чеков."""

import os
from datetime import datetime
from typing import List, Dict, Any
from flask import current_app
from app.models import Order, OrderItem, Staff
from escpos.printer import Network, Usb, Serial
class PrintService:
    """Сервис для печати чеков."""
    
    def __init__(self):
        self.config = current_app.config
        
    def _get_printer_config(self, kind: str) -> dict:
        # kind: 'kitchen' | 'bar' | 'receipt'
        from app.models.system_setting import SystemSetting
        cfg = {
            'type': SystemSetting.get_setting(f'printer_{kind}_type', 'disabled'),  # network | usb | serial | disabled
            'code_page': int(SystemSetting.get_setting(f'printer_{kind}_code_page', '37') or 37),
            'chars_per_line': int(SystemSetting.get_setting(f'printer_{kind}_cpl', '32') or 32),
        }
        if cfg['type'] == 'network':
            cfg['ip'] = SystemSetting.get_setting(f'printer_{kind}_ip', '192.168.1.101')
            cfg['port'] = int(SystemSetting.get_setting(f'printer_{kind}_port', '9100') or 9100)
            cfg['timeout'] = int(SystemSetting.get_setting(f'printer_{kind}_timeout', '5') or 5)
        elif cfg['type'] == 'usb':
            cfg['vendor_id'] = int(SystemSetting.get_setting(f'printer_{kind}_usb_vid', '0'), 0) or 0x0483
            cfg['product_id'] = int(SystemSetting.get_setting(f'printer_{kind}_usb_pid', '0'), 0) or 0x5743
            cfg['in_ep'] = int(SystemSetting.get_setting(f'printer_{kind}_usb_in_ep', '129') or 129)  # 0x81
            cfg['out_ep'] = int(SystemSetting.get_setting(f'printer_{kind}_usb_out_ep', '1') or 1)    # 0x01
        elif cfg['type'] == 'serial':
            cfg['com'] = SystemSetting.get_setting(f'printer_{kind}_com', 'COM3')
            cfg['baudrate'] = int(SystemSetting.get_setting(f'printer_{kind}_baud', '9600') or 9600)
            cfg['bytesize'] = int(SystemSetting.get_setting(f'printer_{kind}_bytesize', '8') or 8)
            cfg['parity'] = SystemSetting.get_setting(f'printer_{kind}_parity', 'N') or 'N'
            cfg['stopbits'] = int(SystemSetting.get_setting(f'printer_{kind}_stopbits', '1') or 1)
            cfg['timeout'] = int(SystemSetting.get_setting(f'printer_{kind}_timeout', '1') or 1)
        return cfg

    def _open_printer(self, cfg: dict):
        t = cfg.get('type', 'disabled')
        if t == 'network':
            return Network(cfg['ip'], port=cfg['port'], timeout=cfg['timeout'])
        if t == 'usb':
            return Usb(cfg['vendor_id'], cfg['product_id'], in_ep=cfg['in_ep'], out_ep=cfg['out_ep'], timeout=0)
        if t == 'serial':
            return Serial(
                devfile=cfg['com'],
                baudrate=cfg['baudrate'],
                bytesize=cfg['bytesize'],
                parity=cfg['parity'],
                stopbits=cfg['stopbits'],
                timeout=cfg['timeout'],
                dsrdtr=True
            )
        return None  # disabled
    
    def _set_code_page(self, printer, code_page: int) -> None:
        try:
            # ESC t n
            printer._raw(bytes([0x1B, 0x74, code_page]))
        except Exception as e:
            current_app.logger.warning(f"Code page set failed: {e}")
    
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
        
        return "\r\n".join(receipt)
    
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
        
        return "\r\n".join(receipt)
    
    def _generate_final_receipt(self, order: Order) -> str:
        """Генерация финального чека для клиента."""
        waiter = Staff.query.get(order.waiter_id)
        
        # Получаем настройки ресторана
        from app.models.system_setting import SystemSetting
        restaurant_address = SystemSetting.get_setting('restaurant_address', 'Адрес: [Адрес ресторана]')
        restaurant_phone = SystemSetting.get_setting('restaurant_phone', 'Телефон: +993 12 XX-XX-XX')
        
        receipt = []
        receipt.append("=" * 32)
        receipt.append("РЕСТОРАН DENIZ")
        receipt.append("=" * 32)
        receipt.append(restaurant_address)
        receipt.append(restaurant_phone)
        receipt.append(f"Стол: {order.table.table_number}      Заказ: #{order.id}")
        receipt.append(f"Дата: {order.created_at.strftime('%d.%m.%Y')}")
        receipt.append(f"Время: {order.created_at.strftime('%H:%M')}  Гостей: {order.guest_count}")
        receipt.append(f"Официант: {waiter.name if waiter else 'Неизвестно'}")
        
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
            receipt.append("-" * 32)
            for item in kitchen_items:
                receipt.append(f"{item.quantity}x {item.menu_item.name_ru:<20} {item.unit_price * item.quantity:>8.2f}")
                if item.comments:
                    receipt.append(f"   - {item.comments}")
            receipt.append("")  # Пустая строка после кухни
        
        # Печатаем позиции бара
        if bar_items:
            receipt.append("БАР:")
            receipt.append("-" * 32)
            for item in bar_items:
                receipt.append(f"{item.quantity}x {item.menu_item.name_ru:<20} {item.unit_price * item.quantity:>8.2f}")
                if item.comments:
                    receipt.append(f"   - {item.comments}")
            receipt.append("")  # Пустая строка после бара
        
        receipt.append("-" * 32)
        receipt.append(f"Подытог:              {order.subtotal:>8.2f}")
        receipt.append(f"Сервисный сбор (10%): {order.service_charge:>8.2f}")
        
        # Промежуточный итог (подытог + сервисный сбор)
        intermediate_total = order.subtotal + order.service_charge
        receipt.append(f"Промежуточный итог:   {intermediate_total:>8.2f}")
        
        # Скидка по бонусной карте
        if order.discount_amount and order.discount_amount > 0:
            discount_percent = order.bonus_card.discount_percent if order.bonus_card else 0
            receipt.append(f"Скидка карта {order.bonus_card.card_number if order.bonus_card else 'XXXXXX'}: -{order.discount_amount:>8.2f}")
            receipt.append(f"({discount_percent}%)")
        
        receipt.append("-" * 32)
        receipt.append(f"ИТОГО:                {order.total_amount:>8.2f}")
        receipt.append("=" * 32)
        receipt.append("Благодарим за посещение!")
        receipt.append("=" * 32)
        
        return "\r\n".join(receipt)
    
    def _send_to_printer(self, content: str, printer_type: str) -> bool:
        """
        printer_type: 'kitchen' | 'bar' | 'receipt'
        """
        try:
            cfg = self._get_printer_config(printer_type)
            if cfg.get('type') == 'disabled':
                raise RuntimeError("Printing disabled for this printer type")

            printer = self._open_printer(cfg)
            if not printer:
                raise RuntimeError("Printer open failed (no config or disabled)")

            # Устанавливаем кириллицу (по умолчанию 37 = Windows-1251) — для будущих кухонных тоже
            self._set_code_page(printer, cfg.get('code_page', 37))

            # Печать
            printer.text(content + "\n")
            try:
                printer.cut()
            except Exception:
                # некоторые 58мм не поддерживают автоматическую обрезку
                pass
            try:
                printer.close()
            except Exception:
                pass

            return True

        except Exception as e:
            # Fallback: лог + сохранение в файл
            current_app.logger.error(f"Printer error ({printer_type}): {e}")
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"receipt_{printer_type}_{timestamp}.txt"
                filepath = os.path.join(current_app.root_path, '..', 'receipts', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                current_app.logger.info(f"Receipt saved to: {filepath}")
            except Exception as e2:
                current_app.logger.error(f"Receipt save failed: {e2}")
            return False 