"""Модель персонала ресторана."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional, TYPE_CHECKING, Dict, Any
from datetime import datetime
from argon2 import PasswordHasher
from flask_login import UserMixin
from .base import BaseModel

if TYPE_CHECKING:
    from .staff_shift import StaffShift
    from .table_assignment import TableAssignment
    from .order import Order
    from .bonus_card import BonusCard

class Staff(BaseModel, UserMixin):
    """Модель персонала ресторана."""
    
    __tablename__ = 'staff'
    
    # Основные поля
    name: so.Mapped[str] = so.mapped_column(
        sa.Text, nullable=False, index=True
    )
    role: so.Mapped[str] = so.mapped_column(
        sa.String(20), nullable=False, index=True
    )  # waiter, admin, kitchen, bar
    login: so.Mapped[str] = so.mapped_column(
        sa.String(50), unique=True, nullable=False, index=True
    )
    password_hash: so.Mapped[str] = so.mapped_column(
        sa.Text, nullable=False
    )
    is_active: so.Mapped[bool] = so.mapped_column(
        sa.Boolean, default=True, nullable=False
    )
    
    # Временные метки
    last_login: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=True
    )
    
    # Отношения
    shifts: so.Mapped[list["StaffShift"]] = so.relationship(
        back_populates="staff",
        lazy='selectin'
    )
    
    table_assignments: so.Mapped[list["TableAssignment"]] = so.relationship(
        back_populates="staff",
        lazy='selectin'
    )
    
    orders: so.Mapped[list["Order"]] = so.relationship(
        back_populates="waiter",
        lazy='selectin'
    )
    
    created_bonus_cards: so.Mapped[list["BonusCard"]] = so.relationship(
        back_populates="created_by",
        lazy='selectin'
    )
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return f'<Staff {self.name} ({self.role})>'
    
    def set_password(self, password: str) -> None:
        """Установка пароля с хешированием."""
        ph = PasswordHasher()
        self.password_hash = ph.hash(password)
    
    def check_password(self, password: str) -> bool:
        """Проверка пароля."""
        try:
            ph = PasswordHasher()
            ph.verify(self.password_hash, password)
            return True
        except Exception:
            return False
    
    def has_role(self, role_name: str) -> bool:
        """Проверка наличия роли."""
        return self.role == role_name
    
    def is_waiter(self) -> bool:
        """Проверка, является ли официантом."""
        return self.role == 'waiter'
    
    def is_admin(self) -> bool:
        """Проверка, является ли администратором."""
        return self.role == 'admin'
    
    def is_kitchen(self) -> bool:
        """Проверка, работает ли на кухне."""
        return self.role == 'kitchen'
    
    def is_bar(self) -> bool:
        """Проверка, работает ли в баре."""
        return self.role == 'bar'
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'name': self.name,
            'role': self.role,
            'login': self.login,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        })
        
        if include_sensitive:
            data.update({
                'password_hash': self.password_hash,
            })
        
        return data
    
    @classmethod
    def find_by_login(cls, login: str) -> Optional['Staff']:
        """Поиск пользователя по логину."""
        return cls.query.filter_by(login=login, is_active=True).first()
    
    @classmethod
    def get_by_role(cls, role: str) -> list['Staff']:
        """Получение всех пользователей по роли."""
        return cls.query.filter_by(role=role, is_active=True).all()
    
    @classmethod
    def get_active_waiters(cls) -> list['Staff']:
        """Получение всех активных официантов."""
        return cls.get_by_role('waiter')
    
    @classmethod
    def get_active_admins(cls) -> list['Staff']:
        """Получение всех активных администраторов."""
        return cls.get_by_role('admin') 