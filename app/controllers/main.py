"""Основной контроллер для главной страницы."""

from flask import Blueprint, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Главная страница - перенаправление на логин."""
    return redirect(url_for('auth.login')) 