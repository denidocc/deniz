#!/usr/bin/env python3
"""Продвинутый скрипт для разработки с дополнительными функциями."""

import os
import sys
import click
from pathlib import Path

# Добавляем корневую директорию в PATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app import create_app, db
from app.utils.admin_tools import DatabaseManager

@click.group()
def cli():
    """Инструменты разработки для DENIZ Restaurant."""
    pass

@cli.command()
@click.option('--port', '-p', default=8000, help='Port to run on')
@click.option('--host', '-h', default='0.0.0.0', help='Host to bind to')
@click.option('--debug/--no-debug', default=True, help='Enable debug mode')
def run(port, host, debug):
    """Запуск приложения в режиме разработки с дополнительными опциями."""
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', '1' if debug else '0')
    
    click.echo(f"🚀 Запуск DENIZ Restaurant на {host}:{port}")
    click.echo(f"🔧 Debug режим: {'включен' if debug else 'отключен'}")
    
    app = create_app('development')
    app.run(host=host, port=port, debug=debug, use_reloader=True)

@cli.command()
def init_db():
    """Инициализация базы данных с тестовыми данными."""
    click.echo("🗄️  Инициализация базы данных...")
    
    app = create_app('development')
    with app.app_context():
        # Создаем таблицы
        db.create_all()
        click.echo("✅ Таблицы созданы")
        
        # Заполняем начальными данными
        result = DatabaseManager.seed_database()
        click.echo(f"📊 {result['message']}")

@cli.command()
def reset_db():
    """Полный сброс базы данных."""
    if click.confirm('⚠️  Вы уверены, что хотите удалить все данные?'):
        app = create_app('development')
        with app.app_context():
            db.drop_all()
            db.create_all()
            result = DatabaseManager.seed_database()
            click.echo(f"🔄 База данных сброшена: {result['message']}")

@cli.command()
def show_routes():
    """Показать все маршруты приложения."""
    app = create_app('development')
    with app.app_context():
        click.echo("📋 Маршруты приложения:")
        for rule in app.url_map.iter_rules():
            methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            click.echo(f"  {rule.endpoint:30} {methods:15} {rule.rule}")

if __name__ == '__main__':
    cli() 