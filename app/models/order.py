"""Модели заказов."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional, TYPE_CHECKING, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from .base import BaseModel, db

if TYPE_CHECKING:
    from .table import Table
    from .staff import Staff
    from .order_item import OrderItem

class Order(BaseModel):
    """Модель заказа."""
    
    __tablename__ = 'orders'
    
    # Основные поля
    table_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, sa.ForeignKey('tables.id'), nullable=False, index=True
    )
    guest_count: so.Mapped[int] = so.mapped_column(
        sa.Integer, nullable=False
    )
    status: so.Mapped[str] = so.mapped_column(
        sa.String(20), default='pending', nullable=False, index=True
    )  # pending, confirmed, completed, cancelled
    subtotal: so.Mapped[Decimal] = so.mapped_column(
        sa.Numeric(10, 2), nullable=False
    )
    service_charge: so.Mapped[Decimal] = so.mapped_column(
        sa.Numeric(10, 2), nullable=False
    )
    total_amount: so.Mapped[Decimal] = so.mapped_column(
        sa.Numeric(10, 2), nullable=False
    )
    comments: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )
    waiter_id: so.Mapped[Optional[int]] = so.mapped_column(
        sa.Integer, sa.ForeignKey('staff.id'), nullable=True, index=True
    )
    language: so.Mapped[str] = so.mapped_column(
        sa.String(2), default='ru', nullable=False
    )  # ru, tk, en
    
    # Временные метки
    confirmed_at: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=True
    )
    completed_at: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=True
    )
    
    # Отношения
    table: so.Mapped["Table"] = so.relationship(
        back_populates="orders",
        lazy='selectin'
    )
    
    waiter: so.Mapped[Optional["Staff"]] = so.relationship(
        back_populates="orders",
        lazy='selectin'
    )
    
    items: so.Mapped[list["OrderItem"]] = so.relationship(
        back_populates="order",
        lazy='selectin',
        order_by="OrderItem.created_at"
    )
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return f'<Order #{self.id} ({self.status})>'
    
    def is_pending(self) -> bool:
        """Проверка, ожидает ли заказ подтверждения."""
        return self.status == 'pending'
    
    def is_confirmed(self) -> bool:
        """Проверка, подтвержден ли заказ."""
        return self.status == 'confirmed'
    
    def is_completed(self) -> bool:
        """Проверка, завершен ли заказ."""
        return self.status == 'completed'
    
    def is_cancelled(self) -> bool:
        """Проверка, отменен ли заказ."""
        return self.status == 'cancelled'
    
    def can_be_edited(self) -> bool:
        """Проверка возможности редактирования заказа."""
        from .system_setting import SystemSetting
        
        # Получаем настройку времени редактирования
        timeout_setting = SystemSetting.get_setting('order_edit_timeout_minutes', '5')
        timeout_minutes = int(timeout_setting)
        
        # Проверяем, не истекло ли время
        time_passed = datetime.utcnow() - self.created_at
        return time_passed.total_seconds() < (timeout_minutes * 60)
    
    def get_kitchen_items(self) -> list["OrderItem"]:
        """Получение позиций для кухни."""
        return [item for item in self.items if item.preparation_type == 'kitchen']
    
    def get_bar_items(self) -> list["OrderItem"]:
        """Получение позиций для бара."""
        return [item for item in self.items if item.preparation_type == 'bar']
    
    def calculate_totals(self) -> None:
        """Пересчет итоговых сумм."""
        subtotal = sum(item.total_price for item in self.items)
        self.subtotal = subtotal
        
        # Получаем процент сервисного сбора
        from .system_setting import SystemSetting
        service_charge_percent = SystemSetting.get_setting('service_charge_percent', '10.0')
        service_charge_rate = Decimal(service_charge_percent) / Decimal('100')
        
        self.service_charge = subtotal * service_charge_rate
        self.total_amount = subtotal + self.service_charge
    
    def confirm(self, waiter_id: int) -> None:
        """Подтверждение заказа."""
        self.status = 'confirmed'
        self.waiter_id = waiter_id
        self.confirmed_at = datetime.utcnow()
        
        # Обновляем статус стола
        self.table.status = 'occupied'
    
    def complete(self) -> None:
        """Завершение заказа."""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        
        # Освобождаем стол
        self.table.status = 'available'
    
    def cancel(self) -> None:
        """Отмена заказа."""
        self.status = 'cancelled'
        
        # Освобождаем стол
        self.table.status = 'available'
    
    def get_estimated_time(self) -> int:
        """Получение расчетного времени приготовления."""
        if not self.items:
            return 0
        
        # Берем максимальное время среди всех позиций
        max_time = max(item.estimated_time for item in self.items)
        return max_time
    
    def to_dict(self, include_items: bool = True) -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'table_number': self.table.table_number if self.table else None,
            'guest_count': self.guest_count,
            'status': self.status,
            'subtotal': float(self.subtotal),
            'service_charge': float(self.service_charge),
            'total_amount': float(self.total_amount),
            'comments': self.comments,
            'language': self.language,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'waiter': {
                'id': self.waiter.id,
                'name': self.waiter.name
            } if self.waiter else None,
            'can_be_edited': self.can_be_edited(),
            'estimated_time': self.get_estimated_time(),
        })
        
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
            data['kitchen_items'] = [item.to_dict() for item in self.get_kitchen_items()]
            data['bar_items'] = [item.to_dict() for item in self.get_bar_items()]
        
        return data
    
    @classmethod
    def get_pending_orders(cls) -> list['Order']:
        """Получение всех ожидающих заказов."""
        return cls.query.filter_by(status='pending').order_by(cls.created_at).all()
    
    @classmethod
    def get_confirmed_orders(cls) -> list['Order']:
        """Получение всех подтвержденных заказов."""
        return cls.query.filter_by(status='confirmed').order_by(cls.created_at).all()
    
    @classmethod
    def get_by_table(cls, table_id: int) -> list['Order']:
        """Получение заказов по столу."""
        return cls.query.filter_by(table_id=table_id).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_by_waiter(cls, waiter_id: int) -> list['Order']:
        """Получение заказов по официанту."""
        return cls.query.filter_by(waiter_id=waiter_id).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_current_by_table(cls, table_id: int) -> Optional['Order']:
        """Получение текущего заказа для стола."""
        return cls.query.filter_by(
            table_id=table_id,
            status__in=['pending', 'confirmed']
        ).first()


class OrderItem(BaseModel):
    """Модель позиции заказа."""
    
    __tablename__ = 'order_items'
    
    # Основные поля
    order_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, sa.ForeignKey('orders.id'), nullable=False, index=True
    )
    menu_item_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, sa.ForeignKey('menu_items.id'), nullable=False, index=True
    )
    size_id: so.Mapped[Optional[int]] = so.mapped_column(
        sa.Integer, sa.ForeignKey('menu_item_sizes.id'), nullable=True
    )
    quantity: so.Mapped[int] = so.mapped_column(
        sa.Integer, default=1, nullable=False
    )
    unit_price: so.Mapped[Decimal] = so.mapped_column(
        sa.Numeric(10, 2), nullable=False
    )
    total_price: so.Mapped[Decimal] = so.mapped_column(
        sa.Numeric(10, 2), nullable=False
    )
    preparation_type: so.Mapped[str] = so.mapped_column(
        sa.String(20), nullable=False, index=True
    )  # kitchen, bar
    comments: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )
    
    # Отношения
    order: so.Mapped["Order"] = so.relationship(
        back_populates="items",
        lazy='selectin'
    )
    
    menu_item: so.Mapped["MenuItem"] = so.relationship(
        back_populates="order_items",
        lazy='selectin'
    )
    
    size: so.Mapped[Optional["MenuItemSize"]] = so.relationship(
        lazy='selectin'
    )
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return f'<OrderItem {self.menu_item.name_ru} x{self.quantity}>'
    
    def calculate_total(self) -> None:
        """Расчет общей стоимости позиции."""
        if self.size:
            self.unit_price = self.menu_item.price + self.size.price_modifier
        else:
            self.unit_price = self.menu_item.price
        
        self.total_price = self.unit_price * self.quantity
    
    @property
    def estimated_time(self) -> int:
        """Получение времени приготовления."""
        return self.menu_item.estimated_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'menu_item': {
                'id': self.menu_item.id,
                'name': self.menu_item.name_ru,
                'preparation_type': self.menu_item.preparation_type,
            },
            'size': {
                'id': self.size.id,
                'name': self.size.size_name_ru,
            } if self.size else None,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total_price': float(self.total_price),
            'preparation_type': self.preparation_type,
            'comments': self.comments,
            'estimated_time': self.estimated_time,
        })
        return data 