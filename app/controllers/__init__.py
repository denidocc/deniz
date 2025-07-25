"""Импорт blueprints для веб-интерфейса."""

from .auth import auth_bp
from .admin import admin_bp
from .waiter import waiter_bp
from .main import main_bp

__all__ = [
    'auth_bp',
    'admin_bp', 
    'waiter_bp',
    'main_bp',
] 