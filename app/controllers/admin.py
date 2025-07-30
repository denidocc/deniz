"""Административные контроллеры."""

from flask import Blueprint, render_template
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Главная страница административной панели."""
    return render_template('admin/dashboard.html')

@admin_bp.route('/menu')
@admin_required
def menu():
    """Управление меню."""
    return render_template('admin/menu.html')

@admin_bp.route('/staff')
@admin_required
def staff():
    """Управление персоналом."""
    return render_template('admin/staff.html')

@admin_bp.route('/reports')
@admin_required
def reports():
    """Отчеты."""
    return render_template('admin/reports.html')

@admin_bp.route('/settings')
@admin_required
def settings():
    """Настройки системы."""
    return render_template('admin/settings.html') 