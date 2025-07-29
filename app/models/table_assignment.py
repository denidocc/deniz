"""Модель назначения столов официантам."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional, TYPE_CHECKING, Dict, Any
from datetime import datetime
from .base import BaseModel

if TYPE_CHECKING:
    from .table import Table
    from .staff import Staff
    from .staff_shift import StaffShift

class TableAssignment(BaseModel):
    """Модель назначения столов официантам."""
    
    __tablename__ = 'table_assignments'
    
    # Основные поля
    table_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, sa.ForeignKey('tables.id'), nullable=False, index=True
    )
    waiter_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, sa.ForeignKey('staff.id'), nullable=False, index=True
    )
    shift_id: so.Mapped[Optional[int]] = so.mapped_column(
        sa.Integer, sa.ForeignKey('staff_shifts.id'), nullable=True, index=True
    )
    assigned_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False
    )
    is_active: so.Mapped[bool] = so.mapped_column(
        sa.Boolean, default=True, nullable=False, index=True
    )
    
    # Отношения
    table: so.Mapped["Table"] = so.relationship(
        back_populates="assignments",
        lazy='selectin'
    )
    
    staff: so.Mapped["Staff"] = so.relationship(
        back_populates="table_assignments",
        lazy='selectin'
    )
    
    shift: so.Mapped[Optional["StaffShift"]] = so.relationship(
        back_populates="table_assignments",
        lazy='selectin'
    )
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return f'<TableAssignment Table {self.table_id} -> Waiter {self.waiter_id}>'
    
    def deactivate(self) -> None:
        """Деактивация назначения."""
        self.is_active = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'table': {
                'id': self.table.id,
                'table_number': self.table.table_number,
                'status': self.table.status,
            } if self.table else None,
            'waiter': {
                'id': self.staff.id,
                'name': self.staff.name,
                'login': self.staff.login,
            } if self.staff else None,
            'assigned_at': self.assigned_at.isoformat(),
            'is_active': self.is_active,
        })
        return data
    
    @classmethod
    def get_active_assignments(cls) -> list['TableAssignment']:
        """Получение всех активных назначений."""
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def get_by_waiter(cls, waiter_id: int) -> list['TableAssignment']:
        """Получение назначений по официанту."""
        return cls.query.filter_by(
            waiter_id=waiter_id,
            is_active=True
        ).all()
    
    @classmethod
    def get_by_table(cls, table_id: int) -> list['TableAssignment']:
        """Получение назначений по столу."""
        return cls.query.filter_by(
            table_id=table_id,
            is_active=True
        ).all()
    
    @classmethod
    def get_current_assignment(cls, table_id: int) -> Optional['TableAssignment']:
        """Получение текущего назначения для стола."""
        return cls.query.filter_by(
            table_id=table_id,
            is_active=True
        ).first()
    
    @classmethod
    def assign_table_to_waiter(cls, table_id: int, waiter_id: int, shift_id: Optional[int] = None) -> 'TableAssignment':
        """Назначение стола официанту."""
        # Деактивируем предыдущие назначения для этого стола
        existing_assignments = cls.query.filter_by(
            table_id=table_id,
            is_active=True
        ).all()
        
        for assignment in existing_assignments:
            assignment.deactivate()
        
        # Создаем новое назначение
        assignment = cls(
            table_id=table_id,
            waiter_id=waiter_id,
            shift_id=shift_id,
            is_active=True
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        return assignment 