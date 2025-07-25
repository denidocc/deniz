"""Дополнительные декораторы."""

from functools import wraps
from flask import request, current_app
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