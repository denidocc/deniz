"""Модели блюд меню."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional, TYPE_CHECKING, Dict, Any
from decimal import Decimal
from .base import BaseModel, db

if TYPE_CHECKING:
    from .menu_category import MenuCategory
    from .order_item import OrderItem

class MenuItem(BaseModel):
    """Модель блюд меню."""
    
    __tablename__ = 'menu_items'
    
    # Основные поля
    category_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, sa.ForeignKey('menu_categories.id'), nullable=False, index=True
    )
    name_ru: so.Mapped[str] = so.mapped_column(
        sa.Text, nullable=False
    )
    name_tk: so.Mapped[str] = so.mapped_column(
        sa.Text, nullable=True
    )
    name_en: so.Mapped[str] = so.mapped_column(
        sa.Text, nullable=True
    )
    description_ru: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )
    description_tk: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )
    description_en: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )
    price: so.Mapped[Decimal] = so.mapped_column(
        sa.Numeric(10, 2), nullable=False
    )
    image_url: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )
    preparation_type: so.Mapped[str] = so.mapped_column(
        sa.String(20), nullable=False, index=True
    )  # kitchen, bar
    estimated_time: so.Mapped[int] = so.mapped_column(
        sa.Integer, default=15, nullable=False
    )  # время приготовления в минутах
    has_size_options: so.Mapped[bool] = so.mapped_column(
        sa.Boolean, default=False, nullable=False
    )
    can_modify_ingredients: so.Mapped[bool] = so.mapped_column(
        sa.Boolean, default=False, nullable=False
    )
    is_active: so.Mapped[bool] = so.mapped_column(
        sa.Boolean, default=True, nullable=False
    )
    sort_order: so.Mapped[int] = so.mapped_column(
        sa.Integer, default=0, nullable=False
    )
    
    # Отношения
    category: so.Mapped["MenuCategory"] = so.relationship(
        back_populates="items",
        lazy='selectin'
    )
    
    sizes: so.Mapped[list["MenuItemSize"]] = so.relationship(
        back_populates="menu_item",
        lazy='selectin',
        order_by="MenuItemSize.sort_order"
    )
    
    order_items: so.Mapped[list["OrderItem"]] = so.relationship(
        back_populates="menu_item",
        lazy='selectin'
    )
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return f'<MenuItem {self.name_ru} ({self.preparation_type})>'
    
    def get_name(self, language: str = 'ru') -> str:
        """Получение названия на указанном языке."""
        if language == 'tk' and self.name_tk:
            return self.name_tk
        elif language == 'en' and self.name_en:
            return self.name_en
        else:
            return self.name_ru
    
    def get_description(self, language: str = 'ru') -> Optional[str]:
        """Получение описания на указанном языке."""
        if language == 'tk' and self.description_tk:
            return self.description_tk
        elif language == 'en' and self.description_en:
            return self.description_en
        else:
            return self.description_ru
    
    def is_kitchen_item(self) -> bool:
        """Проверка, является ли блюдом кухни."""
        return self.preparation_type == 'kitchen'
    
    def is_bar_item(self) -> bool:
        """Проверка, является ли напитком бара."""
        return self.preparation_type == 'bar'
    
    def get_base_price(self) -> Decimal:
        """Получение базовой цены."""
        return self.price
    
    def get_price_for_size(self, size_id: Optional[int] = None) -> Decimal:
        """Получение цены для размера."""
        if not size_id:
            return self.price
        
        size = next((s for s in self.sizes if s.id == size_id), None)
        if size:
            return self.price + size.price_modifier
        return self.price
    
    def to_dict(self, language: str = 'ru') -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'name': self.get_name(language),
            'name_ru': self.name_ru,
            'name_tk': self.name_tk,
            'name_en': self.name_en,
            'description': self.get_description(language),
            'description_ru': self.description_ru,
            'description_tk': self.description_tk,
            'description_en': self.description_en,
            'price': float(self.price),
            'image_url': self.image_url,
            'preparation_type': self.preparation_type,
            'estimated_time': self.estimated_time,
            'has_size_options': self.has_size_options,
            'can_modify_ingredients': self.can_modify_ingredients,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'category': {
                'id': self.category.id,
                'name': self.category.get_name(language)
            } if self.category else None,
            'sizes': [size.to_dict(language) for size in self.sizes],
        })
        return data
    
    @classmethod
    def get_active_items(cls) -> list['MenuItem']:
        """Получение всех активных блюд."""
        return cls.query.filter_by(is_active=True).order_by(cls.sort_order).all()
    
    @classmethod
    def get_by_category(cls, category_id: int) -> list['MenuItem']:
        """Получение блюд по категории."""
        return cls.query.filter_by(
            category_id=category_id,
            is_active=True
        ).order_by(cls.sort_order).all()
    
    @classmethod
    def get_by_preparation_type(cls, prep_type: str) -> list['MenuItem']:
        """Получение блюд по типу приготовления."""
        return cls.query.filter_by(
            preparation_type=prep_type,
            is_active=True
        ).order_by(cls.sort_order).all()
    
    @classmethod
    def get_kitchen_items(cls) -> list['MenuItem']:
        """Получение всех блюд кухни."""
        return cls.get_by_preparation_type('kitchen')
    
    @classmethod
    def get_bar_items(cls) -> list['MenuItem']:
        """Получение всех напитков бара."""
        return cls.get_by_preparation_type('bar')


class MenuItemSize(BaseModel):
    """Модель размеров порций блюд."""
    
    __tablename__ = 'menu_item_sizes'
    
    # Основные поля
    menu_item_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, sa.ForeignKey('menu_items.id'), nullable=False, index=True
    )
    size_name_ru: so.Mapped[str] = so.mapped_column(
        sa.Text, nullable=False
    )
    size_name_tk: so.Mapped[str] = so.mapped_column(
        sa.Text, nullable=True
    )
    size_name_en: so.Mapped[str] = so.mapped_column(
        sa.Text, nullable=True
    )
    price_modifier: so.Mapped[Decimal] = so.mapped_column(
        sa.Numeric(5, 2), default=0.00, nullable=False
    )
    sort_order: so.Mapped[int] = so.mapped_column(
        sa.Integer, default=0, nullable=False
    )
    
    # Отношения
    menu_item: so.Mapped["MenuItem"] = so.relationship(
        back_populates="sizes",
        lazy='selectin'
    )
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return f'<MenuItemSize {self.size_name_ru} ({self.price_modifier})>'
    
    def get_name(self, language: str = 'ru') -> str:
        """Получение названия на указанном языке."""
        if language == 'tk' and self.size_name_tk:
            return self.size_name_tk
        elif language == 'en' and self.size_name_en:
            return self.size_name_en
        else:
            return self.size_name_ru
    
    def get_price(self) -> Decimal:
        """Получение полной цены с модификатором."""
        return self.menu_item.price + self.price_modifier
    
    def to_dict(self, language: str = 'ru') -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'name': self.get_name(language),
            'name_ru': self.size_name_ru,
            'name_tk': self.size_name_tk,
            'name_en': self.size_name_en,
            'price_modifier': float(self.price_modifier),
            'price': float(self.get_price()),
            'sort_order': self.sort_order,
        })
        return data 