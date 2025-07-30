"""CLI команды для управления аудитом."""

import click
from flask.cli import with_appcontext
from flask import current_app
from datetime import datetime, timedelta
import json

@click.group()
def audit():
    """Команды управления аудитом."""
    pass

@audit.command()
@click.option('--limit', default=50, help='Количество записей для показа')
@click.option('--staff-id', type=int, help='ID сотрудника')
@click.option('--action', help='Фильтр по действию')
@click.option('--hours', type=int, default=24, help='Часов назад')
@with_appcontext
def logs(limit, staff_id, action, hours):
    """Просмотр логов аудита."""
    from app.models import AuditLog, Staff
    
    query = AuditLog.query
    
    # Фильтр по времени
    since = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(AuditLog.created_at >= since)
    
    # Фильтры
    if staff_id:
        query = query.filter_by(staff_id=staff_id)
    if action:
        query = query.filter(AuditLog.action.contains(action))
    
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    if not logs:
        click.echo("Логи не найдены")
        return
    
    click.echo(f"\n📋 Найдено {len(logs)} записей за последние {hours} часов:\n")
    
    for log in logs:
        staff_name = log.staff.name if log.staff else "Система"
        
        click.echo(f"🕐 {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"👤 {staff_name} ({log.staff.login if log.staff else 'system'})")
        click.echo(f"🎯 {log.action}")
        
        if log.table_affected:
            click.echo(f"🪑 Стол: {log.table_affected}")
        if log.order_affected:
            click.echo(f"🧾 Заказ: {log.order_affected}")
        if log.ip_address:
            click.echo(f"🌐 IP: {log.ip_address}")
        
        # Детали
        details = log.get_details()
        if details:
            if 'method' in details and 'url' in details:
                click.echo(f"🔗 {details['method']} {details['url']}")
            if 'response_status' in details:
                status_color = 'green' if details['response_status'] < 400 else 'red'
                click.echo(click.style(f"📊 Статус: {details['response_status']}", fg=status_color))
            if 'duration_seconds' in details:
                click.echo(f"⏱️  Время: {details['duration_seconds']}с")
        
        click.echo("-" * 60)

@audit.command()
@click.option('--days', default=7, help='Дней для статистики')
@with_appcontext
def stats(days):
    """Статистика аудита."""
    from app.models import AuditLog
    
    stats = AuditLog.get_statistics(days=days)
    
    click.echo(f"\n📊 Статистика аудита за {days} дней:\n")
    click.echo(f"📈 Всего действий: {stats['total_actions']}")
    click.echo(f"❌ Ошибок: {stats['error_count']} ({stats['error_percentage']}%)")
    
    click.echo(f"\n🔝 Топ действий:")
    for action in stats['top_actions'][:5]:
        click.echo(f"  • {action['action']}: {action['count']}")
    
    click.echo(f"\n👥 Топ пользователей:")
    from app.models import Staff
    for user in stats['top_users'][:5]:
        staff = Staff.query.get(user['staff_id'])
        name = staff.name if staff else f"ID {user['staff_id']}"
        click.echo(f"  • {name}: {user['count']} действий")

@audit.command()
@click.option('--hours', default=1, help='Часов назад')
@with_appcontext
def errors(hours):
    """Просмотр ошибок."""
    from app.models import AuditLog
    
    since = datetime.utcnow() - timedelta(hours=hours)
    error_logs = AuditLog.query.filter(
        AuditLog.created_at >= since,
        AuditLog.action.like('%_error')
    ).order_by(AuditLog.created_at.desc()).all()
    
    if not error_logs:
        click.echo(f"🎉 Ошибок за последние {hours} часов не найдено")
        return
    
    click.echo(f"\n❌ Найдено {len(error_logs)} ошибок за последние {hours} часов:\n")
    
    for log in error_logs:
        staff_name = log.staff.name if log.staff else "Система"
        details = log.get_details()
        
        click.echo(f"🕐 {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"👤 {staff_name}")
        click.echo(click.style(f"🚨 {log.action}", fg='red'))
        
        if 'error' in details:
            click.echo(f"💥 Ошибка: {details['error']}")
        if 'exception_type' in details:
            click.echo(f"🔍 Тип: {details['exception_type']}")
        
        click.echo("-" * 60)

@audit.command()
@click.option('--ip', help='IP адрес')
@click.option('--limit', default=20, help='Количество записей')
@with_appcontext
def by_ip(ip, limit):
    """Просмотр действий по IP адресу."""
    from app.models import AuditLog
    
    if not ip:
        click.echo("Укажите IP адрес с помощью --ip")
        return
    
    logs = AuditLog.get_logs_by_ip(ip, limit)
    
    if not logs:
        click.echo(f"Действий с IP {ip} не найдено")
        return
    
    click.echo(f"\n🌐 Действия с IP {ip} (последние {len(logs)}):\n")
    
    for log in logs:
        staff_name = log.staff.name if log.staff else "Гость"
        click.echo(f"🕐 {log.created_at.strftime('%Y-%m-%d %H:%M:%S')} | {staff_name} | {log.action}")

@audit.command()
@click.option('--action', required=True, help='Название действия')
@click.option('--limit', default=20, help='Количество записей')
@with_appcontext
def by_action(action, limit):
    """Просмотр записей по действию."""
    from app.models import AuditLog
    
    logs = AuditLog.get_by_action(action, limit)
    
    if not logs:
        click.echo(f"Действий '{action}' не найдено")
        return
    
    click.echo(f"\n🎯 Действие '{action}' (последние {len(logs)}):\n")
    
    for log in logs:
        staff_name = log.staff.name if log.staff else "Система"
        details = log.get_details()
        
        click.echo(f"🕐 {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"👤 {staff_name}")
        
        if log.table_affected:
            click.echo(f"🪑 Стол: {log.table_affected}")
        if log.order_affected:
            click.echo(f"🧾 Заказ: {log.order_affected}")
        
        if 'response_status' in details:
            status = details['response_status']
            color = 'green' if status < 400 else 'red'
            click.echo(click.style(f"📊 {status}", fg=color))
        
        click.echo("-" * 40)

@audit.command()
@click.option('--table-id', type=int, required=True, help='ID стола')
@click.option('--limit', default=20, help='Количество записей')
@with_appcontext
def by_table(table_id, limit):
    """Просмотр действий по столу."""
    from app.models import AuditLog, Table
    
    # Проверяем существование стола
    table = Table.query.get(table_id)
    if not table:
        click.echo(f"❌ Стол {table_id} не найден")
        return
    
    logs = AuditLog.get_by_table(table_id, limit)
    
    if not logs:
        click.echo(f"Действий по столу {table_id} не найдено")
        return
    
    click.echo(f"\n🪑 Действия по столу {table_id} (последние {len(logs)}):\n")
    
    for log in logs:
        staff_name = log.staff.name if log.staff else "Система"
        
        click.echo(f"🕐 {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"👤 {staff_name} | 🎯 {log.action}")
        
        if log.order_affected:
            click.echo(f"🧾 Связанный заказ: {log.order_affected}")
        
        details = log.get_details()
        if 'response_status' in details:
            status = details['response_status']
            color = 'green' if status < 400 else 'red'
            click.echo(click.style(f"📊 {status}", fg=color))
        
        click.echo("-" * 40)

@audit.command()
@click.option('--order-id', type=int, required=True, help='ID заказа')
@click.option('--limit', default=20, help='Количество записей')
@with_appcontext
def by_order(order_id, limit):
    """Просмотр действий по заказу."""
    from app.models import AuditLog, Order
    
    # Проверяем существование заказа
    order = Order.query.get(order_id)
    if not order:
        click.echo(f"❌ Заказ {order_id} не найден")
        return
    
    logs = AuditLog.get_by_order(order_id, limit)
    
    if not logs:
        click.echo(f"Действий по заказу {order_id} не найдено")
        return
    
    click.echo(f"\n🧾 Действия по заказу {order_id} (последние {len(logs)}):\n")
    click.echo(f"📋 Заказ на столе {order.table.table_number if order.table else 'N/A'}")
    click.echo(f"💰 Сумма: {order.total_amount} | 👥 Гостей: {order.guest_count}")
    click.echo("-" * 60)
    
    for log in logs:
        staff_name = log.staff.name if log.staff else "Система"
        
        click.echo(f"🕐 {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"👤 {staff_name} | 🎯 {log.action}")
        
        details = log.get_details()
        if 'response_status' in details:
            status = details['response_status']
            color = 'green' if status < 400 else 'red'
            click.echo(click.style(f"📊 {status}", fg=color))
        
        click.echo("-" * 40)

@audit.command()
@click.option('--from', 'date_from', required=True, help='Дата начала (YYYY-MM-DD или YYYY-MM-DD HH:MM)')
@click.option('--to', 'date_to', required=True, help='Дата окончания (YYYY-MM-DD или YYYY-MM-DD HH:MM)')
@click.option('--limit', default=100, help='Максимум записей')
@with_appcontext
def date_range(date_from, date_to, limit):
    """Просмотр логов за период."""
    from app.models import AuditLog
    from datetime import datetime
    
    try:
        # Парсим даты
        if len(date_from) == 10:  # YYYY-MM-DD
            start_date = datetime.strptime(date_from, '%Y-%m-%d')
        else:  # YYYY-MM-DD HH:MM
            start_date = datetime.strptime(date_from, '%Y-%m-%d %H:%M')
        
        if len(date_to) == 10:  # YYYY-MM-DD
            end_date = datetime.strptime(date_to, '%Y-%m-%d')
            # Добавляем время до конца дня
            end_date = end_date.replace(hour=23, minute=59, second=59)
        else:  # YYYY-MM-DD HH:MM
            end_date = datetime.strptime(date_to, '%Y-%m-%d %H:%M')
        
    except ValueError as e:
        click.echo(f"❌ Ошибка формата даты: {e}")
        click.echo("Используйте формат: YYYY-MM-DD или YYYY-MM-DD HH:MM")
        return
    
    if start_date >= end_date:
        click.echo("❌ Дата начала должна быть раньше даты окончания")
        return
    
    logs = AuditLog.get_logs_by_date_range(start_date, end_date)
    
    if not logs:
        click.echo(f"Логов за период {date_from} - {date_to} не найдено")
        return
    
    # Ограничиваем количество выводимых записей
    logs = logs[:limit]
    
    click.echo(f"\n📅 Логи за период {date_from} - {date_to} (показано {len(logs)}):\n")
    
    for log in logs:
        staff_name = log.staff.name if log.staff else "Система"
        
        click.echo(f"🕐 {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"👤 {staff_name} | 🎯 {log.action}")
        
        if log.table_affected:
            click.echo(f"🪑 Стол: {log.table_affected}")
        if log.order_affected:
            click.echo(f"🧾 Заказ: {log.order_affected}")
        
        details = log.get_details()
        if 'response_status' in details:
            status = details['response_status']
            color = 'green' if status < 400 else 'red'
            click.echo(click.style(f"📊 {status}", fg=color))
        
        click.echo("-" * 40)

@audit.command()
@click.option('--limit', default=50, help='Количество записей')
@with_appcontext
def recent(limit):
    """Просмотр последних логов (простой)."""
    from app.models import AuditLog
    
    logs = AuditLog.get_recent_logs_simple(limit)
    
    if not logs:
        click.echo("Логи не найдены")
        return
    
    click.echo(f"\n📋 Последние {len(logs)} записей:\n")
    
    for log in logs:
        staff_name = log.staff.name if log.staff else "Система"
        
        click.echo(f"🕐 {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"👤 {staff_name} | 🎯 {log.action}")
        
        if log.table_affected:
            click.echo(f"🪑 Стол: {log.table_affected}")
        if log.order_affected:
            click.echo(f"🧾 Заказ: {log.order_affected}")
        
        click.echo("-" * 40)

@audit.command()
@click.confirmation_option(prompt='Вы уверены, что хотите очистить старые логи?')
@click.option('--days', default=90, help='Удалить логи старше указанного количества дней')
@with_appcontext
def cleanup(days):
    """Очистка старых логов."""
    from app.models import AuditLog
    from app import db
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    old_logs = AuditLog.query.filter(AuditLog.created_at < cutoff_date)
    count = old_logs.count()
    
    if count == 0:
        click.echo(f"Логов старше {days} дней не найдено")
        return
    
    old_logs.delete()
    db.session.commit()
    
    click.echo(f"✅ Удалено {count} записей старше {days} дней")

@audit.command()
@with_appcontext
def test():
    """Тестовая запись аудита."""
    from app.models import AuditLog
    
    result = AuditLog.log_action(
        action="test_audit_cli",
        details={
            "test": True,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Тестовая запись из CLI"
        },
        ip_address="127.0.0.1"
    )
    
    click.echo(f"✅ Создана тестовая запись аудита ID: {result.id}")

# Регистрация группы команд
def register_audit_commands(app):
    """Регистрация команд аудита в приложении."""
    app.cli.add_command(audit) 