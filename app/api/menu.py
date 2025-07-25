"""
API endpoints для работы с меню ресторана.

Модуль предоставляет REST API для получения информации о меню,
категориях блюд и отдельных позициях с поддержкой многоязычности.
"""

from flask import Blueprint, jsonify, request, current_app
from flask_limiter.util import get_remote_address
from app.models import MenuCategory, MenuItem, MenuItemSize
from app.utils.decorators import measure_time, log_requests
from app.utils.validators import sanitize_input
from app.errors import ValidationError, BusinessLogicError
from typing import Dict, Any, List, Optional
import logging
from app import limiter

# Создание blueprint для API меню
menu_api = Blueprint('menu_api', __name__)

# Настройка логирования
logger = logging.getLogger(__name__)

@menu_api.route('/api/menu', methods=['GET'])
@limiter.limit("1000 per hour")
@measure_time
@log_requests
def get_menu():
    """
    Получение полного меню с категориями и блюдами.
    
    Возвращает структурированное меню с поддержкой многоязычности.
    
    Args:
        lang (str, optional): Язык интерфейса (ru/tk/en). По умолчанию 'ru'
        category_id (int, optional): ID конкретной категории для фильтрации
        preparation_type (str, optional): Тип приготовления (kitchen/bar)
        is_active (bool, optional): Только активные позиции
        
    Returns:
        JSON объект с полным меню
        
    Raises:
        ValidationError: При некорректных параметрах запроса
        
    Example:
        GET /api/menu?lang=ru&preparation_type=kitchen
        
    Response:
        {
            "status": "success",
            "message": "Меню успешно загружено",
            "data": {
                "categories": [
                    {
                        "id": 1,
                        "name": "Горячие блюда",
                        "name_tk": "Ысык ашлар",
                        "name_en": "Hot dishes",
                        "sort_order": 1,
                        "items": [...]
                    }
                ],
                "total_categories": 5,
                "total_items": 25,
                "language": "ru"
            }
        }
    """
    try:
        # Получение параметров запроса
        lang = request.args.get('lang', 'ru').lower()
        category_id = request.args.get('category_id', type=int)
        preparation_type = request.args.get('preparation_type', '').lower()
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        
        # Валидация параметров
        if lang not in ['ru', 'tk', 'en']:
            raise ValidationError("Неподдерживаемый язык. Доступные: ru, tk, en")
        
        if preparation_type and preparation_type not in ['kitchen', 'bar']:
            raise ValidationError("Некорректный тип приготовления. Доступные: kitchen, bar")
        
        # Формирование запроса к БД
        query = MenuCategory.query.filter_by(is_active=True)
        
        if category_id:
            query = query.filter_by(id=category_id)
        
        categories = query.order_by(MenuCategory.sort_order).all()
        
        # Подготовка данных для ответа
        categories_data = []
        total_items = 0
        
        for category in categories:
            # Получение блюд для категории
            items_query = MenuItem.query.filter_by(
                category_id=category.id,
                is_active=is_active
            )
            
            if preparation_type:
                items_query = items_query.filter_by(preparation_type=preparation_type)
            
            items = items_query.order_by(MenuItem.sort_order).all()
            
            # Подготовка данных блюд
            items_data = []
            for item in items:
                item_data = {
                    'id': item.id,
                    'name': getattr(item, f'name_{lang}', item.name_ru),
                    'description': getattr(item, f'description_{lang}', item.description_ru),
                    'price': float(item.price),
                    'image_url': item.image_url,
                    'preparation_type': item.preparation_type,
                    'estimated_time': item.estimated_time,
                    'has_size_options': item.has_size_options,
                    'can_modify_ingredients': item.can_modify_ingredients,
                    'sort_order': item.sort_order
                }
                
                # Добавление размеров порций если есть
                if item.has_size_options:
                    sizes = MenuItemSize.query.filter_by(
                        menu_item_id=item.id
                    ).order_by(MenuItemSize.sort_order).all()
                    
                    item_data['sizes'] = [
                        {
                            'id': size.id,
                            'name': getattr(size, f'size_name_{lang}', size.size_name_ru),
                            'price_modifier': float(size.price_modifier)
                        }
                        for size in sizes
                    ]
                
                items_data.append(item_data)
                total_items += 1
            
            # Подготовка данных категории
            category_data = {
                'id': category.id,
                'name': getattr(category, f'name_{lang}', category.name_ru),
                'name_tk': category.name_tk,
                'name_en': category.name_en,
                'sort_order': category.sort_order,
                'items': items_data,
                'items_count': len(items_data)
            }
            
            categories_data.append(category_data)
        
        # Логирование успешного запроса
        logger.info(
            f"Menu loaded successfully: {len(categories_data)} categories, "
            f"{total_items} items, language: {lang}"
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Меню успешно загружено',
            'data': {
                'categories': categories_data,
                'total_categories': len(categories_data),
                'total_items': total_items,
                'language': lang,
                'filters': {
                    'preparation_type': preparation_type,
                    'is_active': is_active,
                    'category_id': category_id
                }
            }
        }), 200
        
    except ValidationError as e:
        logger.warning(f"Menu API validation error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': {}
        }), 400
        
    except Exception as e:
        logger.error(f"Menu API error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Ошибка при загрузке меню',
            'data': {}
        }), 500


