"""Middleware для автоматического аудита всех действий."""

from flask import request, g, current_app
from flask_login import current_user
import json
import time
from typing import Dict, Any, Optional

class AuditMiddleware:
    """Middleware для автоматического логирования всех действий в системе."""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Инициализация middleware."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_request)
    
    def before_request(self):
        """Действия перед обработкой запроса."""
        try:
            g.start_time = time.time()
            g.request_data = {
                'method': request.method,
                'url': request.url,
                'endpoint': request.endpoint,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'referrer': request.headers.get('Referer'),
                'content_type': request.content_type,
                'content_length': request.content_length
            }
        except Exception as e:
            current_app.logger.error(f"Audit before_request error: {e}")
            # Устанавливаем минимальные данные
            g.start_time = time.time()
            g.request_data = {}
        
        try:
            # Логируем параметры запроса (без паролей)
            if request.args:
                g.request_data['query_params'] = dict(request.args)
            
            # Логируем JSON данные (без паролей)
            if request.is_json:
                try:
                    json_data = request.get_json(silent=True)
                    if json_data:
                        json_data = dict(json_data)
                        # Удаляем чувствительные данные
                        for sensitive_field in ['password', 'password_hash', 'token', 'secret']:
                            if sensitive_field in json_data:
                                json_data[sensitive_field] = '[FILTERED]'
                        g.request_data['json_data'] = json_data
                except Exception as e:
                    # Игнорируем ошибки парсинга JSON
                    current_app.logger.debug(f"JSON parsing failed: {e}")
            
            # Логируем форм-данные (без паролей)
            if request.form:
                form_data = dict(request.form)
                for sensitive_field in ['password', 'password_hash', 'token', 'secret']:
                    if sensitive_field in form_data:
                        form_data[sensitive_field] = '[FILTERED]'
                    g.request_data['form_data'] = form_data
        except Exception as e:
            current_app.logger.error(f"Audit data collection error: {e}")
    
    def after_request(self, response):
        """Действия после обработки запроса."""
        try:
            if not hasattr(g, 'start_time'):
                return response
            
            # Вычисляем время выполнения
            duration = time.time() - g.start_time
            
            # Определяем тип действия на основе endpoint и метода
            action = self.determine_action(request.endpoint, request.method, response.status_code)
            
            # Логируем только важные действия
            if self.should_log_action(action, request.endpoint, response.status_code):
                self.log_request_action(action, response, duration)
        except Exception as e:
            current_app.logger.error(f"Audit after_request error: {e}")
        
        return response
    
    def teardown_request(self, exception=None):
        """Очистка после запроса."""
        if exception:
            # Логируем исключения
            self.log_exception(exception)
    
    def determine_action(self, endpoint: str, method: str, status_code: int) -> str:
        """Определяет тип действия на основе endpoint и метода."""
        if not endpoint:
            return f"{method}_unknown_endpoint"
        
        # Мапим endpoint на действия
        action_map = {
            # Аутентификация
            'auth.login': 'user_login',
            'auth.logout': 'user_logout',
            
            # Заказы
            'orders.create': 'order_create',
            'orders.confirm': 'order_confirm', 
            'orders.complete': 'order_complete',
            'orders.cancel': 'order_cancel',
            
            # Столы
            'tables.assign': 'table_assign',
            'tables.release': 'table_release',
            'tables.status': 'table_status_check',
            
            # Меню
            'menu.create': 'menu_item_create',
            'menu.update': 'menu_item_update',
            'menu.delete': 'menu_item_delete',
            'menu.get': 'menu_view',
            
            # Смены
            'shifts.start': 'shift_start',
            'shifts.end': 'shift_end',
            
            # Печать
            'print.kitchen': 'print_kitchen_order',
            'print.bar': 'print_bar_order',
            'print.receipt': 'print_receipt',
            
            # Админка
            'admin.dashboard': 'admin_dashboard_view',
            'admin.reports': 'admin_reports_view',
            'admin.settings': 'admin_settings_view',
            
            # Официанты
            'waiter.dashboard': 'waiter_dashboard_view',
            'waiter.calls': 'waiter_calls_view',
        }
        
        base_action = action_map.get(endpoint, endpoint.replace('.', '_'))
        
        # Добавляем суффикс на основе статуса
        if status_code >= 400:
            base_action += '_error'
        elif method in ['POST', 'PUT', 'PATCH']:
            base_action += '_modify'
        elif method == 'DELETE':
            base_action += '_delete'
        elif method == 'GET':
            base_action += '_view'
        
        return base_action
    
    def should_log_action(self, action: str, endpoint: str, status_code: int) -> bool:
        """Определяет, нужно ли логировать действие."""
        # Всегда логируем ошибки
        if status_code >= 400:
            return True
        
        # Исключаем статические файлы, healthcheck и waiter API
        excluded_endpoints = [
            'static',
            'health',
            'favicon.ico',
            'waiter.dashboard_stats',
            'waiter.shift_info',
            'waiter.start_shift',
            'waiter.end_shift'
        ]
        
        # Также исключаем по URL пути
        if request.path and any(path in request.path for path in ['/api/dashboard', '/api/shift']):
            return False
        
        if endpoint and any(excl in endpoint for excl in excluded_endpoints):
            return False
        
        # Логируем только важные действия
        important_actions = [
            'user_login', 'user_logout',
            'order_create', 'order_confirm', 'order_complete', 'order_cancel',
            'table_assign', 'table_release',
            'menu_item_create', 'menu_item_update', 'menu_item_delete',
            'shift_start', 'shift_end',
            'print_kitchen_order', 'print_bar_order', 'print_receipt',
            'admin_', 'waiter_'  # Все админские и официантские действия
        ]
        
        return any(important in action for important in important_actions)
    
    def log_request_action(self, action: str, response, duration: float):
        """Логирует действие запроса."""
        try:
            from app.models import AuditLog
            
            # Собираем детали (безопасно получаем request_data)
            request_data = getattr(g, 'request_data', {})
            details = {
                **request_data,
                'duration_seconds': round(duration, 4),
                'response_status': response.status_code,
                'response_size': len(response.get_data()) if hasattr(response, 'get_data') else None,
            }
            
            # Добавляем информацию о пользователе
            if current_user.is_authenticated:
                details['user_info'] = {
                    'id': current_user.id,
                    'login': current_user.login,
                    'name': current_user.name,
                    'role': current_user.role
                }
            
            # Извлекаем ID стола и заказа из URL или данных
            table_id = self.extract_table_id()
            order_id = self.extract_order_id()
            
            # Создаем запись аудита
            AuditLog.log_action(
                action=action,
                staff_id=current_user.id if current_user.is_authenticated else None,
                table_affected=table_id,
                order_affected=order_id,
                details=details,
                ip_address=request.remote_addr
            )
            
        except Exception as e:
            # Если не можем записать аудит, логируем в обычный лог
            import traceback
            current_app.logger.error(f"Failed to log audit action '{action}': {e}")
            current_app.logger.error(f"Audit error traceback: {traceback.format_exc()}")
    
    def log_exception(self, exception):
        """Логирует исключения."""
        try:
            from app.models import AuditLog
            
            # Безопасно получаем request_data
            request_data = getattr(g, 'request_data', {})
            details = {
                **request_data,
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'traceback': self.get_traceback_string(exception)
            }
            
            AuditLog.log_action(
                action='system_exception',
                staff_id=current_user.id if current_user.is_authenticated else None,
                details=details,
                ip_address=request.remote_addr
            )
            
        except Exception as e:
            current_app.logger.error(f"Failed to log exception: {e}")
    
    def extract_table_id(self) -> Optional[int]:
        """Извлекает ID стола из запроса."""
        # Проверяем URL параметры
        if request.view_args and 'table_id' in request.view_args:
            return request.view_args['table_id']
        
        # Проверяем query параметры
        if request.args.get('table_id'):
            try:
                return int(request.args.get('table_id'))
            except (ValueError, TypeError):
                pass
        
        # Проверяем JSON данные
        try:
            json_data = request.get_json(silent=True)
            if json_data and 'table_id' in json_data:
                return int(json_data['table_id'])
        except (ValueError, TypeError, AttributeError):
            pass
        
        # Проверяем форм данные
        if request.form.get('table_id'):
            try:
                return int(request.form.get('table_id'))
            except (ValueError, TypeError):
                pass
        
        return None
    
    def extract_order_id(self) -> Optional[int]:
        """Извлекает ID заказа из запроса."""
        # Проверяем URL параметры
        if request.view_args and 'order_id' in request.view_args:
            return request.view_args['order_id']
        
        # Проверяем query параметры
        if request.args.get('order_id'):
            try:
                return int(request.args.get('order_id'))
            except (ValueError, TypeError):
                pass
        
        # Проверяем JSON данные
        try:
            json_data = request.get_json(silent=True)
            if json_data and 'order_id' in json_data:
                return int(json_data['order_id'])
        except (ValueError, TypeError, AttributeError):
            pass
        
        # Проверяем форм данные
        if request.form.get('order_id'):
            try:
                return int(request.form.get('order_id'))
            except (ValueError, TypeError):
                pass
        
        return None
    
    def get_traceback_string(self, exception) -> str:
        """Получает строковое представление traceback."""
        import traceback
        return traceback.format_exc()


# Глобальный экземпляр
audit_middleware = AuditMiddleware() 