"""API модуль для REST endpoints."""

from .menu import menu_api
from .docs_endpoint import docs_api
from .system import system_api
from .audit import audit_api
from .bonus_cards import bonus_cards_bp as bonus_cards_api
from .table_settings import table_settings_api
from .carousel import carousel_api

__all__ = ['menu_api', 'docs_api', 'system_api', 'audit_api', 'bonus_cards_api', 'table_settings_api', 'carousel_api'] 