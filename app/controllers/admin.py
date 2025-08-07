"""Административные контроллеры."""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, make_response
from flask_login import current_user
from sqlalchemy import func, desc, extract
from datetime import datetime, timedelta
import json

from app import db
from app.models import (
    Staff, MenuCategory, MenuItem, Table, Order, OrderItem, 
    StaffShift, BonusCard, AuditLog, SystemSetting, DailyReport
)
from app.utils.decorators import admin_required, audit_action, with_transaction
# from app.forms.auth import RegistrationForm  # Форма регистрации не используется

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@admin_required
@audit_action("view_admin_dashboard")
def dashboard():
    """Главная страница административной панели."""
    # Статистика за сегодня
    today = datetime.now().date()
    
    # Общая статистика
    stats = {
        'total_staff': Staff.query.filter_by(is_active=True).count(),
        'active_waiters': Staff.query.filter_by(role='waiter', is_active=True).count(),
        'total_tables': Table.query.count(),
        'total_menu_items': MenuItem.query.filter_by(is_active=True).count(),
    }
    
    # Статистика за сегодня
    today_orders = Order.query.filter(
        func.date(Order.created_at) == today
    ).all()
    
    today_stats = {
        'orders_count': len(today_orders),
        'revenue': sum(order.total_amount or 0 for order in today_orders),
        'avg_order': sum(order.total_amount or 0 for order in today_orders) / len(today_orders) if today_orders else 0,
    }
    
    # Популярные блюда за неделю
    week_ago = today - timedelta(days=7)
    popular_dishes = db.session.query(
        MenuItem.name_ru,
        func.sum(OrderItem.quantity).label('total_sold')
    ).join(OrderItem).join(Order).filter(
        func.date(Order.created_at) >= week_ago
    ).group_by(MenuItem.id, MenuItem.name_ru).order_by(
        desc('total_sold')
    ).limit(5).all()
    
    # Активные смены
    active_shifts = StaffShift.query.filter_by(
        shift_date=today,
        shift_end=None
    ).all()
    
    # Последние действия в системе (аудит)
    recent_actions = AuditLog.query.order_by(
        desc(AuditLog.created_at)
    ).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         today_stats=today_stats,
                         popular_dishes=popular_dishes,
                         active_shifts=active_shifts,
                         recent_actions=recent_actions)

# === УПРАВЛЕНИЕ МЕНЮ ===

@admin_bp.route('/menu')
@admin_required
@audit_action("view_menu_management")
def menu():
    """Управление меню."""
    categories = MenuCategory.query.order_by(MenuCategory.sort_order).all()
    items = MenuItem.query.join(MenuCategory).order_by(
        MenuCategory.sort_order, MenuItem.sort_order
    ).all()
    
    return render_template('admin/menu.html',
                         categories=categories,
                         items=items)

