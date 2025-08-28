"""Контроллер интерфейса официанта."""

from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import current_user
from app.utils.decorators import waiter_required, audit_action
from app.models import Order, WaiterCall, Table
from app.models.order import Order as OrderModel
from app import db
from datetime import datetime
from flask_wtf.csrf import CSRFError

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



# API endpoints для dashboard
@waiter_bp.route('/api/dashboard/stats')
@waiter_required
def dashboard_stats():
    """Получение статистики для dashboard."""
    try:
        # Подсчитываем новые заказы для текущего официанта
        pending_orders = Order.query.filter_by(
            waiter_id=current_user.id,
            status='новый'
        ).count()
        
        # Подсчитываем активные вызовы для столов официанта
        from app.models import TableAssignment
        assigned_table_ids = db.session.query(TableAssignment.table_id).filter_by(
            waiter_id=current_user.id
        ).subquery()
        
        pending_calls = WaiterCall.query.filter(
            WaiterCall.table_id.in_(assigned_table_ids),
            WaiterCall.status == 'новый'
        ).count()
        
        # Подсчитываем назначенные столы
        assigned_tables = TableAssignment.query.filter_by(
            waiter_id=current_user.id,
            is_active=True
        ).count()

        # Получаем номера назначенных столов для отображения
        assigned_table_ids = db.session.query(TableAssignment.table_id).filter_by(
            waiter_id=current_user.id,
            is_active=True
        ).subquery()
        
        assigned_tables_data = Table.query.filter(
            Table.id.in_(assigned_table_ids)
        ).all()
        
        assigned_table_numbers = [table.table_number for table in assigned_tables_data]
        
        return jsonify({
            'status': 'success',
            'data': {
                'pending_orders': pending_orders,
                'pending_calls': pending_calls,
                'assigned_tables': assigned_tables,
                'assigned_table_numbers': assigned_table_numbers
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка получения статистики'
        }), 500







@waiter_bp.route('/api/calls')
@waiter_required
def get_calls():
    """Получение вызовов официанта."""
    try:
        # Получаем фильтры из параметров запроса
        status_filter = request.args.get('status')
        
        # Получаем назначенные столы для текущего официанта
        from app.models import TableAssignment
        assigned_table_ids = db.session.query(TableAssignment.table_id).filter_by(
            waiter_id=current_user.id
        ).subquery()
        
        # Базовый запрос вызовов только для назначенных столов
        query = WaiterCall.query.filter(
            WaiterCall.table_id.in_(assigned_table_ids)
        )
        
        # Применяем фильтр по статусу если указан
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        # Сортируем по времени создания (новые первыми)
        calls = query.order_by(WaiterCall.created_at.desc()).limit(50).all()
        
        current_app.logger.info(f"Found {len(calls)} calls for waiter {current_user.id}")
        current_app.logger.info(f"Call statuses: {[call.status for call in calls]}")
        
        # Формируем ответ
        calls_data = []
        for call in calls:
            calls_data.append({
                'id': call.id,
                'table_id': call.table_id,
                'table_number': call.table.table_number if call.table else None,
                'status': call.status,
                'priority': getattr(call, 'priority', 'средний'),  # Приоритет по умолчанию
                'message': getattr(call, 'message', 'Вызов официанта'),  # Сообщение по умолчанию
                'created_at': call.created_at.isoformat(),
                'responded_at': call.responded_at.isoformat() if call.responded_at else None,
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'calls': calls_data,
                'total': len(calls_data)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting calls: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка получения вызовов'
        }), 500

# API endpoints для заказов
@waiter_bp.route('/api/orders')
@waiter_required
def get_orders():
    """Получение заказов официанта."""
    try:
        current_app.logger.info(f"Getting orders for waiter: {current_user.id} ({current_user.name})")
        
        # Получаем параметры фильтрации
        status_filter = request.args.get('status')
        table_filter = request.args.get('table')
        current_app.logger.info(f"Filters - status: {status_filter}, table: {table_filter}")
        
        # Базовый запрос заказов для текущего официанта (исключаем отмененные)
        query = Order.query.filter_by(waiter_id=current_user.id).filter(
            Order.status != 'cancelled'
        )
        current_app.logger.info(f"Base query for waiter_id: {current_user.id}")
        
        # Применяем фильтры
        if status_filter and status_filter != 'all':
            query = query.filter_by(status=status_filter)
        
        if table_filter and table_filter != 'all':
            query = query.filter_by(table_id=int(table_filter))
        
        # Получаем заказы с join к таблице и правильной сортировкой
        orders = query.join(Table).order_by(
            # Сначала по времени создания (новые первыми)
            Order.created_at.desc()
        ).all()
        
        current_app.logger.info(f"Found {len(orders)} orders for waiter {current_user.id}")
        
        # Формируем данные ответа с группировкой
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'table_id': order.table_id,
                'table_number': order.table.table_number,
                'status': order.status,
                'guest_count': order.guest_count,
                'subtotal': float(order.subtotal),
                'service_charge': float(order.service_charge),
                'total_amount': float(order.total_amount),
                'comments': order.comments,
                'language': order.language,
                'created_at': order.created_at.isoformat(),
                'confirmed_at': order.confirmed_at.isoformat() if order.confirmed_at else None,
                'completed_at': order.completed_at.isoformat() if order.completed_at else None,
            })
        
        result = {
            'status': 'success',
            'data': {
                'orders': orders_data,
                'total': len(orders_data)
            }
        }
        current_app.logger.info(f"Returning {len(orders_data)} orders to waiter {current_user.id}")
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error getting orders: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка получения заказов'
        }), 500

