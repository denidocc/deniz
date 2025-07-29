#!/usr/bin/env python3
"""Скрипты для работы с базой данных."""

import click
from flask.cli import with_appcontext
import sys
from pathlib import Path

# Добавляем корневую директорию в PATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app import create_app, db

@click.group()
def cli():
    """Команды управления базой данных."""
    pass

@cli.command()
@with_appcontext
def init():
    """Инициализация базы данных."""
    db.create_all()
    click.echo('База данных инициализирована.')

@cli.command()
@with_appcontext
def drop():
    """Удаление всех таблиц."""
    if click.confirm('Вы уверены, что хотите удалить все таблицы?'):
        db.drop_all()
        click.echo('Все таблицы удалены.')

@cli.command()
@with_appcontext
def reset():
    """Пересоздание базы данных."""
    if click.confirm('Вы уверены, что хотите пересоздать базу данных?'):
        db.drop_all()
        db.create_all()
        click.echo('База данных пересоздана.')

@cli.command()
@click.argument('username')
@click.argument('password')
@click.option('--email', help='Email администратора')
@with_appcontext
def create_admin(username, password, email):
    """Создание администратора."""
    from app.utils.admin_tools import DatabaseManager
    result = DatabaseManager.create_admin_user(username, password, email)
    click.echo(result['message'])

@cli.command()
@with_appcontext
def seed():
    """Заполнение базы данных начальными данными."""
    from app.utils.admin_tools import DatabaseManager
    result = DatabaseManager.seed_database()
    click.echo(result['message'])

def main():
    """Главная функция для запуска CLI."""
    app = create_app()
    with app.app_context():
        cli()

if __name__ == '__main__':
    main() 