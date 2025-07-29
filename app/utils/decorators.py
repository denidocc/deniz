"""Дополнительные декораторы."""

from functools import wraps
from flask import request, current_app, g
from flask_login import current_user
import time

def measure_time(f):
    """Декоратор для измерения времени выполнения."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        
        duration = end_time - start_time
        current_app.logger.info(
            f"Function {f.__name__} executed in {duration:.4f} seconds"
        )
        
        return result
    return decorated_function

def log_requests(f):
    """Декоратор для логирования запросов."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_app.logger.info(
            f"Request: {request.method} {request.path} "
            f"from {request.remote_addr}"
        )
        return f(*args, **kwargs)
    return decorated_function

def audit_action(action: str, table_affected: bool = False, order_affected: bool = False):
    """
    Декоратор для аудита действий персонала.
    
    Args:
        action: Название действия для логирования
        table_affected: Нужно ли логировать ID стола
        order_affected: Нужно ли логировать ID заказа
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Выполнение функции
                result = f(*args, **kwargs)
                
                # Логирование действия
                from app.models import AuditLog
                
                # Получение данных для логирования
                staff_id = current_user.id if current_user.is_authenticated else None
                ip_address = request.remote_addr
                
                # Извлечение ID стола и заказа из аргументов или результата
                table_id = None
                order_id = None
                
                if table_affected:
                    # Ищем table_id в аргументах
                    if 'table_id' in kwargs:
                        table_id = kwargs['table_id']
                    elif len(args) > 0 and hasattr(args[0], 'table_id'):
                        table_id = args[0].table_id
                    elif isinstance(result, dict) and 'table_id' in result:
                        table_id = result['table_id']
                
                if order_affected:
                    # Ищем order_id в аргументах
                    if 'order_id' in kwargs:
                        order_id = kwargs['order_id']
                    elif len(args) > 0 and hasattr(args[0], 'order_id'):
                        order_id = args[0].order_id
                    elif isinstance(result, dict) and 'order_id' in result:
                        order_id = result['order_id']
                
                # Дополнительные детали
                details = {
                    'endpoint': request.endpoint,
                    'method': request.method,
                    'url': request.url,
                    'user_agent': request.headers.get('User-Agent'),
                    'result_status': 'success'
                }
                
                # Добавляем результат если это словарь
                if isinstance(result, dict):
                    details['result'] = result
                
                # Создание записи аудита
                AuditLog.log_action(
                    action=action,
                    staff_id=staff_id,
                    table_affected=table_id,
                    order_affected=order_id,
                    details=details,
                    ip_address=ip_address
                )
                
                return result
                
            except Exception as e:
                # Логирование ошибки
                from app.models import AuditLog
                
                details = {
                    'endpoint': request.endpoint,
                    'method': request.method,
                    'url': request.url,
                    'error': str(e),
                    'result_status': 'error'
                }
                
                AuditLog.log_action(
                    action=f"{action}_error",
                    staff_id=current_user.id if current_user.is_authenticated else None,
                    details=details,
                    ip_address=request.remote_addr
                )
                
                raise
                
        return decorated_function
    return decorator

def with_transaction(f):
    """Декоратор для автоматического управления транзакциями."""
    from functools import wraps
    from sqlalchemy.exc import IntegrityError
    from app import db
    
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            db.session.commit()
            return result
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error in {f.__name__}: {str(e)}")
            if "unique constraint" in str(e):
                from app.errors import ValidationError
                raise ValidationError("Запись с такими данными уже существует")
            raise
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
            raise
    return decorated 