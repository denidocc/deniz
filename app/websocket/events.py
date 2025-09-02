"""Обработчики WebSocket событий."""

from flask import current_app, request
from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import decode_token
from . import socketio
from app.models import Order, WaiterCall, TableAssignment, Staff
from app import db
import logging

logger = current_app.logger if current_app else logging.getLogger(__name__)

@socketio.on('connect')
def handle_connect():
    """Обработка подключения клиента."""
    logger.info(f"Клиент подключился: {request.sid}")
    emit('connected', {'message': 'Подключение установлено'})

@socketio.on('disconnect')
def handle_disconnect():
    """Обработка отключения клиента."""
    logger.info(f"Клиент отключился: {request.sid}")

@socketio.on('join_waiter_room')
def handle_waiter_join(data):
    """Официант присоединяется к своей комнате."""
    try:
        waiter_id = data.get('waiter_id')
        if waiter_id:
            # Присоединяемся к личной комнате официанта
            join_room(f'waiter_{waiter_id}')
            
            # Также присоединяемся к общей комнате всех официантов
            join_room('all_waiters')
            
            emit('joined_room', {
                'message': f'Присоединились к комнате официанта {waiter_id}',
                'room': f'waiter_{waiter_id}'
            })
            
            current_app.logger.info(f"Waiter {waiter_id} joined rooms: waiter_{waiter_id}, all_waiters")
        else:
            emit('error', {'message': 'ID официанта не указан'})
            
    except Exception as e:
        current_app.logger.error(f"Error joining waiter room: {e}")
        emit('error', {'message': 'Ошибка присоединения к комнате'})

@socketio.on('leave_waiter_room')
def handle_leave_waiter_room(data):
    """Официант покидает свою комнату."""
    try:
        waiter_id = data.get('waiter_id')
        if waiter_id:
            room = f'waiter_{waiter_id}'
            leave_room(room)
            logger.info(f"Официант {waiter_id} покинул комнату {room}")
            emit('left_room', {'room': room})
    except Exception as e:
        logger.error(f"Ошибка при выходе из комнаты: {e}")

# Функции для отправки уведомлений (вызываются из других частей приложения)

def notify_new_order(order_id: int):
    """Уведомление официанта о новом заказе."""
    try:
        order = Order.query.get(order_id)
        if not order:
            logger.error(f"Заказ {order_id} не найден")
            return
        
        # Находим активное назначение стола
        assignment = TableAssignment.get_current_assignment(order.table_id)
        if not assignment or not assignment.is_active:
            logger.warning(f"Нет активного назначения для стола {order.table_id}")
            return
        
        waiter_id = assignment.waiter_id
        room = f'waiter_{waiter_id}'
        
        # Отправляем уведомление официанту
        socketio.emit('new_order', {
            'order_id': order.id,
            'table_id': order.table_id,
            'table_number': order.table.table_number if order.table else None,
            'guest_count': order.guest_count,
            'subtotal': float(order.subtotal),
            'total_amount': float(order.total_amount),
            'created_at': order.created_at.isoformat(),
            'message': f'Новый заказ со стола {order.table.table_number if order.table else "N/A"}',
            'sound': 'beep'  # Триггер для звукового уведомления
        }, room=room)
        
        logger.info(f"Уведомление о новом заказе {order_id} отправлено официанту {waiter_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления о новом заказе: {e}")

def notify_waiter_call(call_id: int):
    """Уведомление официанта о вызове."""
    try:
        call = WaiterCall.query.get(call_id)
        if not call:
            logger.error(f"Вызов {call_id} не найден")
            return
        
        # Находим активное назначение стола
        assignment = TableAssignment.get_current_assignment(call.table_id)
        if not assignment or not assignment.is_active:
            logger.warning(f"Нет активного назначения для стола {call.table_id}")
            return
        
        waiter_id = assignment.waiter_id
        room = f'waiter_{waiter_id}'
        
        # Отправляем уведомление официанту
        socketio.emit('waiter_call', {
            'call_id': call.id,
            'table_id': call.table_id,
            'table_number': call.table.table_number if call.table else None,
            'created_at': call.created_at.isoformat(),
            'message': f'Вызов официанта со стола {call.table.table_number if call.table else "N/A"}',
            'sound': 'beep'  # Триггер для звукового уведомления
        }, room=room)
        
        logger.info(f"Уведомление о вызове {call_id} отправлено официанту {waiter_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления о вызове: {e}")