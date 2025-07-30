"""API для просмотра логов аудита."""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from app.models import AuditLog, Staff
from app.utils.decorators import audit_action, admin_required
from app.errors import ValidationError
from datetime import datetime, timedelta
from typing import Dict, Any
import json

audit_api = Blueprint('audit', __name__)

@audit_api.route('/logs', methods=['GET'])
@login_required
@admin_required
@audit_action("view_audit_logs")
def get_audit_logs():
    """Получение логов аудита с фильтрацией."""
    try:
        # Параметры фильтрации
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        staff_id = request.args.get('staff_id', type=int)
        action = request.args.get('action')
        table_id = request.args.get('table_id', type=int)
        order_id = request.args.get('order_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Построение запроса
        query = AuditLog.query
        
        # Фильтры
        if staff_id:
            query = query.filter_by(staff_id=staff_id)
        if action:
            query = query.filter(AuditLog.action.contains(action))
        if table_id:
            query = query.filter_by(table_affected=table_id)
        if order_id:
            query = query.filter_by(order_affected=order_id)
        
        # Фильтр по датам
        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                query = query.filter(AuditLog.created_at >= from_date)
            except ValueError:
                raise ValidationError("Неверный формат даты в date_from")
        
        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                query = query.filter(AuditLog.created_at <= to_date)
            except ValueError:
                raise ValidationError("Неверный формат даты в date_to")
        
        # Сортировка и пагинация
        logs = query.order_by(AuditLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Подготовка данных
        logs_data = []
        for log in logs.items:
            log_data = log.to_dict()
            logs_data.append(log_data)
        
        return jsonify({
            "status": "success",
            "data": {
                "logs": logs_data,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": logs.total,
                    "pages": logs.pages,
                    "has_next": logs.has_next,
                    "has_prev": logs.has_prev
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting audit logs: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка при получении логов аудита"
        }), 500

@audit_api.route('/logs/recent', methods=['GET'])
@login_required
@admin_required
@audit_action("view_recent_logs")
def get_recent_logs():
    """Получение последних логов."""
    try:
        limit = min(request.args.get('limit', 20, type=int), 100)
        logs = AuditLog.get_recent_logs(limit=limit)
        
        logs_data = [log.to_dict() for log in logs]
        
        return jsonify({
            "status": "success",
            "data": {
                "logs": logs_data,
                "count": len(logs_data)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting recent logs: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка при получении последних логов"
        }), 500

@audit_api.route('/logs/staff/<int:staff_id>', methods=['GET'])
@login_required
@admin_required
@audit_action("view_staff_logs")
def get_staff_logs(staff_id):
    """Получение логов сотрудника."""
    try:
        limit = min(request.args.get('limit', 20, type=int), 100)
        
        # Проверяем существование сотрудника
        staff = Staff.query.get(staff_id)
        if not staff:
            return jsonify({
                "status": "error",
                "message": "Сотрудник не найден"
            }), 404
        
        logs = AuditLog.get_by_staff(staff_id, limit)
        logs_data = [log.to_dict() for log in logs]
        
        return jsonify({
            "status": "success",
            "data": {
                "staff": {
                    "id": staff.id,
                    "name": staff.name,
                    "login": staff.login,
                    "role": staff.role
                },
                "logs": logs_data,
                "count": len(logs_data)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting staff logs: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка при получении логов сотрудника"
        }), 500

@audit_api.route('/logs/table/<int:table_id>', methods=['GET'])
@login_required
@admin_required
@audit_action("view_table_logs", table_affected=True)
def get_table_logs(table_id):
    """Получение логов по столу."""
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        # Проверяем существование стола
        from app.models import Table
        table = Table.query.get(table_id)
        if not table:
            return jsonify({
                "status": "error",
                "message": "Стол не найден"
            }), 404
        
        logs = AuditLog.get_by_table(table_id, limit)
        logs_data = [log.to_dict() for log in logs]
        
        return jsonify({
            "status": "success",
            "data": {
                "table": {
                    "id": table.id,
                    "table_number": table.table_number,
                    "status": table.status
                },
                "logs": logs_data,
                "count": len(logs_data)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting table logs: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка при получении логов стола"
        }), 500

@audit_api.route('/logs/order/<int:order_id>', methods=['GET'])
@login_required
@admin_required
@audit_action("view_order_logs", order_affected=True)
def get_order_logs(order_id):
    """Получение логов по заказу."""
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        # Проверяем существование заказа
        from app.models import Order
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                "status": "error",
                "message": "Заказ не найден"
            }), 404
        
        logs = AuditLog.get_by_order(order_id, limit)
        logs_data = [log.to_dict() for log in logs]
        
        return jsonify({
            "status": "success",
            "data": {
                "order": {
                    "id": order.id,
                    "table_id": order.table_id,
                    "table_number": order.table.table_number if order.table else None,
                    "status": order.status,
                    "total_amount": float(order.total_amount),
                    "guest_count": order.guest_count,
                    "created_at": order.created_at.isoformat()
                },
                "logs": logs_data,
                "count": len(logs_data)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting order logs: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка при получении логов заказа"
        }), 500

@audit_api.route('/logs/date-range', methods=['GET'])
@login_required
@admin_required
@audit_action("view_logs_by_date_range")
def get_logs_by_date_range():
    """Получение логов за период."""
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = min(request.args.get('limit', 100, type=int), 500)
        
        if not date_from or not date_to:
            raise ValidationError("Необходимо указать date_from и date_to")
        
        # Парсим даты
        try:
            start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError("Неверный формат даты. Используйте ISO формат")
        
        if start_date >= end_date:
            raise ValidationError("Дата начала должна быть раньше даты окончания")
        
        logs = AuditLog.get_logs_by_date_range(start_date, end_date)
        
        # Ограничиваем количество
        logs = logs[:limit]
        logs_data = [log.to_dict() for log in logs]
        
        return jsonify({
            "status": "success",
            "data": {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "logs": logs_data,
                "count": len(logs_data),
                "limited": len(logs_data) == limit
            }
        })
        
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error getting logs by date range: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка при получении логов за период"
        }), 500

@audit_api.route('/statistics', methods=['GET'])
@login_required
@admin_required
@audit_action("view_audit_stats")
def get_audit_stats():
    """Получение статистики аудита."""
    try:
        # Параметры
        days = request.args.get('days', 7, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Статистика по действиям
        from sqlalchemy import func
        from app import db
        action_stats = db.session.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        ).group_by(AuditLog.action).all()
        
        # Статистика по сотрудникам
        staff_stats = db.session.query(
            AuditLog.staff_id,
            Staff.name,
            func.count(AuditLog.id).label('count')
        ).join(Staff).filter(
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        ).group_by(AuditLog.staff_id, Staff.name).all()
        
        # Общая статистика
        total_logs = AuditLog.query.filter(
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        ).count()
        
        return jsonify({
            "status": "success",
            "data": {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "total_logs": total_logs,
                "action_stats": [
                    {"action": action, "count": count}
                    for action, count in action_stats
                ],
                "staff_stats": [
                    {"staff_id": staff_id, "name": name, "count": count}
                    for staff_id, name, count in staff_stats
                ]
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting audit stats: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка при получении статистики аудита"
        }), 500 