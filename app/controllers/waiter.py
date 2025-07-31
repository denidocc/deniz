"""Контроллер интерфейса официанта."""

from flask import Blueprint, render_template, current_app
from app.utils.decorators import waiter_required

waiter_bp = Blueprint('waiter', __name__)

@waiter_bp.route('/dashboard')
@waiter_required
def dashboard():
    """Главная страница официанта."""
    return render_template('waiter/dashboard.html')

@waiter_bp.route('/orders')
@waiter_required
def orders():
    """Управление заказами."""
    return render_template('waiter/orders.html')

@waiter_bp.route('/tables')
@waiter_required
def tables():
    """Управление столами."""
    return render_template('waiter/tables.html')

@waiter_bp.route('/shift')
@waiter_required
def shift_management():
    """Управление сменой."""
    return render_template('waiter/shift.html') 