@admin_bp.route('/menu/category', methods=['POST'])
@admin_required
@audit_action("create_menu_category")
@with_transaction
def create_category():
    """Создание новой категории меню."""
    data = request.get_json()
    
    category = MenuCategory(
        name_ru=data['name_ru'],
        name_en=data.get('name_en', ''),
        name_tr=data.get('name_tr', ''),
        description_ru=data.get('description_ru', ''),
        description_en=data.get('description_en', ''),
        description_tr=data.get('description_tr', ''),
        sort_order=data.get('sort_order', 0),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(category)
    db.session.flush()
    
    return jsonify({
        'status': 'success',
        'message': 'Категория успешно создана',
        'data': {
            'id': category.id,
            'name': category.name_ru
        }
    })

@admin_bp.route('/menu/item', methods=['POST'])
@admin_required
@audit_action("create_menu_item")
@with_transaction
def create_menu_item():
    """Создание нового блюда."""
    data = request.get_json()
    
    item = MenuItem(
        category_id=data['category_id'],
        name_ru=data['name_ru'],
        name_en=data.get('name_en', ''),
        name_tr=data.get('name_tr', ''),
        description_ru=data.get('description_ru', ''),
        description_en=data.get('description_en', ''),
        description_tr=data.get('description_tr', ''),
        price=float(data['price']),
        estimated_time=data.get('estimated_time', 15),
        image_url=data.get('image_url', ''),
        sort_order=data.get('sort_order', 0),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(item)
    db.session.flush()
    
    return jsonify({
        'status': 'success',
        'message': 'Блюдо успешно создано',
        'data': {
            'id': item.id,
            'name': item.name_ru
        }
    })

# === УПРАВЛЕНИЕ ПЕРСОНАЛОМ ===

@admin_bp.route('/staff')
@admin_required
@audit_action("view_staff_management")
def staff():
    """Управление персоналом."""
    staff_members = Staff.query.order_by(Staff.name).all()
    roles = ['admin', 'waiter', 'kitchen', 'bar']
    
    # Статистика по ролям
    role_stats = {}
    for role in roles:
        role_stats[role] = {
            'total': Staff.query.filter_by(role=role).count(),
            'active': Staff.query.filter_by(role=role, is_active=True).count()
        }
    
    return render_template('admin/staff.html',
                         staff_members=staff_members,
                         roles=roles,
                         role_stats=role_stats)

@admin_bp.route('/staff/create', methods=['POST'])
@admin_required
@audit_action("create_staff_member")
@with_transaction
def create_staff():
    """Создание нового сотрудника."""
    data = request.get_json()
    
    # Проверка уникальности логина
    if Staff.find_by_login(data['login']):
        return jsonify({
            'status': 'error',
            'message': 'Сотрудник с таким логином уже существует'
        }), 400
    
    staff = Staff(
        name=data['name'],
        role=data['role'],
        login=data['login'],
        is_active=data.get('is_active', True)
    )
    staff.set_password(data['password'])
    
    db.session.add(staff)
    db.session.flush()
    
    return jsonify({
        'status': 'success',
        'message': 'Сотрудник успешно создан',
        'data': staff.to_dict()
    })

@admin_bp.route('/staff/<int:staff_id>', methods=['PUT'])
@admin_required
@audit_action("update_staff_member")
@with_transaction
def update_staff(staff_id):
    """Обновление данных сотрудника."""
    staff = Staff.query.get_or_404(staff_id)
    data = request.get_json()
    
    # Проверка уникальности логина (исключая текущего сотрудника)
    if data.get('login') and data['login'] != staff.login:
        existing = Staff.query.filter_by(login=data['login']).first()
        if existing:
            return jsonify({
                'status': 'error',
                'message': 'Сотрудник с таким логином уже существует'
            }), 400
    
    # Обновление полей
    if 'name' in data:
        staff.name = data['name']
    if 'role' in data:
        staff.role = data['role']
    if 'login' in data:
        staff.login = data['login']
    if 'is_active' in data:
        staff.is_active = data['is_active']
    if 'password' in data and data['password']:
        staff.set_password(data['password'])
    
    return jsonify({
        'status': 'success',
        'message': 'Данные сотрудника обновлены',
        'data': staff.to_dict()
    })

# === УПРАВЛЕНИЕ СМЕНАМИ ===

@admin_bp.route('/shifts')
@admin_required
@audit_action("view_shifts_management")
def shifts():
    """Управление сменами."""
    today = datetime.now().date()
    
    # Смены за сегодня
    today_shifts = StaffShift.query.filter_by(shift_date=today).all()
    
    # Статистика смен за неделю
    week_ago = today - timedelta(days=7)
    week_shifts = StaffShift.query.filter(
        StaffShift.shift_date >= week_ago
    ).order_by(desc(StaffShift.shift_date)).all()
    
    # Активные официанты
    active_waiters = Staff.query.filter_by(
        role='waiter', is_active=True
    ).all()
    
    # Все столы
    tables = Table.query.order_by(Table.table_number).all()
    
    return render_template('admin/shifts.html',
                         today_shifts=today_shifts,
                         week_shifts=week_shifts,
                         active_waiters=active_waiters,
                         tables=tables,
                         today=today,
                         now=datetime.now())

@admin_bp.route('/shifts/start', methods=['POST'])
@admin_required
@audit_action("start_shift")
@with_transaction
def start_shift():
    """Начало смены сотрудника."""
    data = request.get_json()
    staff_id = data['staff_id']
    table_ids = data.get('table_ids', [])
    
    # Проверка, что у сотрудника нет активной смены
    active_shift = StaffShift.query.filter_by(
        staff_id=staff_id,
        shift_date=datetime.now().date(),
        shift_end=None
    ).first()
    
    if active_shift:
        return jsonify({
            'status': 'error',
            'message': 'У сотрудника уже есть активная смена'
        }), 400
    
    # Создание смены
    shift = StaffShift(
        staff_id=staff_id,
        shift_date=datetime.now().date(),
        shift_start=datetime.now(),
        is_active=True
    )
    
    db.session.add(shift)
    db.session.flush()  # Получаем ID смены
    
    # Назначаем столы, если указаны
    if table_ids:
        from app.models import TableAssignment
        for table_id in table_ids:
            assignment = TableAssignment(
                table_id=table_id,
                waiter_id=staff_id,
                shift_id=shift.id,
                is_active=True
            )
            db.session.add(assignment)
    
    return jsonify({
        'status': 'success',
        'message': 'Смена успешно начата',
        'data': shift.to_dict()
    })

# === ОТЧЕТЫ ===

@admin_bp.route('/reports')
@admin_required
@audit_action("view_reports")
def reports():
    """Отчеты."""
    return render_template('admin/reports.html')

@admin_bp.route('/reports/sales')
@admin_required
@audit_action("view_sales_report")
def sales_report():
    """Отчет по продажам."""
    # Параметры фильтрации
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Запрос данных
    orders = Order.query.filter(
        func.date(Order.created_at) >= start_date,
        func.date(Order.created_at) <= end_date
    ).all()
    
    # Агрегация данных
    total_revenue = sum(order.total_amount or 0 for order in orders)
    total_orders = len(orders)
    avg_order = total_revenue / total_orders if total_orders else 0
    
    # Группировка по дням
    daily_stats = {}
    for order in orders:
        date_key = order.created_at.date()
        if date_key not in daily_stats:
            daily_stats[date_key] = {
                'orders': 0,
                'revenue': 0
            }
        daily_stats[date_key]['orders'] += 1
        daily_stats[date_key]['revenue'] += order.total_amount or 0
    
    return jsonify({
        'status': 'success',
        'data': {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'summary': {
                'total_revenue': total_revenue,
                'total_orders': total_orders,
                'avg_order': avg_order
            },
            'daily_stats': [
                {
                    'date': date.isoformat(),
                    'orders': stats['orders'],
                    'revenue': stats['revenue']
                }
                for date, stats in sorted(daily_stats.items())
            ]
        }
    })

# === НАСТРОЙКИ СИСТЕМЫ ===

@admin_bp.route('/settings')
@admin_required
@audit_action("view_system_settings")
def settings():
    """Настройки системы."""
    settings = SystemSetting.query.all()
    settings_dict = {s.setting_key: s.setting_value for s in settings}
    
    return render_template('admin/settings.html',
                         settings=settings_dict)

@admin_bp.route('/settings/update', methods=['POST'])
@admin_required
@audit_action("update_system_settings")
@with_transaction
def update_settings():
    """Обновление настроек системы."""
    data = request.get_json()
    
    for key, value in data.items():
        setting = SystemSetting.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = str(value)
        else:
            setting = SystemSetting(setting_key=key, setting_value=str(value))
            db.session.add(setting)
    
    return jsonify({
        'status': 'success',
        'message': 'Настройки успешно обновлены'
    })

# === СИСТЕМА АУДИТА ===

@admin_bp.route('/audit')
@admin_required
@audit_action("view_audit_logs")
def audit_logs():
    """Просмотр логов аудита."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Фильтры
    staff_id = request.args.get('staff_id', type=int)
    action = request.args.get('action')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = AuditLog.query
    
    if staff_id:
        query = query.filter_by(staff_id=staff_id)
    if action:
        query = query.filter(AuditLog.action.contains(action))
    if date_from:
        date_from = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to:
        date_to = datetime.strptime(date_to, '%Y-%m-%d')
        query = query.filter(AuditLog.created_at <= date_to)
    
    logs = query.order_by(desc(AuditLog.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Статистика действий
    actions_stats = db.session.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.action).order_by(desc('count')).limit(10).all()
    
    def get_log_severity(action):
        """Определение уровня важности действия для стилизации."""
        if 'error' in action.lower() or 'fail' in action.lower():
            return 'error'
        elif 'warning' in action.lower() or 'update' in action.lower():
            return 'warning'
        elif 'create' in action.lower() or 'add' in action.lower():
            return 'success'
        else:
            return 'info'
    
    return render_template('admin/audit.html',
                         logs=logs,
                         actions_stats=actions_stats,
                         staff_members=Staff.query.all(),
                         getLogSeverity=get_log_severity)

# === Z-ОТЧЕТЫ ===

@admin_bp.route('/z-reports')
@admin_required
@audit_action("view_z_reports")
def z_reports():
    """Z-отчеты."""
    reports = DailyReport.query.order_by(desc(DailyReport.report_date)).limit(30).all()
    
    return render_template('admin/z_reports.html',
                         reports=reports)

@admin_bp.route('/z-reports/generate', methods=['POST'])
@admin_required
@audit_action("generate_z_report")
@with_transaction
def generate_z_report():
    """Генерация Z-отчета."""
    date = request.get_json().get('date')
    if date:
        report_date = datetime.strptime(date, '%Y-%m-%d').date()
    else:
        report_date = datetime.now().date()
    
    # Проверка, что отчет еще не создан
    existing_report = DailyReport.query.filter_by(report_date=report_date).first()
    if existing_report:
        return jsonify({
            'status': 'error',
            'message': 'Отчет за эту дату уже существует'
        }), 400
    
    # Сбор данных за день
    orders = Order.query.filter(
        func.date(Order.created_at) == report_date
    ).all()
    
    total_revenue = sum(order.total_amount or 0 for order in orders)
    total_orders = len(orders)
    
    # Создание отчета
    report = DailyReport(
        report_date=report_date,
        total_orders=total_orders,
        total_revenue=total_revenue,
        generated_by_id=current_user.id,
        report_data={
            'orders_by_hour': {},  # Можно добавить детализацию
            'payment_methods': {},
            'staff_performance': {}
        }
    )
    
    db.session.add(report)
    
    return jsonify({
        'status': 'success',
        'message': 'Z-отчет успешно сгенерирован',
        'data': report.to_dict()
    })

# === ДОПОЛНИТЕЛЬНЫЕ ЭНДПОИНТЫ ===

@admin_bp.route('/menu/item/<int:item_id>', methods=['PUT'])
@admin_required
@audit_action("update_menu_item")
@with_transaction
def update_menu_item(item_id):
    """Обновление блюда."""
    item = MenuItem.query.get_or_404(item_id)
    data = request.get_json()
    
    # Обновление полей
    for field in ['name_ru', 'name_en', 'name_tr', 'description_ru', 'description_en', 
                  'description_tr', 'price', 'estimated_time', 'image_url', 
                  'sort_order', 'is_active']:
        if field in data:
            setattr(item, field, data[field])
    
    return jsonify({
        'status': 'success',
        'message': 'Блюдо обновлено',
        'data': item.to_dict()
    })

@admin_bp.route('/menu/category/<int:category_id>', methods=['PUT'])
@admin_required
@audit_action("update_menu_category")
@with_transaction
def update_menu_category(category_id):
    """Обновление категории меню."""
    category = MenuCategory.query.get_or_404(category_id)
    data = request.get_json()
    
    # Обновление полей
    for field in ['name_ru', 'name_en', 'name_tr', 'description_ru', 'description_en', 
                  'description_tr', 'sort_order', 'is_active']:
        if field in data:
            setattr(category, field, data[field])
    
    return jsonify({
        'status': 'success',
        'message': 'Категория обновлена',
        'data': category.to_dict()
    })

@admin_bp.route('/shifts/<int:shift_id>/end', methods=['POST'])
@admin_required
@audit_action("end_shift")
@with_transaction
def end_shift(shift_id):
    """Завершение смены."""
    shift = StaffShift.query.get_or_404(shift_id)
    
    if shift.shift_end:
        return jsonify({
            'status': 'error',
            'message': 'Смена уже завершена'
        }), 400
    
    shift.shift_end = datetime.now()
    
    return jsonify({
        'status': 'success',
        'message': 'Смена завершена',
        'data': shift.to_dict()
    })

@admin_bp.route('/backup/create', methods=['POST'])
@admin_required
@audit_action("create_backup")
def create_backup():
    """Создание резервной копии."""
    try:
        from app.utils.backup_manager import BackupManager
        
        backup_manager = BackupManager()
        backup_path = backup_manager.create_backup()
        
        # Обновление настроек с информацией о последнем бэкапе
        from app.models import SystemSetting
        
        last_backup_setting = SystemSetting.query.filter_by(setting_key='last_backup').first()
        if last_backup_setting:
            last_backup_setting.setting_value = datetime.now().isoformat()
        else:
            last_backup_setting = SystemSetting(setting_key='last_backup', setting_value=datetime.now().isoformat())
            db.session.add(last_backup_setting)
        
        backup_size_setting = SystemSetting.query.filter_by(setting_key='backup_size').first()
        if backup_size_setting:
            backup_size_setting.setting_value = backup_manager.get_backup_size(backup_path)
        else:
            backup_size_setting = SystemSetting(setting_key='backup_size', setting_value=backup_manager.get_backup_size(backup_path))
            db.session.add(backup_size_setting)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Резервная копия создана успешно',
            'data': {
                'backup_path': backup_path,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Backup creation failed: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Ошибка создания резервной копии: {str(e)}'
        }), 500

@admin_bp.route('/backup/restore', methods=['POST'])
@admin_required
@audit_action("restore_backup")
def restore_backup():
    """Восстановление из резервной копии."""
    if 'backup_file' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'Файл резервной копии не найден'
        }), 400
    
    backup_file = request.files['backup_file']
    
    if backup_file.filename == '':
        return jsonify({
            'status': 'error',
            'message': 'Файл не выбран'
        }), 400
    
    try:
        from app.utils.backup_manager import BackupManager
        
        backup_manager = BackupManager()
        result = backup_manager.restore_backup(backup_file)
        
        return jsonify({
            'status': 'success',
            'message': 'База данных восстановлена успешно',
            'data': result
        })
        
    except Exception as e:
        current_app.logger.error(f"Backup restoration failed: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Ошибка восстановления: {str(e)}'
        }), 500

@admin_bp.route('/audit/cleanup', methods=['POST'])
@admin_required
@audit_action("cleanup_audit_logs")
@with_transaction
def cleanup_audit_logs():
    """Очистка старых логов аудита."""
    data = request.get_json()
    days_old = data.get('days_old', 30)
    
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    # Подсчет записей для удаления
    old_logs = AuditLog.query.filter(AuditLog.created_at < cutoff_date)
    count = old_logs.count()
    
    # Удаление старых записей
    old_logs.delete()
    
    return jsonify({
        'status': 'success',
        'message': f'Удалено {count} записей старше {days_old} дней'
    })

@admin_bp.route('/z-reports/<int:report_id>')
@admin_required
@audit_action("view_z_report")
def get_z_report(report_id):
    """Получение Z-отчета по ID."""
    report = DailyReport.query.get_or_404(report_id)
    
    return jsonify({
        'status': 'success',
        'data': report.to_dict()
    })

@admin_bp.route('/z-reports/<int:report_id>/export')
@admin_required
@audit_action("export_z_report")
def export_z_report(report_id):
    """Экспорт Z-отчета в PDF."""
    report = DailyReport.query.get_or_404(report_id)
    
    try:
        from app.utils.report_generator import generate_z_report_pdf
        
        pdf_content = generate_z_report_pdf(report)
        
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=z_report_{report.id}.pdf'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"PDF generation failed: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка генерации PDF'
        }), 500 