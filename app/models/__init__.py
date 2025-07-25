"""Импорт всех моделей для автообнаружения Flask-Migrate."""

from .base import BaseModel
from .staff import Staff
from .table import Table
from .menu_category import MenuCategory
from .menu_item import MenuItem, MenuItemSize
from .order import Order, OrderItem
from .table_assignment import TableAssignment
from .waiter_call import WaiterCall
from .staff_shift import StaffShift
from .daily_report import DailyReport
from .audit_log import AuditLog
from .system_setting import SystemSetting

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
    'StaffShift',
    'DailyReport',
    'AuditLog',
    'SystemSetting',
] 