@menu_api.route('/api/menu/categories', methods=['GET'])
@limiter.limit("500 per hour")
@measure_time
@log_requests
def get_categories():
    """
    Получение списка категорий меню.
    
    Возвращает все активные категории с поддержкой многоязычности.
    
    Args:
        lang (str, optional): Язык интерфейса (ru/tk/en). По умолчанию 'ru'
        preparation_type (str, optional): Тип приготовления для фильтрации
        
    Returns:
        JSON объект со списком категорий
        
    Example:
        GET /api/menu/categories?lang=tk
        
    Response:
        {
            "status": "success",
            "message": "Категории загружены",
            "data": {
                "categories": [
                    {
                        "id": 1,
                        "name": "Ысык ашлар",
                        "items_count": 8,
                        "sort_order": 1
                    }
                ]
            }
        }
    """
    try:
        lang = request.args.get('lang', 'ru').lower()
        preparation_type = request.args.get('preparation_type', '').lower()
        
        if lang not in ['ru', 'tk', 'en']:
            raise ValidationError("Неподдерживаемый язык. Доступные: ru, tk, en")
        
        query = MenuCategory.query.filter_by(is_active=True)
        categories = query.order_by(MenuCategory.sort_order).all()
        
        categories_data = []
        for category in categories:
            # Подсчет блюд в категории
            items_query = MenuItem.query.filter_by(
                category_id=category.id,
                is_active=True
            )
            
            if preparation_type:
                items_query = items_query.filter_by(preparation_type=preparation_type)
            
            items_count = items_query.count()
            
            category_data = {
                'id': category.id,
                'name': getattr(category, f'name_{lang}', category.name_ru),
                'name_tk': category.name_tk,
                'name_en': category.name_en,
                'sort_order': category.sort_order,
                'items_count': items_count
            }
            
            categories_data.append(category_data)
        
        logger.info(f"Categories loaded: {len(categories_data)} categories, language: {lang}")
        
        return jsonify({
            'status': 'success',
            'message': 'Категории загружены',
            'data': {
                'categories': categories_data,
                'total_categories': len(categories_data),
                'language': lang
            }
        }), 200
        
    except ValidationError as e:
        logger.warning(f"Categories API validation error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': {}
        }), 400
        
    except Exception as e:
        logger.error(f"Categories API error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Ошибка при загрузке категорий',
            'data': {}
        }), 500


