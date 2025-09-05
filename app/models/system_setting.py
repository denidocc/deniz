"""Модель системных настроек."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import TYPE_CHECKING, Dict, Any, Optional
from .base import BaseModel
from app import db

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

    # Совместимые методы доступа, используемые в API модулях
    @classmethod
    def get_value(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        return cls.get_setting(key, default)

    @classmethod
    def set_value(cls, key: str, value: str, description: str = None) -> 'SystemSetting':
        return cls.set_setting(key, value, description)
    
    @classmethod
    def get_all_settings(cls) -> Dict[str, str]:
        """Получение всех настроек в виде словаря."""
        settings = cls.query.all()
        return {setting.setting_key: setting.setting_value for setting in settings}
    
    @classmethod
    def initialize_default_settings(cls) -> None:
        """Инициализация настроек по умолчанию."""
        default_settings = [
            ('banner_delay_seconds', '5', 'Задержка между баннерами в секундах'),
            ('carousel_max_slides', '5', 'Максимальное количество слайдов в карусели'),
            ('printer_code', '1234', 'Код доступа к настройкам принтеров'),
            ('max_login_attempts', '5', 'Максимальное количество попыток входа'),
            ('block_duration', '30', 'Время блокировки IP в минутах'),
            ('auto_backup', 'true', 'Включить автоматическое резервное копирование'),
            ('backup_interval', 'daily', 'Интервал автобекапа (daily/weekly/monthly)'),
            ('backup_retention', '7', 'Количество резервных копий для хранения'),
            ('session_timeout', '120', 'Время сессии в минутах'),
            ('printer_kitchen_type', 'network', 'Тип подключения кухонного принтера (network|serial|disabled)'),
            ('printer_bar_type', 'serial', 'Тип подключения барного принтера'),
            ('printer_receipt_type', 'serial', 'Тип подключения чекового принтера'),

            # Kitchen printer settings
            ('printer_kitchen_ip', '192.168.1.101', 'IP кухонного принтера'),
            ('printer_kitchen_port', '9100', 'Порт кухонного принтера'),
            ('printer_kitchen_com', 'COM1', 'COM кухонного принтера'),
            ('printer_kitchen_baud', '9600', 'Скорость COM кухни'),
            ('printer_kitchen_bytesize', '8', 'Биты данных COM кухни'),
            ('printer_kitchen_parity', 'N', 'Четность COM кухни'),
            ('printer_kitchen_stopbits', '1', 'Стоп-биты COM кухни'),
            ('printer_kitchen_code_page', '37', 'Кодировка ESC/POS (кириллица) для кухни'),
            ('printer_kitchen_cpl', '48', 'Символов в строке (кухня, 80мм)'),

            # Bar printer settings
            ('printer_bar_ip', '192.168.1.102', 'IP барного принтера'),
            ('printer_bar_port', '9100', 'Порт барного принтера'),
            ('printer_bar_com', 'COM3', 'COM барного принтера'),
            ('printer_bar_baud', '9600', 'Скорость COM бара'),
            ('printer_bar_bytesize', '8', 'Биты данных COM бара'),
            ('printer_bar_parity', 'N', 'Четность COM бара'),
            ('printer_bar_stopbits', '1', 'Стоп-биты COM бара'),
            ('printer_bar_code_page', '37', 'Кодировка ESC/POS (кириллица) для бара'),
            ('printer_bar_cpl', '32', 'Символов в строке (бар, 58мм)'),

            # Receipt printer settings
            ('printer_receipt_ip', '192.168.1.103', 'IP чекового принтера'),
            ('printer_receipt_port', '9100', 'Порт чекового принтера'),
            ('printer_receipt_com', 'COM4', 'COM чекового принтера'),
            ('printer_receipt_baud', '9600', 'Скорость COM чека'),
            ('printer_receipt_bytesize', '8', 'Биты данных COM чека'),
            ('printer_receipt_parity', 'N', 'Четность COM чека'),
            ('printer_receipt_stopbits', '1', 'Стоп-биты COM чека'),
            ('printer_receipt_code_page', '37', 'Кодировка ESC/POS (кириллица) для чека'),
            ('printer_receipt_cpl', '32', 'Символов в строке (итоговый, 58мм)'),
        ]
        
        for key, value, description in default_settings:
            # Проверяем, существует ли уже эта настройка
            existing = cls.query.filter_by(setting_key=key).first()
            if not existing:
                cls.set_setting(key, value, description) 