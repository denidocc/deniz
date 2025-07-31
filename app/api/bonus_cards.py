"""API для работы с бонусными картами."""

from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import BonusCard, Staff
from app.utils.decorators import admin_required
from app.errors import ValidationError, BusinessLogicError
from datetime import datetime, date
import re

bonus_cards_api = Blueprint('bonus_cards_api', __name__)


@bonus_cards_api.route('/verify', methods=['POST'])
def verify_bonus_card():
    """Проверка бонусной карты клиентом."""
    try:
        data = request.get_json()
        
        if not data or 'card_number' not in data:
            raise ValidationError("Номер карты не указан", field="card_number")
        
        card_number = data['card_number'].strip()
        
        # Валидация номера карты (6 цифр)
        if not re.match(r'^\d{6}$', card_number):
            raise ValidationError("Номер карты должен содержать 6 цифр", field="card_number")
        
        # Поиск карты
        card = BonusCard.find_by_number(card_number)
        
        if not card:
            return jsonify({
                "status": "error",
                "message": "Карта не найдена",
                "data": {}
            }), 404
        
        if not card.is_valid():
            return jsonify({
                "status": "error",
                "message": "Карта недействительна или просрочена",
                "data": {}
            }), 400
        
        return jsonify({
            "status": "success",
            "message": "Карта найдена",
            "data": {
                "card_number": card.card_number,
                "client_name": card.client_name,
                "discount_percent": card.discount_percent,
                "is_valid": True
            }
        })
        
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "message": e.message,
            "errors": {e.field: e.message} if e.field else None,
            "data": {}
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error verifying bonus card: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка проверки карты",
            "data": {}
        }), 500


@bonus_cards_api.route('/', methods=['GET'])
@admin_required
def get_bonus_cards():
    """Получение списка бонусных карт (админка)."""
    try:
        # Параметры фильтрации
        is_active = request.args.get('is_active')
        is_valid = request.args.get('is_valid')
        search = request.args.get('search', '').strip()
        
        # Пагинация
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Базовый запрос
        query = BonusCard.query
        
        # Фильтры
        if is_active is not None:
            query = query.filter(BonusCard.is_active == (is_active.lower() == 'true'))
        
        if search:
            query = query.filter(
                db.or_(
                    BonusCard.card_number.contains(search),
                    BonusCard.client_name.ilike(f'%{search}%'),
                    BonusCard.client_phone.contains(search) if BonusCard.client_phone else False
                )
            )
        
        # Сортировка
        query = query.order_by(BonusCard.created_at.desc())
        
        # Пагинация
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        cards = []
        for card in pagination.items:
            card_data = card.to_dict(include_sensitive=True)
            if card.created_by:
                card_data['created_by_name'] = card.created_by.name
            cards.append(card_data)
        
        return jsonify({
            "status": "success",
            "message": "Карты получены",
            "data": {
                "cards": cards,
                "pagination": {
                    "page": pagination.page,
                    "pages": pagination.pages,
                    "per_page": pagination.per_page,
                    "total": pagination.total,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting bonus cards: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка получения карт",
            "data": {}
        }), 500


@bonus_cards_api.route('/', methods=['POST'])
@admin_required
def create_bonus_card():
    """Создание новой бонусной карты."""
    try:
        data = request.get_json()
        
        # Валидация данных
        required_fields = ['card_number', 'client_name', 'discount_percent']
        for field in required_fields:
            if not data or field not in data or not data[field]:
                raise ValidationError(f"Поле {field} обязательно", field=field)
        
        card_number = data['card_number'].strip()
        client_name = data['client_name'].strip()
        discount_percent = int(data['discount_percent'])
        
        # Валидация номера карты
        if not re.match(r'^\d{6}$', card_number):
            raise ValidationError("Номер карты должен содержать 6 цифр", field="card_number")
        
        # Проверка уникальности
        if BonusCard.find_by_number(card_number):
            raise ValidationError("Карта с таким номером уже существует", field="card_number")
        
        # Валидация скидки
        if not 0 <= discount_percent <= 50:
            raise ValidationError("Скидка должна быть от 0 до 50%", field="discount_percent")
        
        # Создание карты
        card = BonusCard(
            card_number=card_number,
            client_name=client_name,
            discount_percent=discount_percent
        )
        
        # Дополнительные поля
        if 'client_phone' in data and data['client_phone']:
            card.client_phone = data['client_phone'].strip()
        
        if 'notes' in data and data['notes']:
            card.notes = data['notes'].strip()
        
        # Сроки действия
        if 'valid_until' in data and data['valid_until']:
            try:
                card.valid_until = datetime.strptime(data['valid_until'], '%Y-%m-%d').date()
            except ValueError:
                raise ValidationError("Неверный формат даты окончания", field="valid_until")
        
        # Добавляем информацию о создателе
        from flask_login import current_user
        if current_user.is_authenticated:
            card.created_by_staff_id = current_user.id
        
        db.session.add(card)
        db.session.commit()
        
        current_app.logger.info(f"Bonus card {card_number} created by staff {current_user.id if current_user.is_authenticated else 'unknown'}")
        
        return jsonify({
            "status": "success",
            "message": "Бонусная карта создана",
            "data": card.to_dict(include_sensitive=True)
        }), 201
        
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "message": e.message,
            "errors": {e.field: e.message} if e.field else None,
            "data": {}
        }), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating bonus card: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка создания карты",
            "data": {}
        }), 500


