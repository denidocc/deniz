#!/usr/bin/env python3
"""Скрипт для запуска в режиме разработки."""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию в PATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app import create_app

def main():
    """Запуск приложения в режиме разработки."""
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', '1')
    
    app = create_app('development')
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )

if __name__ == '__main__':
    main() 