@menu_api.route('/api/menu/items/<int:item_id>', methods=['GET'])
@limiter.limit("2000 per hour")
@measure_time
@log_requests
def get_menu_item(item_id: int):
    """
    Получение детальной информации о конкретном блюде.
    
    Args:
        item_id (int): ID блюда
        lang (str, optional): Язык интерфейса (ru/tk/en). По умолчанию 'ru'
        
    Returns:
        JSON объект с детальной информацией о блюде
        
    Raises:
        BusinessLogicError: Если блюдо не найдено или неактивно
        
    Example:
        GET /api/menu/items/15?lang=en
        
    Response:
        {
            "status": "success",
            "message": "Информация о блюде загружена",
            "data": {
                "item": {
                    "id": 15,
                    "name": "Beef Steak",
                    "description": "Classic beef steak",
                    "price": 850.00,
                    "image_url": "/images/steak.jpg",
                    "preparation_type": "kitchen",
                    "estimated_time": 20,
                    "sizes": [...],
                    "category": {
                        "id": 2,
                        "name": "Hot dishes"
                    }
                }
            }
        }
    """
    try:
        lang = request.args.get('lang', 'ru').lower()
        
        if lang not in ['ru', 'tk', 'en']:
            raise ValidationError("Неподдерживаемый язык. Доступные: ru, tk, en")
        
        # Получение блюда с проверкой активности
        item = MenuItem.query.filter_by(
            id=item_id,
            is_active=True
        ).first()
        
        if not item:
            raise BusinessLogicError("Блюдо не найдено или неактивно")
        
        # Получение категории
        category = MenuCategory.query.get(item.category_id)
        
        # Подготовка данных блюда
        item_data = {
            'id': item.id,
            'name': getattr(item, f'name_{lang}', item.name_ru),
            'description': getattr(item, f'description_{lang}', item.description_ru),
            'price': float(item.price),
            'image_url': item.image_url,
            'preparation_type': item.preparation_type,
            'estimated_time': item.estimated_time,
            'has_size_options': item.has_size_options,
            'can_modify_ingredients': item.can_modify_ingredients,
            'sort_order': item.sort_order,
            'category': {
                'id': category.id,
                'name': getattr(category, f'name_{lang}', category.name_ru)
            } if category else None
        }
        
        # Добавление размеров порций
        if item.has_size_options:
            sizes = MenuItemSize.query.filter_by(
                menu_item_id=item.id
            ).order_by(MenuItemSize.sort_order).all()
            
            item_data['sizes'] = [
                {
                    'id': size.id,
                    'name': getattr(size, f'size_name_{lang}', size.size_name_ru),
                    'price_modifier': float(size.price_modifier)
                }
                for size in sizes
            ]
        
        logger.info(f"Menu item loaded: ID {item_id}, language: {lang}")
        
        return jsonify({
            'status': 'success',
            'message': 'Информация о блюде загружена',
            'data': {
                'item': item_data
            }
        }), 200
        
    except ValidationError as e:
        logger.warning(f"Menu item API validation error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': {}
        }), 400
        
    except BusinessLogicError as e:
        logger.warning(f"Menu item not found: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': {}
        }), 404
        
    except Exception as e:
        logger.error(f"Menu item API error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Ошибка при загрузке информации о блюде',
            'data': {}
        }), 500


@menu_api.route('/api/menu/search', methods=['GET'])
@limiter.limit("300 per hour")
@measure_time
@log_requests
def search_menu_items():
    """
    Поиск блюд по названию и описанию.
    
    Args:
        q (str): Поисковый запрос
        lang (str, optional): Язык интерфейса (ru/tk/en). По умолчанию 'ru'
        category_id (int, optional): Фильтр по категории
        preparation_type (str, optional): Фильтр по типу приготовления
        
    Returns:
        JSON объект с результатами поиска
        
    Example:
        GET /api/menu/search?q=борщ&lang=ru&preparation_type=kitchen
        
    Response:
        {
            "status": "success",
            "message": "Поиск выполнен",
            "data": {
                "items": [...],
                "total_found": 2,
                "query": "борщ"
            }
        }
    """
    try:
        query = request.args.get('q', '').strip()
        lang = request.args.get('lang', 'ru').lower()
        category_id = request.args.get('category_id', type=int)
        preparation_type = request.args.get('preparation_type', '').lower()
        
        if not query:
            raise ValidationError("Поисковый запрос не может быть пустым")
        
        if lang not in ['ru', 'tk', 'en']:
            raise ValidationError("Неподдерживаемый язык. Доступные: ru, tk, en")
        
        if preparation_type and preparation_type not in ['kitchen', 'bar']:
            raise ValidationError("Некорректный тип приготовления. Доступные: kitchen, bar")
        
        # Очистка поискового запроса
        sanitized_query = sanitize_input(query)
        
        # Построение запроса поиска
        from sqlalchemy import or_
        
        search_query = MenuItem.query.filter_by(is_active=True)
        
        # Поиск по названию и описанию на всех языках
        search_conditions = or_(
            MenuItem.name_ru.ilike(f'%{sanitized_query}%'),
            MenuItem.name_tk.ilike(f'%{sanitized_query}%'),
            MenuItem.name_en.ilike(f'%{sanitized_query}%'),
            MenuItem.description_ru.ilike(f'%{sanitized_query}%'),
            MenuItem.description_tk.ilike(f'%{sanitized_query}%'),
            MenuItem.description_en.ilike(f'%{sanitized_query}%')
        )
        
        search_query = search_query.filter(search_conditions)
        
        # Применение фильтров
        if category_id:
            search_query = search_query.filter_by(category_id=category_id)
        
        if preparation_type:
            search_query = search_query.filter_by(preparation_type=preparation_type)
        
        # Выполнение поиска
        items = search_query.order_by(MenuItem.sort_order).limit(20).all()
        
        # Подготовка результатов
        items_data = []
        for item in items:
            item_data = {
                'id': item.id,
                'name': getattr(item, f'name_{lang}', item.name_ru),
                'description': getattr(item, f'description_{lang}', item.description_ru),
                'price': float(item.price),
                'image_url': item.image_url,
                'preparation_type': item.preparation_type,
                'estimated_time': item.estimated_time,
                'category_id': item.category_id
            }
            
            # Добавление размеров если есть
            if item.has_size_options:
                sizes = MenuItemSize.query.filter_by(
                    menu_item_id=item.id
                ).order_by(MenuItemSize.sort_order).all()
                
                item_data['sizes'] = [
                    {
                        'id': size.id,
                        'name': getattr(size, f'size_name_{lang}', size.size_name_ru),
                        'price_modifier': float(size.price_modifier)
                    }
                    for size in sizes
                ]
            
            items_data.append(item_data)
        
        logger.info(f"Menu search completed: query='{sanitized_query}', found={len(items_data)}")
        
        return jsonify({
            'status': 'success',
            'message': 'Поиск выполнен',
            'data': {
                'items': items_data,
                'total_found': len(items_data),
                'query': sanitized_query,
                'language': lang,
                'filters': {
                    'category_id': category_id,
                    'preparation_type': preparation_type
                }
            }
        }), 200
        
    except ValidationError as e:
        logger.warning(f"Menu search API validation error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': {}
        }), 400
        
    except Exception as e:
        logger.error(f"Menu search API error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Ошибка при выполнении поиска',
            'data': {}
        }), 500


