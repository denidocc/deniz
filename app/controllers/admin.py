"""Административные контроллеры."""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, make_response, current_app
from flask_login import current_user
from sqlalchemy import func, desc, extract
import sqlalchemy.orm as so
from datetime import datetime, timedelta
import json

from app import db
from app.models import (
    Staff, MenuCategory, MenuItem, Table, Order, OrderItem, 
    BonusCard, AuditLog, SystemSetting, DailyReport, TableAssignment, Banner
)
from app.utils.decorators import admin_required, audit_action, with_transaction
from app.utils.image_upload import ImageUploadManager
from app.forms.admin.menu import MenuCategoryForm, MenuItemForm

from app.forms.admin.staff import StaffCreateForm, StaffUpdateForm
from app.forms.admin.settings import SystemSettingForm, ServiceChargeForm, ClientPinForm, PrinterSettingsForm
from app.forms.admin.reports import ReportFilterForm, ZReportForm, AuditFilterForm
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
    

    
    # Последние действия в системе (аудит)
    recent_actions = AuditLog.query.order_by(
        desc(AuditLog.created_at)
    ).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         today_stats=today_stats,
                         popular_dishes=popular_dishes,

                         recent_actions=recent_actions)

# === УПРАВЛЕНИЕ МЕНЮ ===

@admin_bp.route('/menu')
@admin_required
@audit_action("view_menu_management")
def menu():
    """Управление меню."""
    categories = MenuCategory.query.options(
        so.joinedload(MenuCategory.items)
    ).order_by(MenuCategory.sort_order).all()
    items = MenuItem.query.join(MenuCategory).order_by(
        MenuCategory.sort_order, MenuItem.sort_order
    ).all()
    
    # Дополнительная отладка для блюд
    current_app.logger.info(f"Loaded {len(items)} menu items")
    for item in items:
        current_app.logger.info(f"Item: {item.id} - {item.name_ru} (category: {item.category_id}, is_active: {item.is_active})")
    
    # Логируем количество загруженных категорий
    current_app.logger.info(f"Loaded {len(categories)} categories for menu management")
    for cat in categories:
        current_app.logger.info(f"Category: {cat.id} - {cat.name_ru} (active: {cat.is_active})")
    
    # Создаем формы для валидации
    category_form = MenuCategoryForm()
    item_form = MenuItemForm()
    
    # Обновляем choices для категорий в форме
    item_form.category_id.choices = [(cat.id, cat.name_ru) for cat in categories]
    current_app.logger.info(f"Form choices: {item_form.category_id.choices}")
    
    # Дополнительная отладка
    current_app.logger.info(f"Categories in template: {[cat.name_ru for cat in categories]}")
    current_app.logger.info(f"Categories count: {len(categories)}")
    
    # Проверяем отношения
    for cat in categories:
        current_app.logger.info(f"Category {cat.id} ({cat.name_ru}) has {len(cat.items)} items")
        for item in cat.items:
            current_app.logger.info(f"  - Item: {item.id} - {item.name_ru} (is_active: {item.is_active})")
    
    # Отладочная информация для статистики
    active_items = [item for item in items if item.is_active]
    inactive_items = [item for item in items if not item.is_active]
    current_app.logger.info(f"Statistics: {len(active_items)} active items, {len(inactive_items)} inactive items")
    
    return render_template('admin/menu.html',
                         categories=categories,
                         items=items,
                         category_form=category_form,
                         item_form=item_form)

