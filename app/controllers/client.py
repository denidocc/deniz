"""Контроллер клиентского интерфейса для планшетов."""

from flask import Blueprint, render_template, request, jsonify, current_app
from app.models import Table, MenuItem, MenuCategory, SystemSetting
from app import db
from sqlalchemy import func
import json

client_bp = Blueprint('client', __name__)

@client_bp.route('/')
def index():
    """Главная страница клиентского интерфейса."""
    try:
        # Получаем настройки системы
        settings = get_system_settings()
        
        # Проверяем, включена ли PIN-защита столов
        table_pin_enabled = settings.get('table_pin_enabled', True)
        
        # Если PIN включен, показываем выбор стола
        if table_pin_enabled:
            return render_template('client/menu.html', settings=settings)
        
        # Иначе сразу показываем меню
        return render_template('client/menu.html', 
                             table_id=request.args.get('table_id', 1),
                             settings=settings)
        
    except Exception as e:
        current_app.logger.error(f"Error loading client interface: {e}")
        return render_template('errors/500.html'), 500

@client_bp.route('/menu')
def menu():
    """Страница меню для выбранного стола."""
    try:
        table_id = request.args.get('table_id', 1, type=int)
        
        # Проверяем существование стола
        table = Table.query.get(table_id)
        if not table:
            return render_template('errors/404.html'), 404
        
        # Получаем настройки системы
        settings = get_system_settings()
        
        return render_template('client/menu.html', 
                             table_id=table_id,
                             table=table,
                             settings=settings)
        
    except Exception as e:
        current_app.logger.error(f"Error loading menu for table {table_id}: {e}")
        return render_template('errors/500.html'), 500

@client_bp.route('/api/verify-table-pin', methods=['POST'])
def verify_table_pin():
    """Проверка PIN-кода для доступа к выбору стола."""
    try:
        data = request.get_json()
        
        if not data or 'pin' not in data:
            return jsonify({
                "status": "error",
                "message": "PIN-код обязателен"
            }), 400
        
        entered_pin = data['pin']
        
        # Получаем настоящий PIN из настроек системы
        actual_pin = get_system_setting('table_access_pin', '1234')
        
        if entered_pin != actual_pin:
            return jsonify({
                "status": "error",
                "message": "Неверный PIN-код"
            }), 401
        
        return jsonify({
            "status": "success",
            "message": "PIN-код верный"
        })
        
    except Exception as e:
        current_app.logger.error(f"Error verifying table PIN: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка проверки PIN-кода"
        }), 500

