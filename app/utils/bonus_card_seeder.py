"""Утилита для заполнения тестовых бонусных карт."""

from app import db
from app.models import BonusCard
from typing import Dict, Any

class BonusCardSeeder:
    """Класс для заполнения бонусных карт."""
    
    @staticmethod
    def seed_bonus_cards() -> Dict[str, Any]:
        """Заполнение бонусных карт тестовыми данными."""
        try:
            # Проверяем, есть ли уже карты
            if BonusCard.query.count() > 0:
                return {"status": "info", "message": "Бонусные карты уже существуют"}
            
            # Создаем тестовые карты
            test_cards = [
                {
                    'card_number': '123456',
                    'discount_percent': 10,
                    'is_active': True
                },
                {
                    'card_number': '234567',
                    'discount_percent': 15,
                    'is_active': True
                },
                {
                    'card_number': '345678',
                    'discount_percent': 20,
                    'is_active': True
                },
                {
                    'card_number': '456789',
                    'discount_percent': 5,
                    'is_active': True
                },
                {
                    'card_number': '567890',
                    'discount_percent': 25,
                    'is_active': True
                }
            ]
            
            # Создаем карты
            for card_data in test_cards:
                card = BonusCard(**card_data)
                db.session.add(card)
            
            db.session.commit()
            
            return {
                "status": "success", 
                "message": f"Создано {len(test_cards)} бонусных карт"
            }
            
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def get_test_cards_info() -> Dict[str, Any]:
        """Получение информации о тестовых картах."""
        cards = BonusCard.query.filter_by(is_active=True).all()
        
        return {
            "status": "success",
            "message": f"Найдено {len(cards)} активных карт",
            "data": {
                "cards": [card.to_dict() for card in cards]
            }
        } 