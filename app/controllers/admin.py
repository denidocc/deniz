"""Контроллер административной панели."""

from flask import Blueprint, render_template, current_app
from app.controllers.auth import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Главная страница администратора."""
    return render_template('admin/dashboard.html')

@admin_bp.route('/menu')
@admin_required
def menu_management():
    """Управление меню."""
    return render_template('admin/menu.html')

@admin_bp.route('/staff')
@admin_required
def staff_management():
    """Управление персоналом."""
    return render_template('admin/staff.html')

@admin_bp.route('/reports')
@admin_required
def reports():
    """Отчеты и статистика."""
    return render_template('admin/reports.html')

@admin_bp.route('/settings')
@admin_required
def settings():
    """Настройки системы."""
    return render_template('admin/settings.html') 