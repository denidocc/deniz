"""Модель бонусных карт."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional, TYPE_CHECKING, Dict, Any
from datetime import datetime
from app import db
from .base import BaseModel

if TYPE_CHECKING:
    from .order import Order

class BonusCard(BaseModel):
    """Модель бонусной карты."""
    
    __tablename__ = 'bonus_cards'
    
    # Основные поля
    card_number: so.Mapped[str] = so.mapped_column(
        sa.String(6), unique=True, nullable=False, index=True
    )
    discount_percent: so.Mapped[int] = so.mapped_column(
        sa.Integer, nullable=False, default=0
    )
    is_active: so.Mapped[bool] = so.mapped_column(
        sa.Boolean, default=True, nullable=False
    )
    total_used: so.Mapped[int] = so.mapped_column(
        sa.Integer, default=0, nullable=False
    )
    total_saved: so.Mapped[float] = so.mapped_column(
        sa.Numeric(10, 2), default=0.00, nullable=False
    )
    
    # Отношения
    orders: so.Mapped[list["Order"]] = so.relationship(
        back_populates="bonus_card",
        lazy='selectin'
    )
    
    def __repr__(self) -> str:
        return f'<BonusCard {self.card_number}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'card_number': self.card_number,
            'discount_percent': self.discount_percent,
            'is_active': self.is_active,
            'total_used': self.total_used,
            'total_saved': float(self.total_saved),
        })
        return data
    
    @classmethod
    def find_by_number(cls, card_number: str) -> Optional['BonusCard']:
        """Поиск карты по номеру."""
        return cls.query.filter_by(card_number=card_number, is_active=True).first()
    
    def calculate_discount(self, amount: float) -> float:
        """Расчет скидки для суммы."""
        return (amount * self.discount_percent) / 100
    
    def apply_to_order(self, order: 'Order') -> None:
        """Применение карты к заказу."""
        discount_amount = self.calculate_discount(float(order.subtotal))
        order.discount_amount = discount_amount
        order.bonus_card_id = self.id
        self.total_used += 1
        self.total_saved += discount_amount