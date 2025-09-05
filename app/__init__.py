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
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
from sqlalchemy import inspect

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

scheduler = BackgroundScheduler()

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
    
    # Инициализация WebSocket сервера
    init_websocket(app)
    
    # Регистрация blueprints
    register_blueprints(app)
    
    # Обработчики ошибок
    register_error_handlers(app)
    
    # Инициализация системных компонентов
    init_system_components(app)
    
    # Инициализация управления сессиями
    init_session_management(app)
    
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
    
    # Инициализация планировщика автобекапов
    init_scheduler(app)
    
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
    with app.app_context():
        try:
            
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
            import traceback
            traceback.print_exc()
            app.logger.error(f"Ошибка инициализации системы: {e}")
    
    # Контекстный процессор для настроек системы
    @app.context_processor
    def inject_settings():
        try:
            from .models import SystemSetting
            settings = SystemSetting.get_all_settings()
            return {'settings': settings}
        except Exception as e:
            app.logger.warning(f"Не удалось загрузить настройки: {e}")
            return {'settings': {}}

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

def init_scheduler(app: Flask) -> None:
    """Инициализация планировщика автобекапов."""
    if app.config.get('TESTING'):
        return  # Не запускаем планировщик в тестах
    
    try:
        # Функция автобекапа
        def auto_backup_job():
            with app.app_context():
                from .models import SystemSetting
                from .utils.backup_manager import BackupManager
                
                # Проверяем включен ли автобекап
                auto_backup_enabled = SystemSetting.get_setting('auto_backup', 'false')
                if auto_backup_enabled.lower() != 'true':
                    app.logger.debug("Auto backup is disabled")
                    return
                
                try:
                    app.logger.info("Starting automatic backup...")
                    backup_manager = BackupManager()
                    backup_path = backup_manager.create_backup()
                    
                    # Обновляем настройки с информацией о последнем бэкапе
                    from datetime import datetime
                    SystemSetting.set_setting('last_backup', datetime.now().isoformat())
                    SystemSetting.set_setting('backup_size', backup_manager.get_backup_size(backup_path))
                    
                    # Очищаем старые бекапы
                    backup_retention = int(SystemSetting.get_setting('backup_retention', '7'))
                    backup_manager.cleanup_old_backups(backup_retention)
                    
                    app.logger.info(f"Automatic backup completed: {backup_path}")
                    
                except Exception as e:
                    app.logger.error(f"Automatic backup failed: {e}")
        
        # Получаем интервал из настроек (с задержкой для инициализации БД)
        def get_backup_interval():
            try:
                from .models import SystemSetting
                return SystemSetting.get_setting('backup_interval', 'daily')
            except:
                return 'daily'
        
        backup_interval = get_backup_interval()
        
        # Настраиваем расписание
        if backup_interval == 'daily':
            trigger = CronTrigger(hour=2, minute=0)  # Каждый день в 02:00
        elif backup_interval == 'weekly':
            trigger = CronTrigger(day_of_week=0, hour=2, minute=0)  # Каждое воскресенье в 02:00
        elif backup_interval == 'monthly':
            trigger = CronTrigger(day=1, hour=2, minute=0)  # 1 числа каждого месяца в 02:00
        else:
            trigger = CronTrigger(hour=2, minute=0)  # По умолчанию ежедневно
        
        # Добавляем задачу в планировщик
        scheduler.add_job(
            func=auto_backup_job,
            trigger=trigger,
            id='auto_backup',
            name='Automatic Database Backup',
            replace_existing=True
        )
        
        # Запускаем планировщик
        if not scheduler.running:
            scheduler.start()
            app.logger.info(f"Backup scheduler started with {backup_interval} interval")
            
            # Регистрируем остановку планировщика при завершении приложения
            atexit.register(lambda: scheduler.shutdown() if scheduler.running else None)
        
    except Exception as e:
        app.logger.error(f"Failed to initialize backup scheduler: {e}")

def init_session_management(app: Flask) -> None:
    """Инициализация управления сессиями с динамическим таймаутом."""
    from datetime import timedelta
    
    @app.before_request
    def update_session_timeout():
        """Обновление времени жизни сессии на основе настроек."""
        if request.endpoint and not request.endpoint.startswith('static'):
            try:
                # Получаем настройку таймаута из базы данных
                from .models import SystemSetting
                session_timeout_minutes = int(SystemSetting.get_setting('session_timeout', '120'))
                
                # Обновляем конфигурацию приложения
                current_timeout = app.permanent_session_lifetime
                new_timeout = timedelta(minutes=session_timeout_minutes)
                
                if current_timeout != new_timeout:
                    app.permanent_session_lifetime = new_timeout
                    app.logger.debug(f"Session timeout updated: {session_timeout_minutes} minutes")
                
                # Делаем сессию постоянной для применения таймаута
                if hasattr(g, 'current_user') or 'user_id' in session:
                    session.permanent = True
                    
            except Exception as e:
                app.logger.debug(f"Session timeout update failed: {e}")
    
    @app.before_request
    def check_session_activity():
        """Проверка активности сессии для автоматического выхода."""
        from flask_login import current_user, logout_user
        from datetime import datetime
        
        # Пропускаем статические файлы и API endpoints
        if (request.endpoint and 
            (request.endpoint.startswith('static') or 
             request.path.startswith('/api/') or
             request.endpoint == 'auth.login')):
            return
        
        if current_user.is_authenticated:
            now = datetime.now()
            
            # Проверяем последнюю активность
            last_activity = session.get('last_activity')
            if last_activity:
                try:
                    from .models import SystemSetting
                    session_timeout_minutes = int(SystemSetting.get_setting('session_timeout', '120'))
                    
                    if isinstance(last_activity, str):
                        last_activity = datetime.fromisoformat(last_activity)
                    
                    time_diff = now - last_activity
                    if time_diff.total_seconds() > (session_timeout_minutes * 60):
                        # Сессия истекла - принудительный выход
                        app.logger.info(f"Session expired for user {current_user.login} after {session_timeout_minutes} minutes of inactivity")
                        logout_user()
                        session.clear()
                        
                        # Перенаправляем на страницу входа с сообщением
                        from flask import flash, redirect, url_for
                        flash('Сессия истекла из-за неактивности. Пожалуйста, войдите снова.', 'warning')
                        return redirect(url_for('auth.login'))
                        
                except Exception as e:
                    app.logger.error(f"Session activity check failed: {e}")
            
            # Обновляем время последней активности
            session['last_activity'] = now.isoformat()

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
    
    # Файловый обработчик (без ротации для разработки)
    if app.debug:
        file_handler = logging.FileHandler('logs/app.log')
    else:
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    app.logger.addHandler(file_handler)
    
    # Обработчик ошибок (без ротации для разработки)
    if app.debug:
        error_handler = logging.FileHandler('logs/errors.log')
    else:
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

def init_websocket(app: Flask) -> None:
    """Инициализация WebSocket сервера."""
    try:
        from .websocket import init_websocket as init_ws
        init_ws(app)
        app.logger.info("WebSocket сервер инициализирован")
    except Exception as e:
        app.logger.error(f"Ошибка инициализации WebSocket: {e}")