@client_bp.route('/api/tables')
def get_tables():
    """Получение списка столов."""
    try:
        tables = Table.query.filter_by(is_active=True).order_by(Table.table_number).all()
        
        tables_data = []
        for table in tables:
            tables_data.append({
                'id': table.id,
                'table_number': table.table_number,
                'status': table.status,
                'is_available': table.status in ['available', 'reserved']
            })
        
        return jsonify({
            "status": "success",
            "data": {
                "tables": tables_data
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting tables: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка получения списка столов"
        }), 500

@client_bp.route('/api/menu')
def get_menu():
    """Получение меню с категориями и блюдами."""
    try:
        language = request.args.get('lang', 'ru')
        category_id = request.args.get('category_id', type=int)
        search = request.args.get('search', '').strip()
        
        # Базовый запрос категорий
        categories_query = MenuCategory.query.filter_by(is_active=True).order_by(MenuCategory.sort_order)
        
        # Базовый запрос блюд
        dishes_query = MenuItem.query.filter_by(is_active=True)
        
        # Фильтр по категории
        if category_id:
            dishes_query = dishes_query.filter_by(category_id=category_id)
        
        # Поиск по названию
        if search:
            if language == 'ru':
                dishes_query = dishes_query.filter(MenuItem.name_ru.ilike(f'%{search}%'))
            elif language == 'tk':
                dishes_query = dishes_query.filter(MenuItem.name_tk.ilike(f'%{search}%'))
            elif language == 'en':
                dishes_query = dishes_query.filter(MenuItem.name_en.ilike(f'%{search}%'))
        
        # Получаем данные
        categories = categories_query.all()
        dishes = dishes_query.order_by(MenuItem.sort_order).all()
        
        # Подсчитываем количество блюд в каждой категории
        category_counts = db.session.query(
            MenuItem.category_id,
            func.count(MenuItem.id).label('count')
        ).filter_by(is_active=True).group_by(MenuItem.category_id).all()
        
        count_dict = {item.category_id: item.count for item in category_counts}
        
        # Формируем ответ
        categories_data = []
        for category in categories:
            count = count_dict.get(category.id, 0)
            categories_data.append({
                'id': category.id,
                'name': get_localized_name(category, language),
                'count': count,
                'sort_order': category.sort_order
            })
        
        dishes_data = []
        for dish in dishes:
            dishes_data.append({
                'id': dish.id,
                'category_id': dish.category_id,
                'name': get_localized_name(dish, language),
                'description': get_localized_description(dish, language),
                'price': float(dish.price),
                'image_url': dish.image_url,
                'preparation_type': dish.preparation_type,
                'estimated_time': dish.estimated_time,
                'has_size_options': dish.has_size_options,
                'can_modify_ingredients': dish.can_modify_ingredients
            })
        
        return jsonify({
            "status": "success",
            "data": {
                "categories": categories_data,
                "dishes": dishes_data,
                "language": language,
                "search": search,
                "category_id": category_id
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting menu: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка получения меню"
        }), 500

@client_bp.route('/api/settings')
def get_client_settings():
    """Получение настроек для клиентского интерфейса."""
    try:
        settings = get_system_settings()
        
        # Настройки для клиента (только публичные)
        client_settings = {
            'service_charge_percent': settings.get('service_charge_percent', 5),
            'order_cancel_timeout': settings.get('order_cancel_timeout', 300),
            'carousel_slide_duration': settings.get('carousel_slide_duration', 5),
            'carousel_transition_speed': settings.get('carousel_transition_speed', 0.5),
            'carousel_slides_count': settings.get('carousel_slides_count', 3),
            'languages': ['ru', 'tk', 'en'],
            'default_language': 'ru',
            'table_pin_enabled': settings.get('table_pin_enabled', True),
            'tables_count': settings.get('tables_count', 28)
        }
        
        return jsonify({
            "status": "success",
            "data": client_settings
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting client settings: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка получения настроек"
        }), 500

def get_system_settings():
    """Получение всех системных настроек."""
    try:
        settings_records = SystemSetting.query.all()
        settings = {}
        
        for setting in settings_records:
            try:
                # Пытаемся парсить как JSON
                value = json.loads(setting.setting_value)
            except (json.JSONDecodeError, TypeError):
                # Если не JSON, оставляем как строку
                value = setting.setting_value
                
            # Преобразуем числовые значения
            if isinstance(value, str):
                if value.isdigit():
                    value = int(value)
                elif value.replace('.', '', 1).isdigit():
                    value = float(value)
                elif value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
            
            settings[setting.setting_key] = value
        
        # Значения по умолчанию
        defaults = {
            'service_charge_percent': 5,
            'order_cancel_timeout': 300,
            'carousel_slide_duration': 5,
            'carousel_transition_speed': 0.5,
            'carousel_slides_count': 3,
            'table_pin_enabled': True,
            'table_access_pin': '1234',
            'tables_count': 28
        }
        
        # Добавляем значения по умолчанию, если их нет
        for key, default_value in defaults.items():
            if key not in settings:
                settings[key] = default_value
        
        return settings
        
    except Exception as e:
        current_app.logger.error(f"Error getting system settings: {e}")
        return {}

def get_system_setting(key, default=None):
    """Получение конкретной системной настройки."""
    try:
        setting = SystemSetting.query.filter_by(setting_key=key).first()
        if not setting:
            return default
        
        try:
            # Пытаемся парсить как JSON
            value = json.loads(setting.setting_value)
        except (json.JSONDecodeError, TypeError):
            value = setting.setting_value
        
        # Преобразуем числовые значения
        if isinstance(value, str):
            if value.isdigit():
                value = int(value)
            elif value.replace('.', '', 1).isdigit():
                value = float(value)
            elif value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
        
        return value
        
    except Exception as e:
        current_app.logger.error(f"Error getting setting {key}: {e}")
        return default

def get_localized_name(obj, language):
    """Получение локализованного названия."""
    if language == 'tk' and hasattr(obj, 'name_tk') and obj.name_tk:
        return obj.name_tk
    elif language == 'en' and hasattr(obj, 'name_en') and obj.name_en:
        return obj.name_en
    else:
        return obj.name_ru

def get_localized_description(obj, language):
    """Получение локализованного описания."""
    if language == 'tk' and hasattr(obj, 'description_tk') and obj.description_tk:
        return obj.description_tk
    elif language == 'en' and hasattr(obj, 'description_en') and obj.description_en:
        return obj.description_en
    else:
        return obj.description_ru or ""