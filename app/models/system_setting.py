"""Модель системных настроек."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import TYPE_CHECKING, Dict, Any, Optional
from app import db
from .base import BaseModel

if TYPE_CHECKING:
    pass

class SystemSetting(BaseModel):
    """Модель системных настроек."""
    
    __tablename__ = 'system_settings'
    
    # Основные поля
    setting_key: so.Mapped[str] = so.mapped_column(
        sa.String(100), unique=True, nullable=False, index=True
    )
    setting_value: so.Mapped[str] = so.mapped_column(
        sa.Text, nullable=False
    )
    description: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return f'<SystemSetting {self.setting_key}={self.setting_value}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'description': self.description,
        })
        return data
    
    @classmethod
    def get_setting(cls, key: str, default: str = None) -> str:
        """Получение значения настройки."""
        setting = cls.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else default
    
    @classmethod
    def set_setting(cls, key: str, value: str, description: str = None) -> 'SystemSetting':
        """Установка значения настройки."""
        setting = cls.query.filter_by(setting_key=key).first()
        
        if setting:
            setting.setting_value = value
            if description:
                setting.description = description
        else:
            setting = cls(
                setting_key=key,
                setting_value=value,
                description=description
            )
            db.session.add(setting)
        
        db.session.commit()
        return setting
    
    @classmethod
    def get_all_settings(cls) -> Dict[str, str]:
        """Получение всех настроек в виде словаря."""
        settings = cls.query.all()
        return {setting.setting_key: setting.setting_value for setting in settings}
    
    @classmethod
    def initialize_default_settings(cls) -> None:
        """Инициализация настроек по умолчанию."""
        default_settings = [
            ('service_charge_percent', '10.0', 'Процент сервисного сбора'),
            ('order_edit_timeout_minutes', '5', 'Время в минутах для отмены/изменения заказа клиентом'),
            ('printer_kitchen_ip', '192.168.1.100', 'IP адрес кухонного принтера'),
            ('printer_bar_ip', '192.168.1.101', 'IP адрес барного принтера'),
            ('printer_receipt_ip', '192.168.1.102', 'IP адрес принтера чеков'),
            ('printer_kitchen_port', '9100', 'Порт кухонного принтера'),
            ('printer_bar_port', '9100', 'Порт барного принтера'),
            ('printer_receipt_port', '9100', 'Порт принтера чеков'),
            ('system_language', 'ru', 'Основной язык системы'),
            ('max_guests_per_table', '8', 'Максимальное количество гостей за столом'),
        ]
        
        for key, value, description in default_settings:
            cls.set_setting(key, value, description) 