@admin_bp.route('/menu/category', methods=['POST'])
@admin_required
@audit_action("create_menu_category")
@with_transaction
def create_category():
    """Создание новой категории меню."""
    data = request.get_json() or {}
    current_app.logger.info(f"Creating category with data: {data}")
    
    form = MenuCategoryForm(data=data, meta={'csrf': False})
    if not form.validate():
        current_app.logger.error(f"Category form validation failed: {form.errors}")
        return jsonify({'status': 'error', 'message': 'Валидация не пройдена', 'errors': form.errors}), 400
    
    category = MenuCategory(
        name_ru=form.name_ru.data,
        name_en=form.name_en.data or '',
        name_tk=form.name_tk.data or '',
        sort_order=form.sort_order.data or 0,
        is_active=True  # По умолчанию категория активна
    )
    
    current_app.logger.info(f"Category object created: {category}")
    current_app.logger.info(f"Category is_active: {category.is_active}")
    
    db.session.add(category)
    db.session.flush()
    
    current_app.logger.info(f"Category saved with ID: {category.id}")
    
    return jsonify({
        'status': 'success',
        'message': 'Категория успешно создана',
        'data': {
            'id': category.id,
            'name': category.name_ru
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
    
    # Создаем формы для валидации
    create_form = StaffCreateForm()
    update_form = StaffUpdateForm()
    
    return render_template('admin/staff.html',
                         staff_members=staff_members,
                         roles=roles,
                         role_stats=role_stats,
                         create_form=create_form,
                         update_form=update_form)

@admin_bp.route('/staff/create', methods=['POST'])
@admin_required
@audit_action("create_staff_member")
@with_transaction
def create_staff():
    """Создание нового сотрудника."""
    try:
        data = request.get_json() or {}
        
        # Логируем входящие данные
        current_app.logger.info(f"Creating staff with data: {data}")
        current_app.logger.info(f"is_active value: {data.get('is_active')}")
        current_app.logger.info(f"is_active type: {type(data.get('is_active'))}")
        
        form = StaffCreateForm(data=data, meta={'csrf': False})
        if not form.validate():
            current_app.logger.error(f"Form validation failed: {form.errors}")
            return jsonify({'status': 'error', 'message': 'Валидация не пройдена', 'errors': form.errors}), 400
        
        # Проверка уникальности логина
        if Staff.find_by_login(form.login.data):
            return jsonify({
                'status': 'error',
                'message': 'Сотрудник с таким логином уже существует'
            }), 400
        
        # Логируем данные формы
        current_app.logger.info(f"Form is_active.data: {form.is_active.data}")
        current_app.logger.info(f"Form is_active.data type: {type(form.is_active.data)}")
        
        staff = Staff(
            name=form.name.data,
            role=form.role.data,
            login=form.login.data,
            is_active=bool(form.is_active.data)
        )
        
        # Логируем финальное значение
        current_app.logger.info(f"Final staff.is_active: {staff.is_active}")
        
        try:
            staff.set_password(form.password.data)
            current_app.logger.info("Password set successfully")
        except Exception as e:
            current_app.logger.error(f"Error setting password: {e}")
            raise
        
        try:
            db.session.add(staff)
            current_app.logger.info("Staff added to session")
            db.session.flush()
            current_app.logger.info("Staff flushed successfully")
        except Exception as e:
            current_app.logger.error(f"Error adding staff to database: {e}")
            raise
        
        return jsonify({
            'status': 'success',
            'message': 'Сотрудник успешно создан',
            'data': staff.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Unexpected error in create_staff: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Внутренняя ошибка сервера: {str(e)}'
        }), 500

@admin_bp.route('/staff/<int:staff_id>', methods=['PUT', 'DELETE'])
@admin_required
@with_transaction
def update_staff(staff_id):
    """Обновление или удаление данных сотрудника."""
    staff = Staff.query.get_or_404(staff_id)
    
    if request.method == 'DELETE':
        # Аудит удаления
        from app.utils.decorators import audit_action
        audit_action("delete_staff_member")(lambda: None)()
        
        # Удаление сотрудника
        staff_name = staff.name
        db.session.delete(staff)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Сотрудник "{staff_name}" успешно удален'
        })
    
    # Аудит обновления
    from app.utils.decorators import audit_action
    audit_action("update_staff_member")(lambda: None)()
    
    # Обновление данных сотрудника
    data = request.get_json() or {}
    
    # Если обновляется только статус, используем упрощенную логику
    if len(data) == 1 and 'is_active' in data:
        staff.is_active = bool(data['is_active'])
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Сотрудник {"активирован" if staff.is_active else "деактивирован"}',
            'data': {'is_active': staff.is_active}
        })
    
    # Полное обновление через форму
    form = StaffUpdateForm(data=data, meta={'csrf': False}, staff_id=staff_id)
    if not form.validate():
        return jsonify({'status': 'error', 'message': 'Валидация не пройдена', 'errors': form.errors}), 400
    
    # Обновление полей только если они переданы
    if 'name' in data:
        staff.name = form.name.data
    if 'role' in data:
        staff.role = form.role.data
    if 'login' in data:
        staff.login = form.login.data
    if 'is_active' in data:
        staff.is_active = bool(form.is_active.data)
    
    if form.password.data:
        staff.set_password(form.password.data)
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Данные сотрудника обновлены',
        'data': staff.to_dict()
    })



