"""Контроллер интерфейса официанта."""

from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import current_user
from app.utils.decorators import waiter_required
from app.models import Order, WaiterCall, Table
from app import db
from datetime import datetime
from app.utils.decorators import audit_action

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
        
        # Формируем ответ
        calls_data = []
        for call in calls:
            calls_data.append({
                'id': call.id,
                'table_id': call.table_id,
                'table_number': call.table.table_number if call.table else None,
                'status': call.status,
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
        
        # Базовый запрос заказов для текущего официанта
        query = Order.query.filter_by(waiter_id=current_user.id)
        current_app.logger.info(f"Base query for waiter_id: {current_user.id}")
        
        # Применяем фильтры
        if status_filter and status_filter != 'all':
            query = query.filter_by(status=status_filter)
        
        if table_filter and table_filter != 'all':
            query = query.filter_by(table_id=int(table_filter))
        
        # Получаем заказы с join к таблице
        orders = query.join(Table).all()
        current_app.logger.info(f"Found {len(orders)} orders for waiter {current_user.id}")
        
        # Формируем данные ответа
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
        ).all()
        
        # Формируем данные ответа только для назначенных столов
        assigned_data = []
        for table in assigned_tables:
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
        
        # Проверяем допустимые статусы
        allowed_statuses = ['новый', 'оплачен']
        if new_status not in allowed_statuses:
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
        
        # Только разрешенные переходы статусов
        if old_status == 'новый' and new_status == 'оплачен':
            order.status = new_status
            if new_status == 'оплачен':
                from datetime import datetime
                order.completed_at = datetime.utcnow()
        elif old_status == new_status:
            return jsonify({
                'status': 'info',
                'message': f'Заказ уже имеет статус "{new_status}"'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Недопустимый переход статуса с "{old_status}" на "{new_status}"'
            }), 400
        
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
        'created_at': order.created_at.isoformat(),
        'items': []
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