@waiter_bp.route('/api/tables')
@waiter_required
def get_tables():
    """Получение столов официанта."""
    try:
        # Получаем столы, назначенные текущему официанту
        from app.models import TableAssignment
        
        assigned_table_ids = db.session.query(TableAssignment.table_id).filter_by(
            waiter_id=current_user.id,
            is_active=True
        ).subquery()
        
        assigned_tables = Table.query.filter(
            Table.id.in_(assigned_table_ids)
        ).order_by(Table.table_number).all()
        
        # Формируем данные ответа только для назначенных столов
        assigned_data = []
        for table in assigned_tables:
            # Принудительно обновляем статус стола из базы данных
            db.session.refresh(table)
            current_app.logger.info(f"Table {table.table_number} (ID: {table.id}) status: {table.status}")
            
            assigned_data.append({
                'id': table.id,
                'table_number': table.table_number,
                'capacity': table.capacity,
                'status': table.status,
                'is_active': table.is_active,
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'tables': assigned_data,
                'total': len(assigned_data)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting tables: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка получения столов'
        }), 500

@waiter_bp.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@waiter_required
def update_order_status(order_id):
    """Обновление статуса заказа."""
    try:
        # Получаем данные запроса
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Не указан новый статус'
            }), 400
        
        new_status = data['status']
        current_app.logger.info(f"Updating order {order_id} status to: '{new_status}'")
        
        # Проверяем допустимые статусы
        allowed_statuses = ['completed', 'confirmed']
        current_app.logger.info(f"Allowed statuses: {allowed_statuses}")
        current_app.logger.info(f"New status '{new_status}' in allowed: {new_status in allowed_statuses}")
        
        if new_status not in allowed_statuses:
            current_app.logger.error(f"Invalid status '{new_status}' for order {order_id}")
            return jsonify({
                'status': 'error',
                'message': f'Недопустимый статус. Разрешены: {", ".join(allowed_statuses)}'
            }), 400
        
        # Находим заказ
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'status': 'error',
                'message': 'Заказ не найден'
            }), 404
        
        # Проверяем права доступа (заказ должен быть назначен текущему официанту)
        if order.waiter_id != current_user.id:
            current_app.logger.warning(f"Waiter {current_user.id} tried to update order {order_id} assigned to waiter {order.waiter_id}")
            return jsonify({
                'status': 'error',
                'message': 'У вас нет прав для изменения этого заказа'
            }), 403
        
        # Логика изменения статуса
        old_status = order.status
        
        # Проверяем возможность перехода к новому статусу
        if not order.can_transition_to(new_status):
            return jsonify({
                'status': 'error',
                'message': f'Недопустимый переход статуса с "{old_status}" на "{new_status}"'
            }), 400
        
        # Изменяем статус заказа
        order.status = new_status
        
        # Устанавливаем соответствующие временные метки
        if new_status == 'completed':
            order.completed_at = datetime.utcnow()
            # При завершении заказа освобождаем стол
            if order.table:
                order.table.status = 'available'
        elif new_status == 'confirmed':
            order.confirmed_at = datetime.utcnow()
        
        # Сохраняем изменения
        db.session.commit()
        
        current_app.logger.info(f"Order {order_id} status changed from '{old_status}' to '{new_status}' by waiter {current_user.id}")
        
        return jsonify({
            'status': 'success',
            'message': f'Статус заказа изменен на "{new_status}"',
            'data': {
                'order_id': order.id,
                'old_status': old_status,
                'new_status': new_status,
                'updated_at': order.updated_at.isoformat() if order.updated_at else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating order status: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка изменения статуса заказа'
        }), 500 

@waiter_bp.route('/api/orders/<int:order_id>/print', methods=['POST'])
@waiter_required
@audit_action("print_order_receipts")
def print_order_receipts(order_id):
    """Печать чеков для заказа (кухня и бар)."""
    order = Order.query.get_or_404(order_id)
    
    # Проверяем, что заказ принадлежит текущему официанту
    if order.waiter_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'У вас нет прав для печати этого заказа'
        }), 403
    
    try:
        from app.utils.print_service import PrintService
        
        print_service = PrintService()
        
        # Разделяем позиции по типам приготовления
        kitchen_items = []
        bar_items = []
        
        for item in order.items:
            if item.menu_item.preparation_type == 'kitchen':
                kitchen_items.append(item)
            elif item.menu_item.preparation_type == 'bar':
                bar_items.append(item)
        
        # Печатаем чек на кухню
        kitchen_success = False
        if kitchen_items:
            kitchen_success = print_service.print_kitchen_receipt(order, kitchen_items)
        
        # Печатаем чек в бар
        bar_success = False
        if bar_items:
            bar_success = print_service.print_bar_receipt(order, bar_items)
        
        # Проверяем возможность перехода к статусу confirmed
        if not order.can_transition_to('confirmed'):
            return jsonify({
                'status': 'error',
                'message': 'Невозможно изменить статус заказа'
            }), 500
        
        # Обновляем статус заказа
        order.status = 'confirmed'
        order.confirmed_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Чеки отправлены на печать',
            'data': {
                'kitchen_printed': kitchen_success,
                'bar_printed': bar_success,
                'kitchen_items_count': len(kitchen_items),
                'bar_items_count': len(bar_items)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Print error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Ошибка печати: {str(e)}'
        }), 500