@admin_bp.route('/csrf-token')
@admin_required
def get_csrf_token():
    """Получение нового CSRF токена."""
    from flask_wtf.csrf import generate_csrf
    return jsonify({
        'status': 'success',
        'csrf_token': generate_csrf()
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
    
    # Создаем формы для валидации
    service_charge_form = ServiceChargeForm()
    client_pin_form = ClientPinForm()
    printer_settings_form = PrinterSettingsForm()
    
    return render_template('admin/settings.html',
                         settings=settings_dict,
                         service_charge_form=service_charge_form,
                         client_pin_form=client_pin_form,
                         printer_settings_form=printer_settings_form)

@admin_bp.route('/settings/update', methods=['POST'])
@admin_required
@audit_action("update_system_settings")
@with_transaction
def update_settings():
    """Обновление настроек системы."""
    data = request.get_json() or {}
    
    # Определяем тип настройки и валидируем соответствующей формой
    if 'service_charge_percentage' in data:
        form = ServiceChargeForm(data={'percentage': data['service_charge_percentage']}, meta={'csrf': False})
        if not form.validate():
            return jsonify({'status': 'error', 'message': 'Валидация не пройдена', 'errors': form.errors}), 400
        data['service_charge_percentage'] = str(form.percentage.data)
    
    if 'table_access_pin' in data:
        form = ClientPinForm(data={'pin': data['table_access_pin']}, meta={'csrf': False})
        if not form.validate():
            return jsonify({'status': 'error', 'message': 'Валидация не пройдена', 'errors': form.errors}), 400
    
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
    actions_stats_rows = db.session.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.action).order_by(desc('count')).limit(10).all()
    actions_stats = [(row[0], int(row[1])) for row in actions_stats_rows]
    
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
    
    # Создаем форму для валидации
    audit_filter_form = AuditFilterForm()
    
    return render_template('admin/audit.html',
                         logs=logs,
                         actions_stats=actions_stats,
                         staff_members=Staff.query.all(),
                         getLogSeverity=get_log_severity,
                         audit_filter_form=audit_filter_form)

# === Z-ОТЧЕТЫ ===

@admin_bp.route('/z-reports')
@admin_required
@audit_action("view_z_reports")
def z_reports():
    """Z-отчеты."""
    reports = DailyReport.query.order_by(desc(DailyReport.report_date)).limit(30).all()
    
    # Создаем форму для валидации
    z_report_form = ZReportForm()
    
    return render_template('admin/z_reports.html',
                         reports=reports,
                         z_report_form=z_report_form)

@admin_bp.route('/z-reports/generate', methods=['POST'])
@admin_required
@audit_action("generate_z_report")
@with_transaction
def generate_z_report():
    """Генерация Z-отчета."""
    data = request.get_json() or {}
    form = ZReportForm(data=data, meta={'csrf': False})
    if not form.validate():
        return jsonify({'status': 'error', 'message': 'Валидация не пройдена', 'errors': form.errors}), 400
    
    report_date = form.report_date.data
    
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

@admin_bp.route('/menu/item/<int:item_id>', methods=['GET'])
@admin_required
@audit_action("view_menu_item")
def get_menu_item(item_id):
    """Получение данных блюда для редактирования."""
    item = MenuItem.query.get_or_404(item_id)
    return jsonify({
        'status': 'success',
        'data': item.to_dict()
    })

@admin_bp.route('/menu/item/<int:item_id>', methods=['POST', 'PUT', 'DELETE'])
@admin_required
@audit_action("update_menu_item")
@with_transaction
def update_menu_item(item_id):
    """Обновление или удаление блюда."""
    item = MenuItem.query.get_or_404(item_id)
    
    if request.method == 'DELETE':
        # Удаление блюда
        # Удаляем изображение, если оно было загружено
        if item.image_url and not item.image_url.startswith('http'):
            ImageUploadManager.delete_image(item.image_url)
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Блюдо удалено'
        })
    
    # Обновление блюда (POST или PUT)
    try:
        # Поддержка JSON и form-data
        if request.is_json:
            data = request.get_json() or {}
            image_file = None
        else:
            data = request.form.to_dict()
            image_file = request.files.get('image')
        
        # Обновляем основные поля
        if 'name_ru' in data:
            item.name_ru = data['name_ru']
        if 'name_en' in data:
            item.name_en = data['name_en']
        if 'name_tk' in data:
            item.name_tk = data['name_tk']
        if 'description_ru' in data:
            item.description_ru = data['description_ru']
        if 'description_en' in data:
            item.description_en = data['description_en']
        if 'description_tk' in data:
            item.description_tk = data['description_tk']
        if 'price' in data:
            item.price = float(data['price'])
        if 'estimated_time' in data:
            item.estimated_time = int(data['estimated_time'])
        if 'preparation_type' in data:
            item.preparation_type = data['preparation_type']
        if 'has_size_options' in data:
            item.has_size_options = data['has_size_options'].lower() == 'true'
        if 'can_modify_ingredients' in data:
            item.can_modify_ingredients = data['can_modify_ingredients'].lower() == 'true'
        if 'sort_order' in data:
            item.sort_order = int(data['sort_order'])
        if 'is_active' in data:
            if isinstance(data['is_active'], bool):
                item.is_active = data['is_active']
            else:
                item.is_active = str(data['is_active']).lower() == 'true'
        
        # Обрабатываем новое изображение, если загружено
        if image_file and image_file.filename != '':
            # Удаляем старое изображение, если оно было загружено
            if item.image_url and not item.image_url.startswith('http'):
                ImageUploadManager.delete_image(item.image_url)
            
            # Загружаем новое
            success, image_path, message = ImageUploadManager.save_image(
                image_file, 'meal'
            )
            
            if not success:
                return jsonify({
                    'status': 'error',
                    'message': message
                }), 400
            
            item.image_url = image_path
        elif 'image_url' in data:
            # Если изображение не загружено, используем URL из формы
            item.image_url = data['image_url']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Блюдо обновлено',
            'data': item.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating menu item: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Ошибка обновления блюда: {str(e)}'
        }), 500

