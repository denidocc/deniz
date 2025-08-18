import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional, Dict, Any
from datetime import datetime
from app import db
from .base import BaseModel

class Banner(BaseModel):
    """Модель баннера для карусели."""
    
    __tablename__ = 'banner'
    
    # Основные поля
    title: so.Mapped[str] = so.mapped_column(
        sa.Text, nullable=False, index=True
    )
    description: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )
    image_path: so.Mapped[str] = so.mapped_column(
        sa.Text, nullable=False, index=True
    )
    image_url: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )
    
    # Настройки отображения
    is_active: so.Mapped[bool] = so.mapped_column(
        sa.Boolean, default=True, nullable=False, index=True
    )
    sort_order: so.Mapped[int] = so.mapped_column(
        sa.Integer, default=0, nullable=False, index=True
    )
    
    # Ссылка и действия
    link_url: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )
    link_text: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )
    
    # Метаданные
    start_date: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    end_date: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return f'<Banner {self.title}>'
    
    def is_currently_active(self) -> bool:
        """Проверка, активен ли баннер в данный момент."""
        if not self.is_active:
            return False
        
        now = datetime.now().replace(tzinfo=None)
        
        if self.start_date and now < self.start_date.replace(tzinfo=None):
            return False
        
        if self.end_date and now > self.end_date.replace(tzinfo=None):
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'title': self.title,
            'description': self.description,
            'image_path': self.image_path,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'link_url': self.link_url,
            'link_text': self.link_text,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_currently_active': self.is_currently_active()
        })
        return data
    
    @classmethod
    def get_active_banners(cls) -> list['Banner']:
        """Получение активных баннеров."""
        return cls.query.filter_by(is_active=True).order_by(cls.sort_order).all()
    
    @classmethod
    def get_current_banners(cls) -> list['Banner']:
        """Получение баннеров, активных в данный момент."""
        now = datetime.now().replace(tzinfo=None)
        return cls.query.filter(
            cls.is_active == True,
            sa.or_(
                cls.start_date.is_(None),
                sa.func.date_trunc('minute', cls.start_date) <= sa.func.date_trunc('minute', sa.func.now())
            ),
            sa.or_(
                cls.end_date.is_(None),
                sa.func.date_trunc('minute', cls.end_date) >= sa.func.date_trunc('minute', sa.func.now())
            )
        ).order_by(cls.sort_order).all()
