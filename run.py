#!/usr/bin/env python3
"""Запуск Flask приложения для системы заказов ресторана DENIZ."""

import os
from app import create_app

# Определение окружения
config_name = os.environ.get('FLASK_ENV', 'development')

# Создание приложения
app = create_app(config_name)

if __name__ == '__main__':
    # Этот блок выполняется только при прямом запуске python run.py
    # Для flask run используются настройки из .flaskenv
    app.run(
        host=os.environ.get('FLASK_RUN_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_RUN_PORT', 8000)),
        debug=os.environ.get('FLASK_DEBUG', '1') == '1'
    ) 