"""
API endpoints для управления каруселью промо-блюд
"""

from flask import Blueprint, jsonify, request
from app.models import SystemSetting
from app.utils.decorators import admin_required
import json

carousel_api = Blueprint('carousel_api', __name__)

@carousel_api.route('/settings', methods=['GET'])
def get_carousel_settings():
    """Получение настроек карусели"""
    try:
        # Настройки карусели из system_settings
        auto_play = SystemSetting.get_setting('carousel_auto_play', 'true')
        auto_play_delay = int(SystemSetting.get_setting('carousel_auto_play_delay', '5000'))
        max_slides = int(SystemSetting.get_setting('carousel_max_slides', '5'))
        
        settings = {
            'enableAutoPlay': auto_play.lower() == 'true',
            'autoPlayDelay': auto_play_delay,
            'maxSlides': max_slides
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Настройки карусели получены',
            'data': settings
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Ошибка получения настроек: {str(e)}',
            'data': {}
        }), 500

@carousel_api.route('/slides', methods=['GET'])
def get_carousel_slides():
    """Получение слайдов карусели"""
    try:
        # Получаем слайды из system_settings
        slides_json = SystemSetting.get_setting('carousel_slides', '[]')
        
        try:
            slides_data = json.loads(slides_json)
        except json.JSONDecodeError:
            slides_data = []
        
        # Фильтруем только активные слайды
        active_slides = [slide for slide in slides_data if slide.get('is_active', False)]
        
        # Сортируем по порядку
        active_slides.sort(key=lambda x: x.get('sort_order', 0))
        
        return jsonify({
            'status': 'success',
            'message': 'Слайды карусели получены',
            'data': {
                'slides': active_slides
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Ошибка получения слайдов: {str(e)}',
            'data': {}
        }), 500

@carousel_api.route('/slides', methods=['POST'])
@admin_required
def create_carousel_slide():
    """Создание нового слайда карусели"""
    try:
        data = request.get_json()
        
        # Валидация данных
        required_fields = ['title', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'Поле {field} обязательно',
                    'data': {}
                }), 400
        
        # Получаем текущие слайды
        slides_json = SystemSetting.get_setting('carousel_slides', '[]')
        try:
            slides_data = json.loads(slides_json)
        except json.JSONDecodeError:
            slides_data = []
        
        # Проверяем лимит слайдов
        max_slides = int(SystemSetting.get_setting('carousel_max_slides', '5'))
        if len(slides_data) >= max_slides:
            return jsonify({
                'status': 'error',
                'message': f'Превышен лимит слайдов ({max_slides})',
                'data': {}
            }), 400
        
        # Создаем новый слайд
        new_slide = {
            'id': max([s.get('id', 0) for s in slides_data], default=0) + 1,
            'title': data['title'],
            'description': data['description'],
            'price': data.get('price'),
            'image_url': data.get('image_url'),
            'menu_item_id': data.get('menu_item_id'),
            'action_text': data.get('action_text', 'Заказать'),
            'is_active': data.get('is_active', True),
            'sort_order': data.get('sort_order', len(slides_data))
        }
        
        slides_data.append(new_slide)
        
        # Сохраняем обновленные слайды
        SystemSetting.set_setting('carousel_slides', json.dumps(slides_data))
        
        return jsonify({
            'status': 'success',
            'message': 'Слайд создан успешно',
            'data': new_slide
        }), 201
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Ошибка создания слайда: {str(e)}',
            'data': {}
        }), 500

@carousel_api.route('/slides/<int:slide_id>', methods=['PUT'])
@admin_required
def update_carousel_slide(slide_id):
    """Обновление слайда карусели"""
    try:
        data = request.get_json()
        
        # Получаем текущие слайды
        slides_json = SystemSetting.get_setting('carousel_slides', '[]')
        try:
            slides_data = json.loads(slides_json)
        except json.JSONDecodeError:
            return jsonify({
                'status': 'error',
                'message': 'Некорректные данные слайдов',
                'data': {}
            }), 400
        
        # Находим слайд для обновления
        slide_index = None
        for i, slide in enumerate(slides_data):
            if slide.get('id') == slide_id:
                slide_index = i
                break
        
        if slide_index is None:
            return jsonify({
                'status': 'error',
                'message': 'Слайд не найден',
                'data': {}
            }), 404
        
        # Обновляем слайд
        slide = slides_data[slide_index]
        slide.update({
            'title': data.get('title', slide['title']),
            'description': data.get('description', slide['description']),
            'price': data.get('price', slide.get('price')),
            'image_url': data.get('image_url', slide.get('image_url')),
            'menu_item_id': data.get('menu_item_id', slide.get('menu_item_id')),
            'action_text': data.get('action_text', slide.get('action_text', 'Заказать')),
            'is_active': data.get('is_active', slide.get('is_active', True)),
            'sort_order': data.get('sort_order', slide.get('sort_order', 0))
        })
        
        # Сохраняем обновленные слайды
        SystemSetting.set_setting('carousel_slides', json.dumps(slides_data))
        
        return jsonify({
            'status': 'success',
            'message': 'Слайд обновлен успешно',
            'data': slide
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Ошибка обновления слайда: {str(e)}',
            'data': {}
        }), 500

@carousel_api.route('/slides/<int:slide_id>', methods=['DELETE'])
@admin_required
def delete_carousel_slide(slide_id):
    """Удаление слайда карусели"""
    try:
        # Получаем текущие слайды
        slides_json = SystemSetting.get_setting('carousel_slides', '[]')
        try:
            slides_data = json.loads(slides_json)
        except json.JSONDecodeError:
            return jsonify({
                'status': 'error',
                'message': 'Некорректные данные слайдов',
                'data': {}
            }), 400
        
        # Находим и удаляем слайд
        original_length = len(slides_data)
        slides_data = [slide for slide in slides_data if slide.get('id') != slide_id]
        
        if len(slides_data) == original_length:
            return jsonify({
                'status': 'error',
                'message': 'Слайд не найден',
                'data': {}
            }), 404
        
        # Сохраняем обновленные слайды
        SystemSetting.set_setting('carousel_slides', json.dumps(slides_data))
        
        return jsonify({
            'status': 'success',
            'message': 'Слайд удален успешно',
            'data': {}
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Ошибка удаления слайда: {str(e)}',
            'data': {}
        }), 500

@carousel_api.route('/settings', methods=['POST'])
@admin_required
def update_carousel_settings():
    """Обновление настроек карусели"""
    try:
        data = request.get_json()
        
        # Обновляем настройки
        if 'enableAutoPlay' in data:
            SystemSetting.set_setting('carousel_auto_play', str(data['enableAutoPlay']).lower())
        
        if 'autoPlayDelay' in data:
            delay = int(data['autoPlayDelay'])
            if delay < 1000 or delay > 10000:
                return jsonify({
                    'status': 'error',
                    'message': 'Задержка должна быть от 1 до 10 секунд',
                    'data': {}
                }), 400
            SystemSetting.set_setting('carousel_auto_play_delay', str(delay))
        
        if 'maxSlides' in data:
            max_slides = int(data['maxSlides'])
            if max_slides < 1 or max_slides > 10:
                return jsonify({
                    'status': 'error',
                    'message': 'Количество слайдов должно быть от 1 до 10',
                    'data': {}
                }), 400
            SystemSetting.set_setting('carousel_max_slides', str(max_slides))
        
        return jsonify({
            'status': 'success',
            'message': 'Настройки карусели обновлены',
            'data': {}
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Ошибка обновления настроек: {str(e)}',
            'data': {}
        }), 500