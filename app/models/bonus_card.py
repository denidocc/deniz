"""Модель бонусных карт."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional, TYPE_CHECKING, Dict, Any
from datetime import datetime, date
from flask import current_app
from app import db
from .base import BaseModel

if TYPE_CHECKING:
    from .order import Order

def encrypted_property(field_name):
    """Декоратор для создания зашифрованных свойств."""
    def getter(self):
        try:
            return db.session.scalar(
                sa.func.pgp_sym_decrypt(
                    sa.cast(getattr(self, f'_{field_name}'), sa.LargeBinary),
                    current_app.config['ENCRYPTION_KEY']
                )
            )
        except Exception as e:
            current_app.logger.error(f"Error decrypting {field_name}: {e}")
            return None
    
    def setter(self, value):
        if value:
            try:
                encrypted_value = db.session.scalar(
                    sa.func.pgp_sym_encrypt(
                        value,
                        current_app.config['ENCRYPTION_KEY']
                    )
                )
                setattr(self, f'_{field_name}', encrypted_value)
            except Exception as e:
                current_app.logger.error(f"Error encrypting {field_name}: {e}")
                raise ValueError(f"Failed to encrypt {field_name}")
        else:
            setattr(self, f'_{field_name}', None)
    
    return property(getter, setter)

class BonusCard(BaseModel):
    """Модель бонусной карты."""
    
    __tablename__ = 'bonus_cards'
    
    # Основные поля
    card_number: so.Mapped[str] = so.mapped_column(
        sa.String(20), unique=True, nullable=False, index=True
    )
    discount_percent: so.Mapped[int] = so.mapped_column(
        sa.Integer, nullable=False, default=0
    )
    is_active: so.Mapped[bool] = so.mapped_column(
        sa.Boolean, default=True, nullable=False
    )
    
    # Зашифрованные поля (хранятся как bytea)
    _first_name: so.Mapped[Optional[str]] = so.mapped_column(
        'first_name', sa.LargeBinary, nullable=True
    )
    _last_name: so.Mapped[Optional[str]] = so.mapped_column(
        'last_name', sa.LargeBinary, nullable=True
    )
    
    # Даты
    activated_at: so.Mapped[Optional[date]] = so.mapped_column(
        sa.Date, nullable=True
    )
    deactivated_at: so.Mapped[Optional[date]] = so.mapped_column(
        sa.Date, nullable=True
    )
    
    # Статистика
    total_used: so.Mapped[int] = so.mapped_column(
        sa.Integer, default=0, nullable=False
    )
    total_saved: so.Mapped[float] = so.mapped_column(
        sa.Numeric(10, 2), default=0.0, nullable=False
    )
    
    # Отношения
    orders: so.Mapped[list["Order"]] = so.relationship(
        back_populates="bonus_card",
        lazy='selectin'
    )
    
    # Зашифрованные свойства
    first_name = encrypted_property('first_name')
    last_name = encrypted_property('last_name')
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return f'<BonusCard {self.card_number}>'
    
    def is_valid(self) -> bool:
        """Проверка валидности карты с автоматической деактивацией."""
        if not self.is_active:
            return False
        
        today = datetime.now().date()
        
        # Приводим даты к типу date для корректного сравнения
        if self.activated_at:
            activated_date = self.activated_at.date() if hasattr(self.activated_at, 'date') else self.activated_at
            if today < activated_date:
                return False
        
        if self.deactivated_at:
            deactivated_date = self.deactivated_at.date() if hasattr(self.deactivated_at, 'date') else self.deactivated_at
            if today > deactivated_date:
                # Автоматически деактивируем карту при истечении срока
                if self.is_active:
                    self.is_active = False
                    try:
                        from app import db
                        db.session.commit()
                        from flask import current_app
                        current_app.logger.info(f"Bonus card {self.card_number} automatically deactivated due to expired date")
                    except Exception as e:
                        current_app.logger.error(f"Failed to auto-deactivate card {self.card_number}: {e}")
                        db.session.rollback()
                return False
        
        return True
    
    def get_invalidity_reason(self) -> str:
        """Получение причины невалидности карты."""
        if not self.is_active:
            return "Карта неактивна"
        
        today = datetime.now().date()
        
        if self.activated_at:
            activated_date = self.activated_at.date() if hasattr(self.activated_at, 'date') else self.activated_at
            if today < activated_date:
                return f"Карта будет активна с {activated_date.strftime('%d.%m.%Y')}"
        
        if self.deactivated_at:
            deactivated_date = self.deactivated_at.date() if hasattr(self.deactivated_at, 'date') else self.deactivated_at
            if today > deactivated_date:
                return f"Срок действия карты истек {deactivated_date.strftime('%d.%m.%Y')}"
        
        return "Карта валидна"
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'card_number': self.card_number,
            'discount_percent': self.discount_percent,
            'is_active': self.is_active,
            'activated_at': self.activated_at.isoformat() if self.activated_at else None,
            'deactivated_at': self.deactivated_at.isoformat() if self.deactivated_at else None,
            'total_used': self.total_used,
            'total_saved': float(self.total_saved),
        })
        
        if include_sensitive:
            data.update({
                'first_name': self.first_name,
                'last_name': self.last_name,
            })
        
        return data
    
    @classmethod
    def find_by_card_number(cls, card_number: str) -> Optional['BonusCard']:
        """Поиск карты по номеру."""
        return cls.query.filter_by(card_number=card_number).first()