@admin_bp.route('/menu/category/<int:category_id>', methods=['GET'])
@admin_required
@audit_action("view_menu_category")
def get_menu_category(category_id):
    """Получение данных категории для редактирования."""
    category = MenuCategory.query.get_or_404(category_id)
    return jsonify({
        'status': 'success',
        'data': category.to_dict()
    })

@admin_bp.route('/menu/category/<int:category_id>', methods=['POST', 'DELETE'])
@admin_required
@audit_action("update_menu_category")
@with_transaction
def update_menu_category(category_id):
    """Обновление или удаление категории меню."""
    category = MenuCategory.query.get_or_404(category_id)
    
    if request.method == 'DELETE':
        # Удаление категории и всех блюд в ней
        from app.models import MenuItem
        MenuItem.query.filter_by(category_id=category_id).delete()
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Категория и все блюда в ней удалены'
        })
    
    # Обновление категории
    data = request.get_json() or {}
    
    # Валидация через форму
    form = MenuCategoryForm(data=data, meta={'csrf': False})
    if not form.validate():
        return jsonify({'status': 'error', 'message': 'Валидация не пройдена', 'errors': form.errors}), 400
    
    # Обновление полей
    for field in ['name_ru', 'name_en', 'name_tk', 'sort_order']:
        if hasattr(form, field) and getattr(form, field).data is not None:
            setattr(category, field, getattr(form, field).data)
    
    # Обработка is_active отдельно
    if hasattr(form, 'is_active') and form.is_active.data is not None:
        category.is_active = bool(form.is_active.data)
    
    return jsonify({
        'status': 'success',
        'message': 'Категория обновлена',
        'data': category.to_dict()
    })

