"""
API endpoints для системной информации.

Предоставляет информацию о состоянии системы, версии, конфигурации.
"""

from flask import Blueprint, jsonify, current_app
from app.utils.decorators import measure_time, log_requests
from app.version import get_version_info, __version__
from app.utils.admin_tools import SystemInfo
from app import limiter
import logging
from datetime import datetime
import time
import os

# Создание blueprint для системных API
system_api = Blueprint('system_api', __name__)

# Настройка логирования
logger = logging.getLogger(__name__)

# Время старта приложения
start_time = time.time()

@system_api.route('/api/system/info', methods=['GET'])
@limiter.limit("50 per hour")
@measure_time
@log_requests
def get_system_info():
    """
    Получение общей информации о системе.
    
    Возвращает информацию о версии, окружении, поддерживаемых функциях
    и состоянии основных компонентов системы.
    
    Returns:
        JSON объект с информацией о системе
        
    Example:
        GET /api/system/info
        
    Response:
        {
            "status": "success",
            "message": "Информация о системе",
            "data": {
                "name": "DENIZ Restaurant API",
                "version": "1.0.0",
                "build": "dev",
                "environment": "development",
                "features": {
                    "menu_api": true,
                    "orders_api": false,
                    "auth_api": false,
                    "printer_integration": false
                },
                "supported_languages": ["ru", "tk", "en"],
                "database": {
                    "status": "connected",
                    "type": "PostgreSQL"
                }
            }
        }
    """
    try:
        # Получение версионной информации
        version_info = get_version_info()
        
        # Получение статуса системы
        system_status = SystemInfo.get_system_status()
        
        # Информация о поддерживаемых функциях
        features = {
            "menu_api": True,  # Уже реализовано
            "orders_api": False,  # Планируется в следующих спринтах
            "auth_api": False,  # Планируется
            "printer_integration": False,  # Планируется
            "multi_language": True,  # Уже реализовано
            "caching": True,  # Уже реализовано
            "security_middleware": True,  # Уже реализовано
            "rate_limiting": True,  # Уже реализовано
        }
        
        # Формирование ответа
        system_info = {
            "name": "DENIZ Restaurant API",
            "version": version_info["version"],
            "build": version_info["build"],
            "environment": version_info["environment"],
            "build_time": version_info["build_time"],
            "python_version": version_info["python_version"],
            "features": features,
            "supported_languages": ["ru", "tk", "en"],
            "database": system_status["database"],
            "configuration": {
                "debug": current_app.debug,
                "testing": current_app.testing,
                "service_charge_percent": current_app.config.get('SERVICE_CHARGE_PERCENT', 10.0),
                "order_edit_timeout": current_app.config.get('ORDER_EDIT_TIMEOUT_MINUTES', 5),
            }
        }
        
        logger.info("System info requested")
        
        return jsonify({
            'status': 'success',
            'message': 'Информация о системе',
            'data': system_info
        }), 200
        
    except Exception as e:
        logger.error(f"System info error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Ошибка при получении информации о системе',
            'data': {}
        }), 500


@system_api.route('/api/system/health', methods=['GET'])
@limiter.limit("200 per hour")
@measure_time
def health_check():
    """
    Проверка состояния системы (healthcheck).
    
    Используется для мониторинга доступности системы.
    Проверяет подключение к базе данных и основные компоненты.
    
    Returns:
        JSON объект с состоянием системы
        
    Example:
        GET /api/system/health
        
    Response:
        {
            "status": "healthy",
            "timestamp": "2025-01-29T10:30:00Z",
            "version": "1.0.0",
            "uptime": 3600.5,
            "checks": {
                "database": "healthy",
                "cache": "healthy"
            }
        }
    """
    try:
        # Проверка базы данных
        system_status = SystemInfo.get_system_status()
        db_healthy = system_status["database"]["status"] == "connected"
        
        # Проверка кеша (если включен)
        cache_healthy = True
        try:
            from app import cache
            cache.get('health_check')  # Простая проверка доступности
        except Exception:
            cache_healthy = False
        
        # Расчет времени работы
        uptime = time.time() - start_time
        
        # Определение общего состояния
        overall_healthy = db_healthy and cache_healthy
        status = "healthy" if overall_healthy else "unhealthy"
        status_code = 200 if overall_healthy else 503
        
        health_data = {
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": __version__,
            "uptime": round(uptime, 2),
            "checks": {
                "database": "healthy" if db_healthy else "unhealthy",
                "cache": "healthy" if cache_healthy else "unhealthy",
            },
            "environment": current_app.config.get('ENV', 'unknown')
        }
        
        if not overall_healthy:
            logger.warning(f"Health check failed: {health_data}")
        
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": "Health check failed",
            "error": str(e)
        }), 503


@system_api.route('/api/system/stats', methods=['GET'])
@limiter.limit("100 per hour")
@measure_time
@log_requests
def get_system_stats():
    """
    Получение статистики использования системы.
    
    Возвращает статистику запросов, производительности и использования ресурсов.
    
    Returns:
        JSON объект со статистикой системы
    """
    try:
        # Базовая статистика
        stats = {
            "uptime_seconds": round(time.time() - start_time, 2),
            "version": __version__,
            "environment": current_app.config.get('ENV', 'unknown'),
            "process_id": os.getpid(),
            "memory_usage": {
                "description": "Для получения информации о памяти требуется psutil"
            },
            "request_stats": {
                "description": "Статистика запросов будет добавлена в будущих версиях"
            }
        }
        
        logger.info("System stats requested")
        
        return jsonify({
            'status': 'success',
            'message': 'Статистика системы',
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"System stats error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Ошибка при получении статистики системы',
            'data': {}
        }), 500 