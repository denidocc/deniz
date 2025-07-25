"""API модуль для REST endpoints."""

from .menu import menu_api
from .docs_endpoint import docs_api

__all__ = ['menu_api', 'docs_api'] 