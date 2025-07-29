"""Модель вызовов официанта."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional, TYPE_CHECKING, Dict, Any
from datetime import datetime
from .base import BaseModel

if TYPE_CHECKING:
    from .table import Table
    from .staff import Staff

class WaiterCall(BaseModel):
    """Модель вызовов официанта."""
    
    __tablename__ = 'waiter_calls'
    
    # Основные поля
    table_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, sa.ForeignKey('tables.id'), nullable=False, index=True
    )
    status: so.Mapped[str] = so.mapped_column(
        sa.String(20), default='pending', nullable=False, index=True
    )  # pending, responded
    responded_at: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    waiter_id: so.Mapped[Optional[int]] = so.mapped_column(
        sa.Integer, sa.ForeignKey('staff.id'), nullable=True, index=True
    )
    
    # Отношения
    table: so.Mapped["Table"] = so.relationship(
        back_populates="waiter_calls",
        lazy='selectin'
    )
    
    waiter: so.Mapped[Optional["Staff"]] = so.relationship(
        lazy='selectin'
    )
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return f'<WaiterCall Table {self.table_id} ({self.status})>'
    
    def is_pending(self) -> bool:
        """Проверка, ожидает ли вызов ответа."""
        return self.status == 'pending'
    
    def is_responded(self) -> bool:
        """Проверка, ответили ли на вызов."""
        return self.status == 'responded'
    
    def respond(self, waiter_id: int) -> None:
        """Ответ на вызов официанта."""
        self.status = 'responded'
        self.waiter_id = waiter_id
        self.responded_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'table': {
                'id': self.table.id,
                'table_number': self.table.table_number,
            } if self.table else None,
            'status': self.status,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
            'waiter': {
                'id': self.waiter.id,
                'name': self.waiter.name,
            } if self.waiter else None,
        })
        return data
    
    @classmethod
    def get_pending_calls(cls) -> list['WaiterCall']:
        """Получение всех ожидающих вызовов."""
        return cls.query.filter_by(status='pending').order_by(cls.created_at).all()
    
    @classmethod
    def get_by_table(cls, table_id: int) -> list['WaiterCall']:
        """Получение вызовов по столу."""
        return cls.query.filter_by(table_id=table_id).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_by_waiter(cls, waiter_id: int) -> list['WaiterCall']:
        """Получение вызовов по официанту."""
        return cls.query.filter_by(waiter_id=waiter_id).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def create_call(cls, table_id: int) -> 'WaiterCall':
        """Создание нового вызова."""
        call = cls(
            table_id=table_id,
            status='pending'
        )
        
        db.session.add(call)
        db.session.commit()
        
        return call 