@admin_bp.route('/menu/item/<int:item_id>/toggle', methods=['POST'])
@admin_required
@audit_action("toggle_menu_item_availability")
@with_transaction
def toggle_menu_item_availability(item_id):
    """Изменение доступности блюда."""
    item = MenuItem.query.get_or_404(item_id)
    data = request.get_json() or {}
    
    if 'is_available' in data:
        item.is_active = data['is_available']
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Блюдо {"доступно" if item.is_active else "скрыто"}',
            'data': {'is_available': item.is_active}
        })
    
    return jsonify({
        'status': 'error',
        'message': 'Не указан параметр is_available'
    }), 400



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

# === УПРАВЛЕНИЕ СТОЛАМИ ===

@admin_bp.route('/tables')
@admin_required
@audit_action("view_tables_page")
def tables_page():
    """Страница управления столами."""
    tables = Table.query.order_by(Table.table_number).all()
    return render_template('admin/tables.html', tables=tables)

@admin_bp.route('/api/staff/waiters')
@admin_required
@audit_action("view_waiters_list")
def get_waiters():
    """Получение списка официантов для назначения к столам."""
    try:
        from app.models import Staff
        
        # Получаем только активных официантов
        waiters = Staff.query.filter_by(
            role='waiter',
            is_active=True
        ).order_by(Staff.name).all()
        
        waiters_data = []
        for waiter in waiters:
            waiters_data.append({
                'id': waiter.id,
                'name': waiter.name,
                'login': waiter.login,
                'is_active': waiter.is_active
            })
        
        return jsonify({
            'status': 'success',
            'data': waiters_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting waiters: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка получения списка официантов'
        }), 500

@admin_bp.route('/api/tables/assign', methods=['POST'])
@admin_required
@audit_action("assign_table_to_waiter")
@with_transaction
def assign_table_to_waiter():
    """Назначение стола официанту."""
    try:
        data = request.get_json() or {}
        
        table_id = data.get('table_id')
        waiter_id = data.get('waiter_id')
        is_active = data.get('is_active', True)
        
        if not table_id or not waiter_id:
            return jsonify({
                'status': 'error',
                'message': 'ID стола и официанта обязательны'
            }), 400
        
        # Проверяем существование стола и официанта
        from app.models import Table, Staff, TableAssignment
        
        table = Table.query.get(table_id)
        if not table:
            return jsonify({
                'status': 'error',
                'message': 'Стол не найден'
            }), 404
        
        waiter = Staff.query.get(waiter_id)
        if not waiter or waiter.role != 'waiter':
            return jsonify({
                'status': 'error',
                'message': 'Официант не найден'
            }), 404
        
        # Проверяем, не назначен ли уже стол другому официанту
        existing_assignment = TableAssignment.query.filter_by(
            table_id=table_id,
            is_active=True
        ).first()
        
        if existing_assignment:
            # Деактивируем существующее назначение
            existing_assignment.is_active = False
            current_app.logger.info(f"Deactivated existing assignment: table {table_id} -> waiter {existing_assignment.waiter_id}")
        
        # Создаем новое назначение
        new_assignment = TableAssignment(
            table_id=table_id,
            waiter_id=waiter_id,
            is_active=is_active
        )
        
        db.session.add(new_assignment)
        db.session.commit()
        
        current_app.logger.info(f"Assigned table {table_id} to waiter {waiter_id}")
        
        return jsonify({
            'status': 'success',
            'message': f'Стол {table.table_number} назначен официанту {waiter.name}',
            'data': {
                'table_id': table_id,
                'waiter_id': waiter_id,
                'assignment_id': new_assignment.id
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error assigning table to waiter: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка назначения стола официанту'
        }), 500

@admin_bp.route('/api/tables', methods=['GET'])
@admin_required
@audit_action("view_tables")
def get_tables():
    """Получение списка всех столов с информацией о назначенных официантах."""
    try:
        from app.models import TableAssignment, Staff
        
        tables = Table.query.order_by(Table.table_number).all()
        tables_data = []
        
        for table in tables:
            table_data = table.to_dict()
            
            # Получаем активное назначение официанта для этого стола
            assignment = TableAssignment.query.filter_by(
                table_id=table.id,
                is_active=True
            ).first()
            
            if assignment:
                waiter = Staff.query.get(assignment.waiter_id)
                table_data['assigned_waiter'] = {
                    'id': waiter.id,
                    'name': waiter.name,
                    'login': waiter.login
                } if waiter else None
            else:
                table_data['assigned_waiter'] = None
            
            tables_data.append(table_data)
        
        return jsonify({
            'status': 'success',
            'data': tables_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting tables with assignments: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка получения столов'
        }), 500

@admin_bp.route('/api/tables/create', methods=['POST'])
@admin_required
@audit_action("create_table")
@with_transaction
def create_table():
    """Создание нового стола."""
    data = request.get_json() or {}
    
    table_number = data.get('table_number')
    capacity = data.get('capacity')
    is_active = data.get('is_active', True)
    
    if not table_number or not capacity:
        return jsonify({
            'status': 'error',
            'message': 'Номер стола и количество мест обязательны'
        }), 400
    
    # Проверка уникальности номера стола
    existing_table = Table.query.filter_by(table_number=table_number).first()
    if existing_table:
        return jsonify({
            'status': 'error',
            'message': f'Стол с номером {table_number} уже существует'
        }), 400
    
    # Создание стола
    table = Table(
        table_number=table_number,
        capacity=capacity,
        is_active=is_active
    )
    
    db.session.add(table)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'Стол {table_number} успешно создан',
        'data': table.to_dict()
    })

