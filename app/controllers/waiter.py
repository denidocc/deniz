"""Контроллер интерфейса официанта."""

from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import current_user
from app.utils.decorators import waiter_required
from app.models import Order, WaiterCall, Table, StaffShift
from app import db

waiter_bp = Blueprint('waiter', __name__)

@waiter_bp.route('/dashboard')
@waiter_required
def dashboard():
    """Dashboard официанта."""
    return render_template('waiter/dashboard.html')

@waiter_bp.route('/orders')
@waiter_required
def orders():
    """Список заказов официанта."""
    return render_template('waiter/orders.html')

@waiter_bp.route('/tables')
@waiter_required
def tables():
    """Управление столами официанта."""
    return render_template('waiter/tables.html')

@waiter_bp.route('/calls')
@waiter_required
def calls():
    """Вызовы официанта."""
    return render_template('waiter/calls.html')

@waiter_bp.route('/shift')
@waiter_required
def shift():
    """Управление сменой."""
    return render_template('waiter/shift.html')

# API endpoints для dashboard
@waiter_bp.route('/api/dashboard/stats')
@waiter_required
def dashboard_stats():
    """Получение статистики для dashboard."""
    try:
        # Проверка активной смены
        active_shift = StaffShift.query.filter_by(
            staff_id=current_user.id,
            is_active=True
        ).first()
        
        if not active_shift:
            return jsonify({
                'status': 'success',
                'data': {
                    'has_active_shift': False,
                    'pending_orders': 0,
                    'pending_calls': 0,
                    'assigned_tables': 0
                }
            })
        
        # Получение статистики
        # TODO: Реализовать подсчет заказов и вызовов для закрепленных столов
        pending_orders = 0
        pending_calls = 0
        assigned_tables = 0
        
        return jsonify({
            'status': 'success',
            'data': {
                'has_active_shift': True,
                'shift_start': active_shift.shift_start.isoformat(),
                'pending_orders': pending_orders,
                'pending_calls': pending_calls,
                'assigned_tables': assigned_tables,
                'total_orders': active_shift.total_orders,
                'total_revenue': float(active_shift.total_revenue)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка получения статистики'
        }), 500 