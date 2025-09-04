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

@socketio.on('join_client_room')
def handle_client_join():
    """Клиент присоединяется к общей комнате клиентов."""
    try:
        # Присоединяемся к общей комнате всех клиентов
        join_room('all_clients')
        
        emit('joined_client_room', {
            'message': 'Присоединились к клиентской комнате',
            'room': 'all_clients'
        })
        
        current_app.logger.info("Client joined room: all_clients")
        
    except Exception as e:
        current_app.logger.error(f"Error in handle_client_join: {e}")
        emit('error', {'message': 'Ошибка присоединения к комнате'})

def broadcast_content_update(content_type: str, action: str, message: str = None):
    """
    Универсальная функция для уведомления клиентов об обновлениях контента.
    
    Args:
        content_type: Тип контента ('menu', 'category', 'banner', 'settings')
        action: Действие ('create', 'update', 'delete')
        message: Дополнительное сообщение
    """
    try:
        if not message:
            action_names = {
                'create': 'создан',
                'update': 'обновлен', 
                'delete': 'удален'
            }
            type_names = {
                'menu': 'Элемент меню',
                'category': 'Категория',
                'banner': 'Баннер',
                'settings': 'Настройки'
            }
            
            message = f"{type_names.get(content_type, 'Контент')} {action_names.get(action, 'изменен')}"
        
        # Отправляем уведомление всем клиентам
        socketio.emit('content_updated', {
            'type': content_type,
            'action': action,
            'message': message,
            'timestamp': current_app.logger.handlers[0].formatter.formatTime(
                logging.LogRecord('', 0, '', 0, '', (), None)
            ) if current_app.logger.handlers else None
        }, room='all_clients')
        
        current_app.logger.info(f"Content update broadcasted: {content_type} - {action} - {message}")
        
    except Exception as e:
        current_app.logger.error(f"Error broadcasting content update: {e}")