@admin_bp.route('/api/tables/<int:table_id>', methods=['GET'])
@admin_required
@audit_action("view_table")
def get_table(table_id):
    """Получение данных конкретного стола."""
    table = Table.query.get_or_404(table_id)
    return jsonify({
        'status': 'success',
        'data': table.to_dict()
    })

@admin_bp.route('/api/tables/<int:table_id>/status', methods=['GET'])
@admin_required
@audit_action("check_table_status")
def check_table_status(table_id):
    """Проверка статуса стола для возможности удаления."""
    table = Table.query.get_or_404(table_id)
    
    # Проверяем, есть ли активные заказы
    from app.models import Order
    active_orders = Order.query.filter(
        Order.table_id == table_id,
        Order.status.in_(['pending', 'confirmed', 'active'])
    ).first()
    
    can_delete = active_orders is None
    
    return jsonify({
        'status': 'success',
        'data': {
            'table_id': table_id,
            'table_number': table.table_number,
            'can_delete': can_delete,
            'has_active_orders': not can_delete
        }
    })

@admin_bp.route('/api/tables/<int:table_id>/update', methods=['PUT'])
@admin_required
@audit_action("update_table")
@with_transaction
def update_table(table_id):
    """Обновление стола."""
    table = Table.query.get_or_404(table_id)
    data = request.get_json() or {}
    
    table_number = data.get('table_number')
    capacity = data.get('capacity')
    is_active = data.get('is_active')
    
    if table_number is not None:
        # Проверка уникальности номера стола (если изменился)
        if table_number != table.table_number:
            existing_table = Table.query.filter_by(table_number=table_number).first()
            if existing_table:
                return jsonify({
                    'status': 'error',
                    'message': f'Стол с номером {table_number} уже существует'
                }), 400
        table.table_number = table_number
    
    if capacity is not None:
        table.capacity = capacity
    
    if is_active is not None:
        table.is_active = is_active
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'Стол {table.table_number} успешно обновлен',
        'data': table.to_dict()
    })

@admin_bp.route('/api/tables/<int:table_id>/delete', methods=['DELETE'])
@admin_required
@audit_action("delete_table")
@with_transaction
def delete_table(table_id):
    """Удаление стола."""
    table = Table.query.get_or_404(table_id)
    
    # Проверка, не используется ли стол в активных заказах
    from app.models import Order
    # Проверяем заказы со статусами: pending, confirmed, active
    active_orders = Order.query.filter(
        Order.table_id == table_id,
        Order.status.in_(['pending', 'confirmed', 'active'])
    ).first()
    if active_orders:
        return jsonify({
            'status': 'error',
            'message': 'Нельзя удалить стол с активными заказами'
        }), 400
    
    table_number = table.table_number
    db.session.delete(table)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'Стол {table_number} успешно удален'
    })

