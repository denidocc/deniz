"""Импорт всех моделей для автообнаружения Flask-Migrate."""

from .base import BaseModel
from .staff import Staff
from .table import Table
from .menu_category import MenuCategory
from .menu_item import MenuItem, MenuItemSize
from .order import Order, OrderItem
from .table_assignment import TableAssignment
from .waiter_call import WaiterCall

from .daily_report import DailyReport
from .audit_log import AuditLog
from .system_setting import SystemSetting
from .bonus_card import BonusCard
from .banner import Banner

__all__ = [
    'BaseModel',
    'Staff',
    'Table', 
    'MenuCategory',
    'MenuItem',
    'MenuItemSize',
    'Order',
    'OrderItem',
    'TableAssignment',
    'WaiterCall',

    'DailyReport',
    'AuditLog',
    'SystemSetting',
    'BonusCard',
    'Banner',
] 