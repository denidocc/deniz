"""Основной контроллер для главной страницы."""

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Главная страница приложения."""
    return render_template('main/index.html')

@main_bp.route('/about')
def about():
    """Страница о системе."""
    return render_template('main/about.html') 