# === УПРАВЛЕНИЕ БАННЕРАМИ ===

@admin_bp.route('/banners')
@admin_required
@audit_action("view_banners_management")
def banners_page():
    """Страница управления баннерами."""
    return render_template('admin/banners.html')

@admin_bp.route('/api/banners', methods=['GET'])
@admin_required
@audit_action("get_banners")
def get_banners():
    """Получение списка всех баннеров."""
    banners = Banner.query.order_by(Banner.sort_order).all()
    return jsonify({
        'status': 'success',
        'data': [banner.to_dict() for banner in banners]
    })

@admin_bp.route('/api/banners', methods=['POST'])
@admin_required
@audit_action("create_banner")
@with_transaction
def create_banner():
    """Создание нового баннера."""
    try:
        # Логируем входящие данные для отладки
        current_app.logger.info(f"Creating banner with form data: {request.form.to_dict()}")
        current_app.logger.info(f"Files: {list(request.files.keys())}")
        
        data = request.form.to_dict()
        image_file = request.files.get('image')
        
        current_app.logger.info(f"Image file: {image_file.filename if image_file else 'None'}")
        current_app.logger.info(f"Form data keys: {list(data.keys())}")
        
        if not image_file or image_file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'Изображение обязательно для загрузки'
            }), 400
        
        # Загружаем изображение
        current_app.logger.info(f"Attempting to save image: {image_file.filename}")
        success, image_path, message = ImageUploadManager.save_image(
            image_file, 'banner'
        )
        
        current_app.logger.info(f"Image save result: success={success}, path={image_path}, message={message}")
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
        
        # Получаем следующий порядок сортировки
        max_sort_order = db.session.query(db.func.max(Banner.sort_order)).scalar() or 0
        next_sort_order = max_sort_order + 1
        
        # Создаем баннер
        banner = Banner(
            title=data.get('title', ''),
            description=data.get('description', ''),
            image_path=image_path,
            image_url=f'/static/assets/{image_path}',
            is_active=data.get('is_active') == 'true',
            sort_order=next_sort_order,
            link_url=data.get('link_url', ''),
            link_text=data.get('link_text', ''),
            start_date=datetime.fromisoformat(data['start_date'].replace('Z', '+00:00')) if data.get('start_date') else None,
            end_date=datetime.fromisoformat(data['end_date'].replace('Z', '+00:00')) if data.get('end_date') else None
        )
        
        db.session.add(banner)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Баннер успешно создан',
            'data': banner.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating banner: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Ошибка создания баннера: {str(e)}'
        }), 500

@admin_bp.route('/api/banners/<int:banner_id>', methods=['GET'])
@admin_required
@audit_action("get_banner")
def get_banner(banner_id):
    """Получение данных конкретного баннера."""
    banner = Banner.query.get_or_404(banner_id)
    return jsonify({
        'status': 'success',
        'data': banner.to_dict()
    })

@admin_bp.route('/api/banners/<int:banner_id>', methods=['PUT'])
@admin_required
@audit_action("update_banner")
@with_transaction
def update_banner(banner_id):
    """Обновление баннера."""
    try:
        banner = Banner.query.get_or_404(banner_id)
        data = request.form.to_dict()
        
        # Обновляем основные поля
        if 'title' in data:
            banner.title = data['title']
        if 'description' in data:
            banner.description = data['description']
        if 'is_active' in data:
            banner.is_active = data['is_active'] == 'true'
        if 'sort_order' in data:
            banner.sort_order = int(data['sort_order'])
        if 'link_url' in data:
            banner.link_url = data['link_url']
        if 'link_text' in data:
            banner.link_text = data['link_text']
        if 'start_date' in data and data['start_date']:
            banner.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        if 'end_date' in data and data['end_date']:
            banner.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        
        # Обрабатываем новое изображение, если загружено
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            # Удаляем старое изображение
            if banner.image_path:
                ImageUploadManager.delete_image(banner.image_path)
            
            # Загружаем новое
            success, image_path, message = ImageUploadManager.save_image(
                image_file, 'banner'
            )
            
            if not success:
                return jsonify({
                    'status': 'error',
                    'message': message
                }), 400
            
            banner.image_path = image_path
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Баннер успешно обновлен',
            'data': banner.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating banner: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Ошибка обновления баннера: {str(e)}'
        }), 500