@menu_api.route('/api/menu/stats', methods=['GET'])
@limiter.limit("100 per hour")
@measure_time
@log_requests
def get_menu_statistics():
    """
    Получение статистики меню.
    
    Возвращает общую статистику по меню: количество категорий,
    блюд, распределение по типам приготовления и т.д.
    
    Returns:
        JSON объект со статистикой меню
        
    Example:
        GET /api/menu/stats
        
    Response:
        {
            "status": "success",
            "message": "Статистика загружена",
            "data": {
                "total_categories": 5,
                "total_items": 25,
                "kitchen_items": 18,
                "bar_items": 7,
                "average_price": 450.50,
                "price_range": {
                    "min": 50.00,
                    "max": 1200.00
                }
            }
        }
    """
    try:
        from sqlalchemy import func
        
        # Статистика по категориям
        total_categories = MenuCategory.query.filter_by(is_active=True).count()
        
        # Статистика по блюдам
        items_stats = MenuItem.query.filter_by(is_active=True).with_entities(
            func.count(MenuItem.id).label('total_items'),
            func.count(MenuItem.id).filter(MenuItem.preparation_type == 'kitchen').label('kitchen_items'),
            func.count(MenuItem.id).filter(MenuItem.preparation_type == 'bar').label('bar_items'),
            func.avg(MenuItem.price).label('average_price'),
            func.min(MenuItem.price).label('min_price'),
            func.max(MenuItem.price).label('max_price')
        ).first()
        
        # Статистика по размерам порций
        items_with_sizes = MenuItem.query.filter_by(
            is_active=True,
            has_size_options=True
        ).count()
        
        stats_data = {
            'total_categories': total_categories,
            'total_items': items_stats.total_items or 0,
            'kitchen_items': items_stats.kitchen_items or 0,
            'bar_items': items_stats.bar_items or 0,
            'items_with_sizes': items_with_sizes,
            'average_price': float(items_stats.average_price or 0),
            'price_range': {
                'min': float(items_stats.min_price or 0),
                'max': float(items_stats.max_price or 0)
            }
        }
        
        logger.info(f"Menu statistics loaded: {stats_data['total_items']} items, {stats_data['total_categories']} categories")
        
        return jsonify({
            'status': 'success',
            'message': 'Статистика загружена',
            'data': stats_data
        }), 200
        
    except Exception as e:
        logger.error(f"Menu statistics API error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Ошибка при загрузке статистики',
            'data': {}
        }), 500 