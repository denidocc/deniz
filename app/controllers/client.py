"""Контроллер клиентского интерфейса для планшетов."""

from flask import Blueprint, render_template, request, jsonify, current_app
from app.models import Table, MenuItem, MenuCategory, SystemSetting
from app import db, csrf
from sqlalchemy import func
import json
import hashlib
import re

client_bp = Blueprint('client', __name__)

@client_bp.route('/')
def index():
    """Главная страница клиентского интерфейса."""
    try:
        # Получаем настройки системы
        settings = get_system_settings()
        
        # Логируем настройки для отладки
        current_app.logger.info(f"Client settings loaded: {settings}")
        
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

@client_bp.route('/index')
def client_index():
    """Альтернативная главная страница клиентского интерфейса."""
    return index()

@client_bp.route('/debug-settings')
def debug_settings():
    """Отладочная страница для проверки настроек."""
    try:
        settings = get_system_settings()
        return jsonify({
            'status': 'success',
            'settings': settings,
            'raw_settings': [{'key': s.setting_key, 'value': s.setting_value} for s in SystemSetting.query.all()]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@client_bp.route('/clean-duplicate-settings')
def clean_duplicate_settings():
    """Очистка дублирующихся настроек в базе данных."""
    try:
        from app.models import SystemSetting
        
        # Удаляем старые дублирующиеся настройки
        duplicates_to_remove = [
            'service_charge_percent',  # Старый ключ для сервисного сбора
            'carousel_auto_play',      # Старый ключ для автопроигрывания
            'carousel_auto_play_delay', # Старый ключ для задержки
            'carousel_max_slides',     # Старый ключ для слайдов
            'carousel_slides',         # Старый ключ для слайдов
            'system_language',         # Старый ключ для языка
            'max_guests_per_table',    # Старый ключ для гостей
            'printer_kitchen_ip',      # Старые ключи для принтеров
            'printer_bar_ip',
            'printer_receipt_ip',
            'printer_kitchen_port',
            'printer_bar_port',
            'printer_receipt_port'
        ]
        
        removed_count = 0
        for key in duplicates_to_remove:
            setting = SystemSetting.query.filter_by(setting_key=key).first()
            if setting:
                db.session.delete(setting)
                removed_count += 1
                current_app.logger.error(f"Removed duplicate setting: {key}")
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Удалено {removed_count} дублирующихся настроек',
            'removed_settings': removed_count
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error cleaning duplicate settings: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@client_bp.route('/api/banners')
def get_banners():
    """Получение активных баннеров для клиентской части."""
    try:
        from app.models import Banner
        
        # Получаем только активные баннеры с учетом дат, отсортированные по порядку
        banners = Banner.get_current_banners()
        
        # Логируем для отладки
        current_app.logger.info(f"Found {len(banners)} current banners")
        for banner in banners:
            current_app.logger.info(f"Banner: {banner.title}, active: {banner.is_active}, start: {banner.start_date}, end: {banner.end_date}")
        
        # Преобразуем в формат для клиента
        banner_data = []
        for banner in banners:
            banner_data.append({
                'id': banner.id,
                'title': banner.title,
                'description': banner.description,
                'image_path': banner.image_path,
                'image_url': f'/static/assets/{banner.image_path}' if banner.image_path else '',
                'link_url': banner.link_url,
                'link_text': banner.link_text,
                'sort_order': banner.sort_order
            })
        
        return jsonify({
            'status': 'success',
            'data': banner_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting banners: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка загрузки баннеров'
        }), 500

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
@csrf.exempt
def verify_table_pin():
    """Проверка PIN-кода для доступа к выбору стола."""
    try:
        # Надежно извлекаем данные из запроса
        data = request.get_json(silent=True) or {}
        if not data:
            try:
                raw = request.get_data(cache=False, as_text=True)
                if raw:
                    data = json.loads(raw)
            except Exception:
                pass
        if not data:
            data = request.form.to_dict() if request.form else {}
        if not data:
            data = request.args.to_dict() if request.args else {}
        
        if 'pin' not in data or not str(data.get('pin')).strip():
            return jsonify({
                "status": "error",
                "message": "PIN-код обязателен"
            }), 400
        
        entered_pin = data['pin'].strip()

        # Получаем сохраненный PIN-код (хранится как SHA-256)
        stored_pin_hash = SystemSetting.get_value('table_access_pin')

        # Если PIN не настроен, используем дефолтный 2112 (в хешированном виде)
        if not stored_pin_hash:
            stored_pin_hash = hashlib.sha256('2112'.encode()).hexdigest()
        else:
            # Совместимость: если в БД хранится не хеш, а plaintext (например "1234"),
            # конвертируем его в sha256 для корректного сравнения
            value_str = str(stored_pin_hash)
            if not re.fullmatch(r'[0-9a-fA-F]{64}', value_str):
                stored_pin_hash = hashlib.sha256(value_str.encode()).hexdigest()

        # Хешируем введенный PIN и сравниваем
        provided_pin_hash = hashlib.sha256(entered_pin.encode()).hexdigest()

        if provided_pin_hash != stored_pin_hash:
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
    current_app.logger.info("=== MENU API CALLED ===")
    current_app.logger.info(f"Request URL: {request.url}")
    current_app.logger.info(f"Request method: {request.method}")
    current_app.logger.info(f"Request args: {dict(request.args)}")
    current_app.logger.info(f"Request headers: {dict(request.headers)}")
    current_app.logger.info("========================")
    
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
                'image_url': dish.image_url.replace('/images/', '/static/images/') if dish.image_url else None,
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

@client_bp.route('/api/carousel')
def get_carousel():
    """Получение настроек и слайдов карусели."""
    try:
        current_app.logger.info(f"Carousel API called with args: {request.args}")
        current_app.logger.info(f"Request headers: {dict(request.headers)}")
        
        settings = get_system_settings()
        
        # Пока создаем тестовые слайды, позже можно будет добавить модель CarouselSlide
        slides = [
            {
                'id': 1,
                'title': 'РЫБНЫЙ МИКС ДНЯ',
                'description': 'Ассорти из лучших сортов рыбы с авторским соусом и свежими овощами',
                'price': 1250,
                'image_url': '/static/assets/images/fish.png',
                'is_active': True,
                'sort_order': 1
            },
            {
                'id': 2,
                'title': 'КОРОЛЕВСКИЕ КРЕВЕТКИ',
                'description': 'Тигровые креветки на гриле с ароматными травами и лимонным маслом',
                'price': 1850,
                'image_url': '/static/assets/images/fish.png',
                'is_active': True,
                'sort_order': 2
            },
            {
                'id': 3,
                'title': 'МРАМОРНАЯ ГОВЯДИНА',
                'description': 'Стейк Рибай из отборной мраморной говядины с трюфельным соусом',
                'price': 2900,
                'image_url': '/static/assets/images/fish.png',
                'is_active': True,
                'sort_order': 3
            },
            {
                'id': 4,
                'title': 'ЛОБСТЕР С ПАСТОЙ',
                'description': 'Домашняя паста с мясом омара в сливочно-коньячном соусе',
                'price': 2150,
                'image_url': '/static/assets/images/fish.png',
                'is_active': True,
                'sort_order': 4
            }
        ]
        
        carousel_data = {
            'autoplay': True,
            'interval': settings.get('carousel_slide_duration', 5) * 1000,  # в миллисекундах
            'showDots': True,
            'showNavigation': False,
            'slides': slides
        }
        
        return jsonify({
            "status": "success",
            "data": carousel_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting carousel: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка получения карусели"
        }), 500

@client_bp.route('/api/orders', methods=['POST'])
def create_order():
    """Создание нового заказа."""
    try:
        data = request.get_json()
        
        # Валидация обязательных полей
        required_fields = ['table_id', 'items']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Поле '{field}' обязательно"
                }), 400
        
        table_id = data.get('table_id')
        items = data.get('items', [])
        notes = data.get('notes', '')
        bonus_card = data.get('bonus_card')
        language = data.get('language', 'ru')
        
        # Проверяем стол
        table = Table.query.get(table_id)
        if not table:
            return jsonify({
                "status": "error",
                "message": "Стол не найден"
            }), 404
        
        if not table.is_available():
            return jsonify({
                "status": "error",
                "message": "Стол недоступен"
            }), 400
        
        # Проверяем блюда
        if not items:
            return jsonify({
                "status": "error",
                "message": "Список блюд не может быть пустым"
            }), 400
        
        total_amount = 0
        order_items = []
        
        for item in items:
            dish_id = item.get('dish_id')
            quantity = item.get('quantity', 1)
            
            dish = MenuItem.query.get(dish_id)
            if not dish or not dish.is_active:
                return jsonify({
                    "status": "error",
                    "message": f"Блюдо с ID {dish_id} не найдено"
                }), 404
            
            item_total = float(dish.price) * quantity
            total_amount += item_total
            
            order_items.append({
                'dish_id': dish_id,
                'dish_name': get_localized_name(dish, language),
                'quantity': quantity,
                'price': float(dish.price),
                'total': item_total
            })
        
        # Добавляем сервисный сбор
        settings = get_system_settings()
        service_charge_percent = settings.get('service_charge_percent', 5)
        service_charge = total_amount * (service_charge_percent / 100)
        final_amount = total_amount + service_charge
        
        # TODO: Здесь нужно создать запись в базе данных (модель Order)
        # Пока возвращаем успешный ответ с деталями заказа
        
        order_data = {
            'order_id': 'ORD' + str(int(table_id) * 1000 + len(items)),  # Временный ID
            'table_id': table_id,
            'table_number': table.table_number,
            'items': order_items,
            'subtotal': total_amount,
            'service_charge_percent': service_charge_percent,
            'service_charge': service_charge,
            'total_amount': final_amount,
            'status': 'pending',
            'notes': notes,
            'bonus_card': bonus_card,
            'estimated_time': max([30] + [item.get('estimated_time', 30) for item in items]),  # Максимальное время
            'created_at': 'now'  # В реальности - datetime.utcnow()
        }
        
        return jsonify({
            "status": "success",
            "message": "Заказ успешно создан",
            "data": order_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error creating order: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка создания заказа"
        }), 500

