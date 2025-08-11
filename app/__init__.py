"""Инициализация Flask приложения."""

from flask import Flask, g, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_babel import Babel
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

# Инициализация расширений
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
jwt = JWTManager()
cache = Cache()
babel = Babel()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"]
)

def create_app(config_name: str = 'development') -> Flask:
    """
    Фабрика приложений Flask.
    
    Args:
        config_name: Название конфигурации ('development', 'testing', 'production')
        
    Returns:
        Flask: Настроенное приложение Flask
    """
    app = Flask(__name__)
    
    # Загрузка конфигурации
    from config import get_config
    app.config.from_object(get_config(config_name))
    
    # Инициализация расширений
    init_extensions(app)
    
    # Настройка логирования
    setup_logging(app)
    
    # Инициализация системы аудита
    init_audit_system(app)
    
    # Регистрация CLI команд аудита
    register_audit_commands(app)
    
    # Регистрация blueprints
    register_blueprints(app)
    
    # Обработчики ошибок
    register_error_handlers(app)
    
    # Инициализация системных компонентов
    init_system_components(app)
    
    # Инициализация системы безопасности
    init_security_components(app)
    
    # Добавляем маршрут для favicon
    @app.route('/favicon.ico')
    def favicon():
        return app.send_static_file('favicon.ico')
    
    return app

def init_extensions(app: Flask) -> None:
    """Инициализация расширений Flask."""
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    babel.init_app(app)
    limiter.init_app(app)
    
    # Отключаем CSRF защиту для JSON API эндпоинтов: регистрируем after_request exempt по префиксу
    # Прямое использование lambda в exempt может не работать корректно; явно исключим известные blueprints
    try:
        from .api import menu_api, docs_api, system_api, audit_api, bonus_cards_api, table_settings_api, carousel_api
        csrf.exempt(menu_api)
        csrf.exempt(docs_api)
        csrf.exempt(system_api)
        csrf.exempt(audit_api)
        csrf.exempt(bonus_cards_api)
        csrf.exempt(table_settings_api)
        csrf.exempt(carousel_api)
    except Exception:
        # В случае порядка импорта, подстрахуемся проверкой пути запроса
        csrf.exempt(lambda: request.path.startswith('/api/'))
    
    # Настройка Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Загрузка пользователя по ID для Flask-Login."""
        from app.models import Staff
        return Staff.query.get(int(user_id))

def register_blueprints(app: Flask) -> None:
    """Регистрация blueprints."""
    from .controllers import auth_bp, admin_bp, main_bp, waiter_bp, client_bp
    from .api import menu_api, docs_api, system_api, audit_api, bonus_cards_api, table_settings_api, carousel_api
    
    # Web blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(waiter_bp, url_prefix='/waiter')
    app.register_blueprint(client_bp, url_prefix='/client')
    
    # API blueprints
    app.register_blueprint(menu_api)
    app.register_blueprint(docs_api)
    app.register_blueprint(system_api)
    app.register_blueprint(audit_api, url_prefix='/api/audit')
    app.register_blueprint(bonus_cards_api, url_prefix='/api/bonus-cards')
    app.register_blueprint(table_settings_api, url_prefix='/api/tables')
    app.register_blueprint(carousel_api, url_prefix='/api/carousel')

def register_error_handlers(app: Flask) -> None:
    """Регистрация обработчиков ошибок."""
    from .errors import register_error_handlers as register_handlers
    register_handlers(app)

def init_system_components(app: Flask) -> None:
    """Инициализация системных компонентов."""
    # Автоматическая инициализация БД при первом запуске
    with app.app_context():
        try:
            # Проверка существования таблиц
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if not tables:
                app.logger.info("Таблицы БД не найдены, выполняется инициализация...")
                db.create_all()
                app.logger.info("База данных инициализирована")
                
                # Создание начальных данных
                from .utils.admin_tools import DatabaseManager
                result = DatabaseManager.seed_database()
                app.logger.info(f"Инициализация данных: {result['message']}")
                
        except Exception as e:
            app.logger.error(f"Ошибка инициализации системы: {e}")

def init_audit_system(app: Flask) -> None:
    """Инициализация системы аудита."""
    try:
        from .utils.audit_middleware import audit_middleware
        audit_middleware.init_app(app)
        app.logger.info("Система аудита инициализирована")
    except Exception as e:
        app.logger.error(f"Ошибка инициализации аудита: {e}")

def register_audit_commands(app: Flask) -> None:
    """Регистрация CLI команд аудита."""
    try:
        from .utils.audit_cli import register_audit_commands
        register_audit_commands(app)
        app.logger.info("CLI команды аудита зарегистрированы")
    except Exception as e:
        app.logger.error(f"Ошибка регистрации CLI команд аудита: {e}")

def init_security_components(app: Flask) -> None:
    """Инициализация компонентов безопасности."""
    try:
        from .utils.security import init_security
        init_security(app)
        app.logger.info("Система безопасности инициализирована")
    except Exception as e:
        app.logger.error(f"Ошибка инициализации системы безопасности: {e}")

def setup_logging(app: Flask) -> None:
    """Настройка системы логирования."""
    if app.config.get('TESTING'):
        return
        
    # Создание директории для логов
    import os
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Настройка уровня логирования
    log_level = logging.DEBUG if app.debug else logging.INFO
    app.logger.setLevel(log_level)
    
    # Настройка форматтера с дополнительным контекстом
    class RequestFormatter(logging.Formatter):
        def format(self, record):
            try:
                # Проверяем наличие контекста приложения
                from flask import has_request_context
                if has_request_context() and hasattr(g, 'request_id'):
                    record.request_id = g.request_id
                else:
                    record.request_id = 'no-request'
            except RuntimeError:
                # Если нет контекста приложения
                record.request_id = 'app-init'
            return super().format(record)
    
    formatter = RequestFormatter(
        '%(asctime)s %(name)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d] [request_id: %(request_id)s]'
    )
    
    # Файловый обработчик
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    app.logger.addHandler(file_handler)
    
    # Обработчик ошибок
    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=10485760,
        backupCount=5
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    app.logger.addHandler(error_handler)
    
    # Консольный вывод для разработки
    if app.debug:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(console_handler)
    
    # Добавление контекста запроса в логи
    @app.before_request
    def before_request():
        import uuid
        from flask import g
        from datetime import datetime
        
        g.request_id = str(uuid.uuid4())
        g.start_time = datetime.utcnow()
        
        app.logger.info(
            f"Request started: {request.method} {request.path}"
        )
    
    @app.after_request
    def after_request(response):
        from flask import g, request
        from datetime import datetime
        import time
        
        if hasattr(g, 'request_id') and hasattr(g, 'start_time'):
            try:
                # Если start_time это datetime объект
                if isinstance(g.start_time, datetime):
                    duration = (datetime.utcnow() - g.start_time).total_seconds()
                # Если start_time это timestamp (float)
                elif isinstance(g.start_time, (int, float)):
                    duration = time.time() - g.start_time
                else:
                    duration = 0
                
                app.logger.info(
                    f"Request completed: {response.status_code} "
                    f"({duration:.4f}s)"
                )
            except Exception as e:
                app.logger.warning(f"Error calculating request duration: {e}")
        
        return response
        
    app.logger.info('Приложение DENIZ Restaurant запущено') 