@waiter_bp.route('/api/orders/<int:order_id>')
@waiter_required
def get_order_details(order_id):
    """Получение деталей заказа."""
    order = Order.query.get_or_404(order_id)
    
    # Проверяем, что заказ принадлежит текущему официанту
    if order.waiter_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'У вас нет прав для просмотра этого заказа'
        }), 403
    
    # Подготавливаем данные заказа
    order_data = {
        'id': order.id,
        'table_number': order.table.table_number,
        'guest_count': order.guest_count,
        'status': order.status,
        'subtotal': float(order.subtotal),
        'service_charge': float(order.service_charge),
        'total_amount': float(order.total_amount),
        'discount_amount': float(order.discount_amount),
        'discount_percent': order.bonus_card.discount_percent if order.bonus_card else 0, 
        'created_at': order.created_at.isoformat(),
        'items': []
    }
    
    # ✅ Добавляем информацию о бонусной карте
    if order.bonus_card:
        order_data['bonus_card'] = {
            'card_number': order.bonus_card.card_number,
            'discount_percent': order.bonus_card.discount_percent
        }
    
    # Добавляем позиции заказа
    for item in order.items:
        item_data = {
            'id': item.id,
            'quantity': item.quantity,
            'name': item.menu_item.name_ru,
            'unit_price': float(item.unit_price),
            'total_price': float(item.total_price),
            'preparation_type': item.menu_item.preparation_type,
            'comments': item.comments
        }
        order_data['items'].append(item_data)
    
    return jsonify({
        'status': 'success',
        'data': {
            'order': order_data
        }
    })

