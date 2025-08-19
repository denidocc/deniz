"""Модель столов ресторана."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional, TYPE_CHECKING, Dict, Any
from .base import BaseModel

if TYPE_CHECKING:
    from .order import Order
    from .table_assignment import TableAssignment
    from .waiter_call import WaiterCall

class Table(BaseModel):
    """Модель столов ресторана."""
    
    __tablename__ = 'tables'
    
    # Основные поля
    table_number: so.Mapped[int] = so.mapped_column(
        sa.Integer, unique=True, nullable=False, index=True
    )
    status: so.Mapped[str] = so.mapped_column(
        sa.String(20), default='available', nullable=False, index=True
    )  # available, occupied, reserved
    capacity: so.Mapped[int] = so.mapped_column(
        sa.Integer, default=4, nullable=False
    )  # Вместимость стола
    is_active: so.Mapped[bool] = so.mapped_column(
        sa.Boolean, default=True, nullable=False
    )
    
    # Отношения
    orders: so.Mapped[list["Order"]] = so.relationship(
        back_populates="table",
        lazy='selectin'
    )
    
    assignments: so.Mapped[list["TableAssignment"]] = so.relationship(
        back_populates="table",
        lazy='selectin'
    )
    
    waiter_calls: so.Mapped[list["WaiterCall"]] = so.relationship(
        back_populates="table",
        lazy='selectin'
    )
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return f'<Table {self.table_number} ({self.status})>'
    
    def is_available(self) -> bool:
        """Проверка доступности стола."""
        return self.status == 'available' and self.is_active
    
    def is_occupied(self) -> bool:
        """Проверка занятости стола."""
        return self.status == 'occupied'
    
    def is_reserved(self) -> bool:
        """Проверка резервирования стола."""
        return self.status == 'reserved'
    
    def get_current_order(self) -> Optional["Order"]:
        """Получение текущего заказа для стола."""
        from .order import Order
        from flask import current_app
        
        # Логируем поиск заказов для отладки
        if current_app:
            current_app.logger.info(f"Searching for active orders on table {self.table_number} (ID: {self.id})")
            
        orders = Order.query.filter(
            Order.table_id == self.id,
            Order.status.in_(['pending', 'confirmed'])
        ).all()
        
        if current_app:
            current_app.logger.info(f"Found {len(orders)} orders for table {self.table_number}: {[o.id for o in orders]}")
            
        return orders[0] if orders else None
    
    def get_assigned_waiter(self) -> Optional["Staff"]:
        """Получение назначенного официанта."""
        from .table_assignment import TableAssignment
        assignment = TableAssignment.query.filter_by(
            table_id=self.id,
            is_active=True
        ).first()
        return assignment.staff if assignment else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'table_number': self.table_number,
            'status': self.status,
            'capacity': self.capacity,
            'is_active': self.is_active,
        })
        
        # Добавляем информацию о назначенном официанте
        waiter = self.get_assigned_waiter()
        if waiter:
            data['assigned_waiter'] = {
                'id': waiter.id,
                'name': waiter.name,
                'login': waiter.login
            }
        
        # Добавляем информацию о текущем заказе
        current_order = self.get_current_order()
        if current_order:
            data['current_order'] = {
                'id': current_order.id,
                'status': current_order.status,
                'guest_count': current_order.guest_count
            }
        
        return data
    
    @classmethod
    def get_available_tables(cls) -> list['Table']:
        """Получение всех доступных столов."""
        return cls.query.filter_by(
            status='available',
            is_active=True
        ).order_by(cls.table_number).all()
    
    @classmethod
    def get_occupied_tables(cls) -> list['Table']:
        """Получение всех занятых столов."""
        return cls.query.filter_by(status='occupied').order_by(cls.table_number).all()
    
    @classmethod
    def get_by_number(cls, table_number: int) -> Optional['Table']:
        """Получение стола по номеру."""
        return cls.query.filter_by(table_number=table_number).first()
    
    @classmethod
    def get_by_waiter(cls, waiter_id: int) -> list['Table']:
        """Получение столов, назначенных официанту."""
        from .table_assignment import TableAssignment
        assignments = TableAssignment.query.filter_by(
            waiter_id=waiter_id,
            is_active=True
        ).all()
        return [assignment.table for assignment in assignments] 