@admin_bp.route('/api/banners/<int:banner_id>', methods=['DELETE'])
@admin_required
@audit_action("delete_banner")
@with_transaction
def delete_banner(banner_id):
    """Удаление баннера."""
    try:
        banner = Banner.query.get_or_404(banner_id)
        
        # Удаляем изображение
        if banner.image_path:
            ImageUploadManager.delete_image(banner.image_path)
        
        banner_title = banner.title
        db.session.delete(banner)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Баннер "{banner_title}" успешно удален'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting banner: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Ошибка удаления баннера: {str(e)}'
        }), 500

@admin_bp.route('/api/banners/<int:banner_id>/toggle', methods=['PUT'])
@admin_required
@audit_action("toggle_banner_status")
@with_transaction
def toggle_banner_status(banner_id):
    """Переключение статуса баннера."""
    banner = Banner.query.get_or_404(banner_id)
    banner.is_active = not banner.is_active
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'Статус баннера "{banner.title}" изменен на {"активный" if banner.is_active else "неактивный"}',
        'data': banner.to_dict()
    })

@admin_bp.route('/api/banners/reorder', methods=['PUT'])
@admin_required
@audit_action("reorder_banners")
@with_transaction
def reorder_banners():
    """Изменение порядка баннеров."""
    try:
        data = request.get_json() or {}
        banner_orders = data.get('banner_orders', [])
        
        for item in banner_orders:
            banner_id = item.get('id')
            new_order = item.get('sort_order')
            
            if banner_id and new_order is not None:
                banner = Banner.query.get(banner_id)
                if banner:
                    banner.sort_order = new_order
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Порядок баннеров обновлен'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error reordering banners: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Ошибка изменения порядка: {str(e)}'
        }), 500

@admin_bp.route('/api/menu-items', methods=['POST'])
@admin_required
@audit_action("create_menu_item_api")
@with_transaction
def create_menu_item_api():
    """Создание нового блюда."""
    try:
        # Поддержка JSON и form-data
        if request.is_json:
            data = request.get_json() or {}
            image_file = None
        else:
            data = request.form.to_dict()
            image_file = request.files.get('image')

        # Валидация обязательных полей
        required_fields = ['category_id', 'name_ru', 'price']
        missing_fields = [f for f in required_fields if not data.get(f)]
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f"Отсутствуют обязательные поля: {', '.join(missing_fields)}"
            }), 400

        def to_bool(value, default=False):
            if isinstance(value, bool):
                return value
            if value is None:
                return default
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)
        
        # Получаем следующий порядок сортировки для категории
        max_sort_order = db.session.query(db.func.max(MenuItem.sort_order))\
            .filter_by(category_id=int(data['category_id']))\
            .scalar() or 0
        next_sort_order = max_sort_order + 1
        
        # Создаем блюдо
        menu_item = MenuItem(
            category_id=int(data['category_id']),
            name_ru=data['name_ru'],
            name_en=data.get('name_en', ''),
            name_tk=data.get('name_tk', ''),
            description_ru=data.get('description_ru', ''),
            price=float(data['price']),
            estimated_time=int(data.get('estimated_time', 15)),
            preparation_type=data.get('preparation_type', 'kitchen'),  # Значение по умолчанию
            sort_order=next_sort_order,
            is_active=to_bool(data.get('is_active', True))
        )
        
        # Обрабатываем изображение, если есть
        if image_file and image_file.filename != '':
            success, image_path, message = ImageUploadManager.save_image(
                image_file, 'meal'
            )
            
            if success:
                menu_item.image_url = f'/static/assets/{image_path}'
            else:
                current_app.logger.warning(f"Image upload failed: {message}")
        else:
            # Если изображение не загружено, используем URL из формы
            menu_item.image_url = data.get('image_url', '')
        
        db.session.add(menu_item)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Блюдо успешно создано',
            'data': menu_item.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating menu item: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Ошибка создания блюда: {str(e)}'
        }), 500 