@bonus_cards_api.route('/<string:card_number>', methods=['PUT'])
@admin_required
def update_bonus_card(card_number):
    """Обновление бонусной карты."""
    try:
        card = BonusCard.find_by_number(card_number)
        if not card:
            return jsonify({
                "status": "error",
                "message": "Карта не найдена",
                "data": {}
            }), 404
        
        data = request.get_json()
        
        # Обновляемые поля
        if 'client_name' in data:
            card.client_name = data['client_name'].strip()
        
        if 'client_phone' in data:
            card.client_phone = data['client_phone'].strip() if data['client_phone'] else None
        
        if 'discount_percent' in data:
            discount_percent = int(data['discount_percent'])
            if not 0 <= discount_percent <= 50:
                raise ValidationError("Скидка должна быть от 0 до 50%", field="discount_percent")
            card.discount_percent = discount_percent
        
        if 'notes' in data:
            card.notes = data['notes'].strip() if data['notes'] else None
        
        if 'is_active' in data:
            card.is_active = bool(data['is_active'])
        
        if 'valid_until' in data:
            if data['valid_until']:
                try:
                    card.valid_until = datetime.strptime(data['valid_until'], '%Y-%m-%d').date()
                except ValueError:
                    raise ValidationError("Неверный формат даты окончания", field="valid_until")
            else:
                card.valid_until = None
        
        db.session.commit()
        
        current_app.logger.info(f"Bonus card {card_number} updated")
        
        return jsonify({
            "status": "success",
            "message": "Карта обновлена",
            "data": card.to_dict(include_sensitive=True)
        })
        
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "message": e.message,
            "errors": {e.field: e.message} if e.field else None,
            "data": {}
        }), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating bonus card: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка обновления карты",
            "data": {}
        }), 500


@bonus_cards_api.route('/<string:card_number>', methods=['DELETE'])
@admin_required
def delete_bonus_card(card_number):
    """Удаление бонусной карты."""
    try:
        card = BonusCard.find_by_number(card_number)
        if not card:
            return jsonify({
                "status": "error",
                "message": "Карта не найдена",
                "data": {}
            }), 404
        
        db.session.delete(card)
        db.session.commit()
        
        current_app.logger.info(f"Bonus card {card_number} deleted")
        
        return jsonify({
            "status": "success",
            "message": "Карта удалена",
            "data": {}
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting bonus card: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка удаления карты",
            "data": {}
        }), 500


@bonus_cards_api.route('/statistics', methods=['GET'])
@admin_required
def get_bonus_cards_statistics():
    """Получение статистики по бонусным картам."""
    try:
        stats = BonusCard.get_statistics()
        
        return jsonify({
            "status": "success",
            "message": "Статистика получена",
            "data": stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting bonus cards statistics: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка получения статистики",
            "data": {}
        }), 500