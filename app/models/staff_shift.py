"""Модель смен персонала."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional, TYPE_CHECKING, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from app import db
from .base import BaseModel

if TYPE_CHECKING:
    from .staff import Staff
    from .table_assignment import TableAssignment
    from .order import Order

class StaffShift(BaseModel):
    """Модель смен персонала."""
    
    __tablename__ = 'staff_shifts'
    
    # Основные поля
    staff_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, sa.ForeignKey('staff.id'), nullable=False, index=True
    )
    shift_date: so.Mapped[date] = so.mapped_column(
        sa.Date, nullable=False, index=True
    )
    shift_start: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    shift_end: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    total_orders: so.Mapped[int] = so.mapped_column(
        sa.Integer, default=0, nullable=False
    )
    total_revenue: so.Mapped[Decimal] = so.mapped_column(
        sa.Numeric(12, 2), default=0.00, nullable=False
    )
    is_active: so.Mapped[bool] = so.mapped_column(
        sa.Boolean, default=True, nullable=False, index=True
    )
    notes: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )
    
    # Отношения
    staff: so.Mapped["Staff"] = so.relationship(
        back_populates="shifts",
        lazy='selectin'
    )
    
    table_assignments: so.Mapped[list["TableAssignment"]] = so.relationship(
        back_populates="shift",
        lazy='selectin'
    )
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return f'<StaffShift {self.staff.name} {self.shift_date}>'
    
    def is_active_shift(self) -> bool:
        """Проверка, активна ли смена."""
        return self.is_active and self.shift_end is None
    
    def get_duration(self) -> Optional[int]:
        """Получение продолжительности смены в минутах."""
        if self.shift_end:
            duration = self.shift_end - self.shift_start
            return int(duration.total_seconds() / 60)
        return None
    
    def get_assigned_tables(self) -> list["Table"]:
        """Получение назначенных столов."""
        from .table import Table
        table_ids = [ta.table_id for ta in self.table_assignments if ta.is_active]
        return Table.query.filter(Table.id.in_(table_ids)).all()
    
    def calculate_stats(self) -> None:
        """Пересчет статистики смены."""
        # Подсчитываем заказы за смену
        orders = Order.query.filter_by(
            waiter_id=self.staff_id
        ).filter(
            Order.created_at >= self.shift_start
        )
        
        if self.shift_end:
            orders = orders.filter(Order.created_at <= self.shift_end)
        
        orders = orders.all()
        
        self.total_orders = len(orders)
        self.total_revenue = sum(order.total_amount for order in orders)
    
    def end_shift(self) -> None:
        """Завершение смены."""
        self.shift_end = datetime.utcnow()
        self.is_active = False
        self.calculate_stats()
        
        # Освобождаем назначенные столы
        for assignment in self.table_assignments:
            if assignment.is_active:
                assignment.deactivate()
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'staff': {
                'id': self.staff.id,
                'name': self.staff.name,
                'login': self.staff.login,
            } if self.staff else None,
            'shift_date': self.shift_date.isoformat(),
            'shift_start': self.shift_start.isoformat(),
            'shift_end': self.shift_end.isoformat() if self.shift_end else None,
            'total_orders': self.total_orders,
            'total_revenue': float(self.total_revenue),
            'is_active': self.is_active,
            'notes': self.notes,
            'duration_minutes': self.get_duration(),
            'assigned_tables': [table.to_dict() for table in self.get_assigned_tables()],
        })
        return data
    
    @classmethod
    def get_active_shifts(cls) -> list['StaffShift']:
        """Получение всех активных смен."""
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def get_by_staff(cls, staff_id: int) -> list['StaffShift']:
        """Получение смен по сотруднику."""
        return cls.query.filter_by(staff_id=staff_id).order_by(cls.shift_start.desc()).all()
    
    @classmethod
    def get_by_date(cls, shift_date: date) -> list['StaffShift']:
        """Получение смен по дате."""
        return cls.query.filter_by(shift_date=shift_date).all()
    
    @classmethod
    def get_current_shift(cls, staff_id: int) -> Optional['StaffShift']:
        """Получение текущей смены сотрудника."""
        return cls.query.filter_by(
            staff_id=staff_id,
            is_active=True
        ).first()
    
    @classmethod
    def start_shift(cls, staff_id: int, table_ids: list[int] = None) -> 'StaffShift':
        """Начало новой смены."""
        # Завершаем предыдущую активную смену, если есть
        current_shift = cls.get_current_shift(staff_id)
        if current_shift:
            current_shift.end_shift()
        
        # Создаем новую смену
        shift = cls(
            staff_id=staff_id,
            shift_date=datetime.utcnow().date(),
            shift_start=datetime.utcnow(),
            is_active=True
        )
        
        db.session.add(shift)
        db.session.flush()  # Получаем ID смены
        
        # Назначаем столы, если указаны
        if table_ids:
            from .table_assignment import TableAssignment
            for table_id in table_ids:
                TableAssignment.assign_table_to_waiter(
                    table_id=table_id,
                    waiter_id=staff_id,
                    shift_id=shift.id
                )
        
        db.session.commit()
        return shift 