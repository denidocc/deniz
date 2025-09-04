"""API для работы с бонусными картами."""

from flask import Blueprint, request, jsonify
from app.models import BonusCard, Order
from app import db
from app.utils.decorators import auth_required
from app.errors import ValidationError

bonus_cards_bp = Blueprint('bonus_cards', __name__)



@bonus_cards_bp.route('/check', methods=['POST'])
def check_bonus_card():
    """Проверка бонусной карты."""
    try:
        from flask import current_app
        current_app.logger.info("=== BONUS CARD CHECK STARTED ===")
        
        data = request.get_json()
        current_app.logger.info(f"Request data: {data}")
        
        if not data or 'card_number' not in data:
            raise ValidationError("Номер карты обязателен")
        
        card_number = data['card_number'].strip()
        current_app.logger.info(f"Card number: {card_number}")
        
        if len(card_number) != 6 or not card_number.isdigit():
            raise ValidationError("Номер карты должен содержать 6 цифр")
        
        # Ищем карту
        current_app.logger.info("Searching for bonus card...")
        bonus_card = BonusCard.find_by_card_number(card_number)
        current_app.logger.info(f"Found card: {bonus_card}")
        
        if not bonus_card:
            current_app.logger.info("Card not found")
            return jsonify({
                'status': 'error',
                'message': 'Карта не найдена',
                'data': {
                    'card_number': card_number,
                    'reason': 'Карта с таким номером не существует'
                }
            }), 404
        
        # Проверяем валидность карты (с автоматической деактивацией)
        current_app.logger.info("Checking card validity...")
        is_valid = bonus_card.is_valid()
        current_app.logger.info(f"Card is valid: {is_valid}")
        
        if not is_valid:
            current_app.logger.info("Card is not valid")
            reason = bonus_card.get_invalidity_reason()
            return jsonify({
                'status': 'error',
                'message': 'Карта неактивна или срок действия истек',
                'data': {
                    'card': bonus_card.to_dict(),
                    'reason': reason,
                    'card_number': card_number
                }
            }), 400
        
        # Сериализуем карту
        current_app.logger.info("Serializing card...")
        card_dict = bonus_card.to_dict()
        current_app.logger.info(f"Card dict: {card_dict}")
        
        current_app.logger.info("=== BONUS CARD CHECK SUCCESS ===")
        return jsonify({
            'status': 'success',
            'message': 'Карта найдена',
            'data': {
                'card': card_dict
            }
        })
        
    except ValidationError as e:
        current_app.logger.error(f"Validation error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': {}
        }), 400
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Внутренняя ошибка сервера',
            'data': {}
        }), 500

@bonus_cards_bp.route('/verify', methods=['POST'])
def verify_bonus_card():
    """Верификация бонусной карты (алиас для /check)."""
    return check_bonus_card()

@bonus_cards_bp.route('/apply/<int:order_id>', methods=['POST'])
@auth_required
def apply_bonus_card(order_id):
    """Применение бонусной карты к заказу."""
    try:
        # Отладочная информация
        from flask import current_app
        current_app.logger.info(f"Applying bonus card to order {order_id}")
        current_app.logger.info(f"Request data: {request.get_data()}")
        current_app.logger.info(f"Request headers: {dict(request.headers)}")
        
        try:
            data = request.get_json()
            current_app.logger.info(f"Parsed JSON data: {data}")
        except Exception as e:
            current_app.logger.error(f"Error parsing JSON: {e}")
            return jsonify({
                'status': 'error',
                'message': 'Неверный формат JSON',
                'data': {}
            }), 400
        
        if not data:
            current_app.logger.error("No JSON data received")
            return jsonify({
                'status': 'error',
                'message': 'Отсутствуют данные запроса',
                'data': {}
            }), 400
            
        if 'card_number' not in data:
            current_app.logger.error(f"Missing card_number in data: {data}")
            raise ValidationError("Номер карты обязателен")
        
        card_number = data['card_number'].strip()
        
        if len(card_number) != 5 or not card_number.isdigit():
            raise ValidationError("Номер карты должен содержать 5 цифр")
        
        # Находим заказ
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'status': 'error',
                'message': 'Заказ не найден',
                'data': {}
            }), 404
        
        # Проверяем, что заказ в подходящем статусе для применения карты
        if order.status not in ['pending', 'confirmed']:
            return jsonify({
                'status': 'error',
                'message': 'Бонусную карту можно применить только к новым или подтвержденным заказам',
                'data': {}
            }), 400
        
        # Ищем карту
        bonus_card = BonusCard.find_by_card_number(card_number)
        
        if not bonus_card:
            return jsonify({
                'status': 'error',
                'message': 'Карта не найдена или неактивна',
                'data': {}
            }), 404
        
        # Применяем карту к заказу
        bonus_card.apply_to_order(order)
        
        # Пересчитываем итоги
        order.calculate_totals()
        
        # Сохраняем изменения
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Карта {card_number} применена. Скидка: {bonus_card.discount_percent}%',
            'data': {
                'order': order.to_dict(),
                'bonus_card': bonus_card.to_dict()
            }
        })
        
    except ValidationError as e:
        current_app.logger.error(f"Validation error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': {}
        }), 400
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Внутренняя ошибка сервера',
            'data': {}
        }), 500

@bonus_cards_bp.route('/remove/<int:order_id>', methods=['POST'])
@auth_required
def remove_bonus_card(order_id):
    """Удаление бонусной карты из заказа."""
    try:
        # Находим заказ
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'status': 'error',
                'message': 'Заказ не найден',
                'data': {}
            }), 404
        
        # Проверяем, что заказ в подходящем статусе для удаления карты
        if order.status not in ['pending', 'confirmed']:
            return jsonify({
                'status': 'error',
                'message': 'Бонусную карту можно удалить только у новых или подтвержденных заказов',
                'data': {}
            }), 400
        
        # Удаляем карту из заказа
        order.bonus_card_id = None
        order.discount_amount = 0
        
        # Пересчитываем итоги
        order.calculate_totals()
        
        # Сохраняем изменения
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Бонусная карта удалена из заказа',
            'data': {
                'order': order.to_dict()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Внутренняя ошибка сервера',
            'data': {}
        }), 500