@waiter_bp.route('/api/orders/<int:order_id>/print-final', methods=['POST'])
@waiter_required
@audit_action("print_final_receipt")
def print_final_receipt(order_id):
    """Печать финального чека для клиента."""
    order = Order.query.get_or_404(order_id)
    
    # Проверяем, что заказ принадлежит текущему официанту
    if order.waiter_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'У вас нет прав для печати этого заказа'
        }), 403
    
    try:
        from app.utils.print_service import PrintService
        
        print_service = PrintService()
        success = print_service.print_final_receipt(order)
        
        if success:
            # Проверяем возможность перехода к статусу completed
            if not order.can_transition_to('completed'):
                return jsonify({
                    'status': 'error',
                    'message': 'Невозможно изменить статус заказа'
                }), 500
            
            # Обновляем статус заказа
            order.status = 'completed'
            order.completed_at = datetime.now()
            db.session.commit()
        
        return jsonify({
            'status': 'success' if success else 'error',
            'message': 'Финальный чек напечатан' if success else 'Ошибка печати финального чека',
            'data': {
                'receipt_printed': success
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Final receipt print error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Ошибка печати финального чека: {str(e)}'
        }), 500

@waiter_bp.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
@waiter_required
def cancel_order(order_id):
    """Отмена заказа официантом."""
    try:
        from app.models.order import Order
        
        # Получаем заказ
        order = OrderModel.query.get(order_id)
        if not order:
            return jsonify({
                "status": "error",
                "message": "Заказ не найден"
            }), 404
        
        # Добавляем логирование для отладки
        current_app.logger.info(f"Cancel order {order_id}: status={order.status}, waiter_id={order.waiter_id}, current_user_id={current_user.id}")
        
        # Проверяем, что заказ принадлежит текущему официанту
        if order.waiter_id != current_user.id:
            current_app.logger.warning(f"Waiter {current_user.id} tried to cancel order {order_id} belonging to waiter {order.waiter_id}")
            return jsonify({
                "status": "error",
                "message": "У вас нет прав для отмены этого заказа"
            }), 403
        
        # Проверяем, что заказ еще не завершен или отменен
        if order.status in ['completed', 'cancelled']:
            current_app.logger.warning(f"Order {order_id} already in final status: {order.status}")
            return jsonify({
                "status": "error",
                "message": "Заказ уже завершен или отменен"
            }), 400
        
        # Проверяем возможность перехода к статусу cancelled
        status_info = order.get_status_info()
        current_app.logger.info(f"Order {order_id} status_info: {status_info}")
        
        if status_info:
            current_app.logger.info(f"Order {order_id} status_info.can_transition_to: {status_info.can_transition_to}")
            transition_targets = status_info.get_transition_targets()
            current_app.logger.info(f"Order {order_id} transition_targets: {transition_targets}")
        else:
            current_app.logger.warning(f"Order {order_id} has no status_info")
            transition_targets = []
        
        can_cancel = order.can_transition_to('cancelled')
        current_app.logger.info(f"Order {order_id} can_transition_to('cancelled'): {can_cancel}")
        
        if not can_cancel:
            current_app.logger.warning(f"Order {order_id} cannot transition to cancelled from status {order.status}")
            return jsonify({
                "status": "error",
                "message": "Невозможно отменить заказ в текущем статусе"
            }), 400
        
        # Изменяем статус заказа на "отменен"
        order.status = 'cancelled'
        order.cancelled_at = datetime.utcnow()
        
        # Получаем стол
        table = order.table
        if table:
            # Изменяем статус стола на "свободен"
            table.status = 'available'
        
        # Сохраняем изменения
        db.session.commit()
        
        # Логирование действия
        current_app.logger.info(f"Order {order.id} cancelled by waiter {current_user.id} for table {table.table_number if table else 'unknown'}")
        
        current_app.logger.info(f"Order {order_id} cancelled by waiter {current_user.id}")
        
        return jsonify({
            "status": "success",
            "message": "Заказ успешно отменен",
            "data": {
                'order_id': order.id,
                'table_id': table.id if table else None,
                'table_number': table.table_number if table else None,
                'status': order.status,
                'cancelled_at': order.cancelled_at.isoformat()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error cancelling order: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка отмены заказа"
        }), 500 

@waiter_bp.route('/api/order-statuses', methods=['GET'])
@waiter_required
def get_order_statuses():
    """Получение справочника статусов заказов."""
    try:
        from app.models.c_order_status import C_OrderStatus
        statuses = C_OrderStatus.get_active()
        
        statuses_data = []
        for status in statuses:
            statuses_data.append({
                'id': status.id,
                'code': status.code,
                'name': status.name,
                'description': status.description,
                'color': status.color,
                'icon': status.icon,
                'sort_order': status.sort_order,
                'can_transition_to': status.get_transition_targets()
            })
        
        current_app.logger.info(f"Found {len(statuses)} order statuses")
        return jsonify({
            "status": "success",
            "data": statuses_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting order statuses: {e}")
        return jsonify({"status": "error", "message": "Ошибка получения статусов"}), 500 

@waiter_bp.route('/api/counters')
@waiter_required
def get_counters():
    """Получение актуальных счетчиков для официанта."""
    try:
        # Подсчитываем новые заказы для текущего официанта
        pending_orders = Order.query.filter_by(
            waiter_id=current_user.id,
            status='новый'
        ).count()
        
        # Подсчитываем активные вызовы для столов официанта
        from app.models import TableAssignment
        assigned_table_ids = db.session.query(TableAssignment.table_id).filter_by(
            waiter_id=current_user.id
        ).subquery()
        
        pending_calls = WaiterCall.query.filter(
            WaiterCall.table_id.in_(assigned_table_ids),
            WaiterCall.status == 'pending'
        ).count()
        
        # Подсчитываем назначенные столы
        assigned_tables = TableAssignment.query.filter_by(
            waiter_id=current_user.id,
            is_active=True
        ).count()
        
        return jsonify({
            'status': 'success',
            'data': {
                'pending_orders': pending_orders,
                'pending_calls': pending_calls,
                'assigned_tables': assigned_tables
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting counters: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка получения счетчиков'
        }), 500 

@waiter_bp.route('/api/calls/<int:call_id>/mark-read', methods=['POST'])
@waiter_required
def mark_call_as_read(call_id):
    """Отметить вызов официанта как прочитанный."""
    try:
        call = WaiterCall.query.get_or_404(call_id)
        
        # Проверяем, что вызов относится к столу официанта
        from app.models import TableAssignment
        is_assigned = TableAssignment.query.filter_by(
            table_id=call.table_id,
            waiter_id=current_user.id,
            is_active=True
        ).first()
        
        if not is_assigned:
            return jsonify({
                'status': 'error',
                'message': 'Вызов не относится к вашему столу'
            }), 403
        
        # Обновляем статус
        call.status = 'completed'
        call.completed_at = datetime.utcnow()
        call.completed_by = current_user.id
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Вызов отмечен как прочитанный'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error marking call as read: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка обновления статуса'
        }), 500 