"""Базовая модель с общими полями и методами."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime
from typing import Optional, Any, Dict
from flask_sqlalchemy import SQLAlchemy

# Локальный экземпляр будет заменен на глобальный при инициализации
db = SQLAlchemy()

class BaseModel(db.Model):
    """Базовая модель с общими полями и методами."""
    
    __abstract__ = True
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False
    )
    updated_at: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime(timezone=True),
        onupdate=sa.func.now(),
        nullable=True
    )
    
    def save(self) -> 'BaseModel':
        """Сохранение записи."""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self) -> None:
        """Удаление записи."""
        db.session.delete(self)
        db.session.commit()
    
    def update(self, **kwargs) -> 'BaseModel':
        """Обновление полей."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Базовая сериализация."""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def get_by_id(cls, id: int) -> Optional['BaseModel']:
        """Получение записи по ID."""
        return cls.query.get(id)
    
    @classmethod
    def get_all(cls) -> list['BaseModel']:
        """Получение всех записей."""
        return cls.query.all() 