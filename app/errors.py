"""Обработка ошибок приложения."""

from flask import Flask, request, jsonify, render_template, current_app
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError
import logging

class ValidationError(Exception):
    """Кастомное исключение для ошибок валидации."""
    
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(self.message)

class BusinessLogicError(Exception):
    """Исключение для ошибок бизнес-логики."""
    
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

class AuthenticationError(Exception):
    """Исключение для ошибок аутентификации."""
    pass

class AuthorizationError(Exception):
    """Исключение для ошибок авторизации."""
    pass

class OrderError(Exception):
    """Исключение для ошибок заказов."""
    pass

def is_api_request() -> bool:
    """Проверка, является ли запрос API запросом."""
    return (
        request.path.startswith('/app/') or 
        request.headers.get('Accept', '').startswith('application/json') or
        request.headers.get('Content-Type', '').startswith('application/json')
    )

def api_error_response(message: str, status_code: int = 400, 
                      errors: dict = None, code: str = None):
    """Стандартный формат ошибки для API."""
    response = {
        "status": "error",
        "message": message,
        "data": {}
    }
    
    if errors:
        response["errors"] = errors
    if code:
        response["code"] = code
        
    return jsonify(response), status_code

def register_error_handlers(app: Flask) -> None:
    """Регистрация обработчиков ошибок."""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(e: ValidationError):
        """Обработка ошибок валидации."""
        if is_api_request():
            errors = {e.field: e.message} if e.field else None
            return api_error_response(
                message=e.message,
                status_code=400,
                errors=errors,
                code=e.code
            )
        else:
            return render_template('errors/400.html', error=e.message), 400
    
    @app.errorhandler(BusinessLogicError)
    def handle_business_logic_error(e: BusinessLogicError):
        """Обработка ошибок бизнес-логики."""
        if is_api_request():
            return api_error_response(
                message=e.message,
                status_code=422,
                code=e.code
            )
        else:
            return render_template('errors/422.html', error=e.message), 422
    
    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(e: AuthenticationError):
        """Обработка ошибок аутентификации."""
        if is_api_request():
            return api_error_response(
                message=str(e),
                status_code=401
            )
        else:
            return render_template('errors/401.html'), 401
    
    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(e: AuthorizationError):
        """Обработка ошибок авторизации."""
        if is_api_request():
            return api_error_response(
                message=str(e),
                status_code=403
            )
        else:
            return render_template('errors/403.html'), 403
    
    @app.errorhandler(OrderError)
    def handle_order_error(e: OrderError):
        """Обработка ошибок заказов."""
        if is_api_request():
            return api_error_response(
                message=str(e),
                status_code=400
            )
        else:
            return render_template('errors/400.html', error=str(e)), 400
    
    @app.errorhandler(IntegrityError)
    def handle_integrity_error(e: IntegrityError):
        """Обработка ошибок целостности БД."""
        app.logger.error(f"Database integrity error: {str(e)}")
        
        message = "Данные не могут быть сохранены из-за конфликта"
        if "unique constraint" in str(e):
            message = "Запись с такими данными уже существует"
        elif "foreign key constraint" in str(e):
            message = "Связанная запись не найдена"
            
        if is_api_request():
            return api_error_response(message=message, status_code=409)
        else:
            return render_template('errors/409.html', error=message), 409
    
    @app.errorhandler(404)
    def handle_not_found(e):
        """Обработка 404 ошибок."""
        if is_api_request():
            return api_error_response(
                message="Ресурс не найден",
                status_code=404
            )
        else:
            return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def handle_internal_error(e):
        """Обработка внутренних ошибок сервера."""
        app.logger.error(f"Internal server error: {str(e)}", exc_info=True)
        
        if is_api_request():
            return api_error_response(
                message="Внутренняя ошибка сервера",
                status_code=500
            )
        else:
            return render_template('errors/500.html'), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        """Обработка HTTP исключений."""
        if is_api_request():
            return api_error_response(
                message=e.description or "HTTP ошибка",
                status_code=e.code
            )
        else:
            template = f'errors/{e.code}.html'
            try:
                return render_template(template), e.code
            except:
                return render_template('errors/generic.html', 
                                     error=e.description), e.code 