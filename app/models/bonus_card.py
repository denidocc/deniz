"""Модель бонусных карт."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime, date
from typing import Optional, Dict, Any
from app import db
from .base import BaseModel


class BonusCard(BaseModel):
    """Модель бонусной карты."""
    
    __tablename__ = 'bonus_cards'
    
    # Основные поля
    card_number: so.Mapped[str] = so.mapped_column(
        sa.String(6), unique=True, nullable=False, index=True
    )
    client_name: so.Mapped[str] = so.mapped_column(
        sa.Text, nullable=False
    )
    client_phone: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )
    discount_percent: so.Mapped[int] = so.mapped_column(
        sa.Integer, nullable=False, default=0
    )
    
    # Сроки действия
    valid_from: so.Mapped[date] = so.mapped_column(
        sa.Date, nullable=False, default=date.today
    )
    valid_until: so.Mapped[Optional[date]] = so.mapped_column(
        sa.Date, nullable=True
    )
    
    # Метаданные
    notes: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )
    created_by_staff_id: so.Mapped[Optional[int]] = so.mapped_column(
        sa.Integer, sa.ForeignKey('staff.id'), nullable=True
    )
    is_active: so.Mapped[bool] = so.mapped_column(
        sa.Boolean, default=True, nullable=False
    )
    
    # Статистика использования
    usage_count: so.Mapped[int] = so.mapped_column(
        sa.Integer, default=0, nullable=False
    )
    total_saved_amount: so.Mapped[float] = so.mapped_column(
        sa.Float, default=0.0, nullable=False
    )
    last_used_at: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    
    # Отношения
    created_by: so.Mapped[Optional["Staff"]] = so.relationship(
        "Staff", back_populates="created_bonus_cards", lazy='selectin'
    )
    
    def __repr__(self) -> str:
        return f'<BonusCard {self.card_number}: {self.discount_percent}%>'
    
    def is_valid(self) -> bool:
        """Проверка действительности карты."""
        if not self.is_active:
            return False
        
        today = date.today()
        
        # Проверка даты начала
        if self.valid_from > today:
            return False
        
        # Проверка даты окончания
        if self.valid_until and self.valid_until < today:
            return False
        
        return True
    
    def use_card(self, order_amount: float) -> float:
        """
        Использование карты и расчет скидки.
        
        Args:
            order_amount: Сумма заказа
            
        Returns:
            Размер скидки
        """
        if not self.is_valid():
            return 0.0
        
        discount_amount = (order_amount * self.discount_percent) / 100
        
        # Обновляем статистику
        self.usage_count += 1
        self.total_saved_amount += discount_amount
        self.last_used_at = datetime.utcnow()
        
        return discount_amount
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'card_number': self.card_number,
            'client_name': self.client_name,
            'discount_percent': self.discount_percent,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'is_active': self.is_active,
            'is_valid': self.is_valid(),
            'usage_count': self.usage_count,
            'total_saved_amount': self.total_saved_amount,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
        })
        
        if include_sensitive:
            data.update({
                'client_phone': self.client_phone,
                'notes': self.notes,
                'created_by_staff_id': self.created_by_staff_id,
            })
        
        return data
    
    @classmethod
    def find_by_number(cls, card_number: str) -> Optional['BonusCard']:
        """Поиск карты по номеру."""
        return cls.query.filter_by(card_number=card_number).first()
    
    @classmethod
    def get_active_cards(cls) -> list['BonusCard']:
        """Получение всех активных карт."""
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def get_valid_cards(cls) -> list['BonusCard']:
        """Получение всех действующих карт."""
        today = date.today()
        return cls.query.filter(
            cls.is_active == True,
            cls.valid_from <= today,
            sa.or_(cls.valid_until.is_(None), cls.valid_until >= today)
        ).all()
    
    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """Получение статистики по бонусным картам."""
        total_cards = cls.query.count()
        active_cards = cls.query.filter_by(is_active=True).count()
        used_cards = cls.query.filter(cls.usage_count > 0).count()
        
        total_savings = db.session.query(
            sa.func.sum(cls.total_saved_amount)
        ).scalar() or 0.0
        
        avg_discount = db.session.query(
            sa.func.avg(cls.discount_percent)
        ).scalar() or 0.0
        
        return {
            'total_cards': total_cards,
            'active_cards': active_cards,
            'used_cards': used_cards,
            'total_savings': float(total_savings),
            'average_discount': float(avg_discount),
        }