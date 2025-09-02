"""Справочник статусов заказов."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from .base import BaseModel
from typing import Optional

class C_OrderStatus(BaseModel):
    """Справочник статусов заказов."""
    
    __tablename__ = 'c_order_status'
    
    name: so.Mapped[str] = so.mapped_column(
        sa.Text, unique=True, nullable=False
    )
    code: so.Mapped[str] = so.mapped_column(
        sa.String(50), unique=True, nullable=False
    )
    description: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )
    color: so.Mapped[str] = so.mapped_column(
        sa.String(7), nullable=False, default='#6c757d'  # hex цвет
    )
    icon: so.Mapped[str] = so.mapped_column(
        sa.String(10), nullable=False, default='⚫'  # эмодзи иконка
    )
    is_active: so.Mapped[bool] = so.mapped_column(
        sa.Boolean, default=True, nullable=False
    )
    sort_order: so.Mapped[int] = so.mapped_column(
        sa.Integer, default=0, nullable=False
    )
    can_transition_to: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True  # JSON массив разрешенных переходов
    )
    
    def __repr__(self) -> str:
        return f'<C_OrderStatus {self.name}>'
    
    @classmethod
    def get_active(cls) -> list['C_OrderStatus']:
        """Получение активных статусов."""
        return cls.query.filter_by(is_active=True).order_by(cls.sort_order).all()
    
    @classmethod
    def get_by_code(cls, code: str) -> Optional['C_OrderStatus']:
        """Получение статуса по коду."""
        return cls.query.filter_by(code=code, is_active=True).first()
    
    def get_transition_targets(self) -> list[str]:
        """Получение списка разрешенных переходов."""
        if not self.can_transition_to:
            return []
        
        # Если это уже список, возвращаем как есть
        if isinstance(self.can_transition_to, list):
            return self.can_transition_to
        
        # Если это строка, пытаемся распарсить JSON
        if isinstance(self.can_transition_to, str):
            try:
                import json
                return json.loads(self.can_transition_to)
            except (json.JSONDecodeError, TypeError):
                return []
        
        return []