@client_bp.route('/api/waiter-call', methods=['POST'])
def call_waiter():
    """Вызов официанта к столу."""
    try:
        data = request.get_json()
        table_id = data.get('table_id')
        
        if not table_id:
            return jsonify({
                "status": "error",
                "message": "ID стола обязателен"
            }), 400
        
        table = Table.query.get(table_id)
        if not table:
            return jsonify({
                "status": "error",
                "message": "Стол не найден"
            }), 404
        
        # TODO: Здесь нужно создать запись в таблице WaiterCall
        # Пока возвращаем успешный ответ
        
        return jsonify({
            "status": "success",
            "message": f"Официант вызван к столу {table.table_number}"
        })
        
    except Exception as e:
        current_app.logger.error(f"Error calling waiter: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка вызова официанта"
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
        
        # Значения по умолчанию (используем только если настройки вообще не найдены)
        defaults = {
            'service_charge': 5,
            'service_charge_enabled': True,
            'currency': 'TMT',
            'restaurant_name': 'DENIZ Restaurant',
            'restaurant_address': '',
            'restaurant_phone': '',
            'restaurant_email': '',
            'default_language': 'ru',
            'available_languages': 'ru,en,tk',
            'order_cancel_timeout': 300,
            'carousel_slide_duration': 5,
            'carousel_transition_speed': 0.5,
            'carousel_slides_count': 3,
            'table_pin_enabled': True,
            'table_access_pin': '2112',
            'tables_count': 28
        }
        
        # Очищаем дублирующиеся настройки
        if 'service_charge' in settings and 'service_charge_percent' in settings:
            # Удаляем старый ключ, оставляем новый
            del settings['service_charge_percent']
            current_app.logger.info("Removed duplicate setting: service_charge_percent")
        
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