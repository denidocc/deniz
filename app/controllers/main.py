"""Основной контроллер для главной страницы."""

from flask import Blueprint, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Главная страница - клиентское меню."""
    return redirect(url_for('client.index'))

@main_bp.route('/admin')
def admin_login():
    """Вход для персонала."""
    return redirect(url_for('auth.login')) 