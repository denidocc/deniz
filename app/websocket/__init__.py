"""Инициализация WebSocket сервера для локальной среды."""

from flask_socketio import SocketIO
from flask import current_app

# Глобальный экземпляр SocketIO
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='threading',  # Используем threading для совместимости с flask run
    logger=True,
    engineio_logger=True
)

def init_websocket(app):
    """Инициализация WebSocket сервера."""
    
    try:
        # Простая инициализация для локальной среды
        socketio.init_app(app)
        app.logger.info("WebSocket сервер инициализирован для локальной среды")
        
        # Импорт обработчиков событий
        from . import events
        
    except Exception as e:
        app.logger.error(f"Ошибка инициализации WebSocket: {e}")
    
    return socketio