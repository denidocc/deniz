"""Модель категорий меню."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import TYPE_CHECKING, Dict, Any
from .base import BaseModel, db

if TYPE_CHECKING:
    from .menu_item import MenuItem

class MenuCategory(BaseModel):
    """Модель категорий меню."""
    
    __tablename__ = 'menu_categories'
    
    # Основные поля
    name_ru: so.Mapped[str] = so.mapped_column(
        sa.Text, nullable=False
    )
    name_tk: so.Mapped[str] = so.mapped_column(
        sa.Text, nullable=True
    )
    name_en: so.Mapped[str] = so.mapped_column(
        sa.Text, nullable=True
    )
    sort_order: so.Mapped[int] = so.mapped_column(
        sa.Integer, default=0, nullable=False
    )
    is_active: so.Mapped[bool] = so.mapped_column(
        sa.Boolean, default=True, nullable=False
    )
    
    # Отношения
    items: so.Mapped[list["MenuItem"]] = so.relationship(
        back_populates="category",
        lazy='selectin',
        order_by="MenuItem.sort_order"
    )
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return f'<MenuCategory {self.name_ru}>'
    
    def get_name(self, language: str = 'ru') -> str:
        """Получение названия на указанном языке."""
        if language == 'tk' and self.name_tk:
            return self.name_tk
        elif language == 'en' and self.name_en:
            return self.name_en
        else:
            return self.name_ru
    
    def get_active_items(self) -> list["MenuItem"]:
        """Получение активных блюд в категории."""
        return [item for item in self.items if item.is_active]
    
    def to_dict(self, language: str = 'ru') -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'name': self.get_name(language),
            'name_ru': self.name_ru,
            'name_tk': self.name_tk,
            'name_en': self.name_en,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'items_count': len(self.get_active_items()),
        })
        return data
    
    @classmethod
    def get_active_categories(cls) -> list['MenuCategory']:
        """Получение всех активных категорий."""
        return cls.query.filter_by(is_active=True).order_by(cls.sort_order).all()
    
    @classmethod
    def get_with_items(cls) -> list['MenuCategory']:
        """Получение категорий с блюдами."""
        return cls.query.filter_by(is_active=True).order_by(cls.sort_order).all() 