import os
from datetime import timedelta
from pathlib import Path
from typing import Type
from dotenv import load_dotenv

# Загрузка переменных окружения
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    load_dotenv(env_file)

class BaseConfig:
    """Базовая конфигурация."""
    
    # Основные настройки
    SECRET_KEY: str = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # База данных
    DB_NAME: str = os.environ.get('DB_NAME', 'deniz_restaurant')
    DB_USER: str = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD: str = os.environ.get('DB_PASSWORD', 'password')
    DB_HOST: str = os.environ.get('DB_HOST', 'localhost')
    DB_PORT: str = os.environ.get('DB_PORT', '5432')
    
    SQLALCHEMY_DATABASE_URI: str = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    # JWT настройки
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(days=15)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=30)
    
    # Шифрование
    ENCRYPTION_KEY: str = os.environ.get('ENCRYPTION_KEY', 'default-encryption-key')
    
    # Redis и кеширование
    REDIS_URL: str = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TYPE: str = "redis"
    CACHE_REDIS_URL: str = REDIS_URL
    CACHE_DEFAULT_TIMEOUT: int = 300
    
    # Rate limiting
    RATELIMIT_STORAGE_URL: str = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
    RATELIMIT_DEFAULT: str = "1000 per hour"
    
    # Celery настройки
    CELERY_BROKER_URL: str = REDIS_URL
    CELERY_RESULT_BACKEND: str = REDIS_URL
    
    # Безопасность
    WTF_CSRF_TIME_LIMIT: int = 3600
    WTF_CSRF_SECRET_KEY: str = os.environ.get('WTF_CSRF_SECRET_KEY') or SECRET_KEY
    WTF_CSRF_ENABLED: bool = os.environ.get('WTF_CSRF_ENABLED', 'true').lower() == 'true'
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'
    
    # Файлы
    UPLOAD_FOLDER: str = 'uploads'
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    
    # Настройки ресторана
    SERVICE_CHARGE_PERCENT: float = 10.0  # Сервисный сбор 10%
    ORDER_EDIT_TIMEOUT_MINUTES: int = 5  # Время для отмены заказа
    
    # Принтеры
    PRINTERS = {
        'kitchen': {
            'type': 'network',
            'host': os.environ.get('KITCHEN_PRINTER_HOST', '192.168.1.100'),
            'port': int(os.environ.get('KITCHEN_PRINTER_PORT', '9100'))
        },
        'bar': {
            'type': 'usb',
            'vendor_id': int(os.environ.get('BAR_PRINTER_VENDOR_ID', '0x0483'), 16),
            'product_id': int(os.environ.get('BAR_PRINTER_PRODUCT_ID', '0x5740'), 16)
        },
        'receipt': {
            'type': 'network',
            'host': os.environ.get('RECEIPT_PRINTER_HOST', '192.168.1.101'),
            'port': int(os.environ.get('RECEIPT_PRINTER_PORT', '9100'))
        }
    }

class DevelopmentConfig(BaseConfig):
    """Конфигурация для разработки."""
    
    DEBUG: bool = True
    TESTING: bool = False
    SESSION_COOKIE_SECURE: bool = False
    
    # Менее строгие настройки для разработки
    WTF_CSRF_ENABLED: bool = True
    RATELIMIT_ENABLED: bool = False

class TestingConfig(BaseConfig):
    """Конфигурация для тестирования."""
    
    DEBUG: bool = False
    TESTING: bool = True
    WTF_CSRF_ENABLED: bool = False
    RATELIMIT_ENABLED: bool = False
    
    # Тестовая база данных
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///:memory:'
    
    # Отключение внешних сервисов
    CACHE_TYPE: str = "null"
    CELERY_TASK_ALWAYS_EAGER: bool = True

class ProductionConfig(BaseConfig):
    """Конфигурация для продакшена."""
    
    DEBUG: bool = False
    TESTING: bool = False
    
    # Строгие настройки безопасности
    SESSION_COOKIE_SECURE: bool = True
    WTF_CSRF_ENABLED: bool = True
    RATELIMIT_ENABLED: bool = True
    
    # Логирование
    LOG_LEVEL: str = 'INFO'

# Словарь конфигураций
config_map: dict[str, Type[BaseConfig]] = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}

def get_config(config_name: str = 'default') -> Type[BaseConfig]:
    """
    Получение конфигурации по имени.
    
    Args:
        config_name: Имя конфигурации
        
    Returns:
        Класс конфигурации
    """
    return config_map.get(config_name, DevelopmentConfig) 