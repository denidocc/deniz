#!/usr/bin/env python3
"""Запуск Flask приложения для системы заказов ресторана DENIZ."""

import os
from app import create_app

# Установка переменных окружения
os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('FLASK_DEBUG', '1')

# Создание приложения
app = create_app('development')

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    ) 