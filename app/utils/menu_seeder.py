"""
Утилита для заполнения меню тестовыми данными.

Создает категории и блюда для тестирования API меню.
"""

import sys
import os
from typing import Dict, Any
import logging

# Добавляем путь к корневой директории проекта
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models import MenuCategory, MenuItem, MenuItemSize

logger = logging.getLogger(__name__)


class MenuSeeder:
    """Класс для заполнения меню тестовыми данными."""
    
    @staticmethod
    def seed_menu() -> Dict[str, Any]:
        """
        Заполнение меню тестовыми данными.
        
        Returns:
            Dict с результатом операции
        """
        try:
            # Проверка существования данных
            if MenuCategory.query.count() > 0:
                return {
                    "status": "info",
                    "message": "Меню уже содержит данные"
                }
            
            # Создание категорий
            categories = [
                {
                    "name_ru": "Горячие блюда",
                    "name_tk": "Ысык ашлар",
                    "name_en": "Hot dishes",
                    "sort_order": 1
                },
                {
                    "name_ru": "Холодные закуски",
                    "name_tk": "Совук закускалар",
                    "name_en": "Cold appetizers",
                    "sort_order": 2
                },
                {
                    "name_ru": "Салаты",
                    "name_tk": "Салатлар",
                    "name_en": "Salads",
                    "sort_order": 3
                },
                {
                    "name_ru": "Напитки",
                    "name_tk": "Ичимликлер",
                    "name_en": "Beverages",
                    "sort_order": 4
                },
                {
                    "name_ru": "Десерты",
                    "name_tk": "Татлылар",
                    "name_en": "Desserts",
                    "sort_order": 5
                }
            ]
            
            created_categories = []
            for cat_data in categories:
                category = MenuCategory(**cat_data)
                db.session.add(category)
                created_categories.append(category)
            
            db.session.flush()  # Получаем ID категорий
            
            # Создание блюд
            menu_items = [
                # Горячие блюда
                {
                    "category_id": created_categories[0].id,
                    "name_ru": "Борщ классический",
                    "name_tk": "Классик борщ",
                    "name_en": "Classic Borscht",
                    "description_ru": "Традиционный украинский борщ с говядиной",
                    "description_tk": "Говядина билен украин борщ",
                    "description_en": "Traditional Ukrainian borscht with beef",
                    "price": 300.00,
                    "image_url": "/images/borsch.jpg",
                    "preparation_type": "kitchen",
                    "estimated_time": 20,
                    "has_size_options": False,
                    "can_modify_ingredients": True,
                    "sort_order": 1
                },
                {
                    "category_id": created_categories[0].id,
                    "name_ru": "Стейк из говядины",
                    "name_tk": "Говядина стейк",
                    "name_en": "Beef Steak",
                    "description_ru": "Сочный стейк из говядины с овощами",
                    "description_tk": "Совук говядина стейк яшылчык билен",
                    "description_en": "Juicy beef steak with vegetables",
                    "price": 850.00,
                    "image_url": "/images/steak.jpg",
                    "preparation_type": "kitchen",
                    "estimated_time": 25,
                    "has_size_options": True,
                    "can_modify_ingredients": True,
                    "sort_order": 2
                },
                {
                    "category_id": created_categories[0].id,
                    "name_ru": "Куриная грудка",
                    "name_tk": "Тавук гөвүш",
                    "name_en": "Chicken Breast",
                    "description_ru": "Нежная куриная грудка с гарниром",
                    "description_tk": "Назык тавук гөвүш гарнир билен",
                    "description_en": "Tender chicken breast with side dish",
                    "price": 450.00,
                    "image_url": "/images/chicken.jpg",
                    "preparation_type": "kitchen",
                    "estimated_time": 15,
                    "has_size_options": False,
                    "can_modify_ingredients": True,
                    "sort_order": 3
                },
                
                # Холодные закуски
                {
                    "category_id": created_categories[1].id,
                    "name_ru": "Сельдь под шубой",
                    "name_tk": "Шуба астында селдка",
                    "name_en": "Herring under a fur coat",
                    "description_ru": "Классическая русская закуска",
                    "description_tk": "Классик рус закуска",
                    "description_en": "Classic Russian appetizer",
                    "price": 250.00,
                    "image_url": "/images/herring.jpg",
                    "preparation_type": "kitchen",
                    "estimated_time": 10,
                    "has_size_options": False,
                    "can_modify_ingredients": False,
                    "sort_order": 1
                },
                
                # Салаты
                {
                    "category_id": created_categories[2].id,
                    "name_ru": "Цезарь с курицей",
                    "name_tk": "Тавук билен Цезарь",
                    "name_en": "Caesar with chicken",
                    "description_ru": "Салат Цезарь с куриным филе",
                    "description_tk": "Тавук филе билен Цезарь салат",
                    "description_en": "Caesar salad with chicken fillet",
                    "price": 350.00,
                    "image_url": "/images/caesar.jpg",
                    "preparation_type": "kitchen",
                    "estimated_time": 12,
                    "has_size_options": False,
                    "can_modify_ingredients": True,
                    "sort_order": 1
                },
                {
                    "category_id": created_categories[2].id,
                    "name_ru": "Греческий салат",
                    "name_tk": "Грек салат",
                    "name_en": "Greek salad",
                    "description_ru": "Свежий греческий салат с фетой",
                    "description_tk": "Тазе грек салат фета билен",
                    "description_en": "Fresh Greek salad with feta",
                    "price": 280.00,
                    "image_url": "/images/greek.jpg",
                    "preparation_type": "kitchen",
                    "estimated_time": 8,
                    "has_size_options": False,
                    "can_modify_ingredients": True,
                    "sort_order": 2
                },
                
                # Напитки
                {
                    "category_id": created_categories[3].id,
                    "name_ru": "Кофе эспрессо",
                    "name_tk": "Эспрессо кофе",
                    "name_en": "Espresso coffee",
                    "description_ru": "Крепкий итальянский эспрессо",
                    "description_tk": "Гүчлиително итальян эспрессо",
                    "description_en": "Strong Italian espresso",
                    "price": 120.00,
                    "image_url": "/images/espresso.jpg",
                    "preparation_type": "bar",
                    "estimated_time": 3,
                    "has_size_options": False,
                    "can_modify_ingredients": False,
                    "sort_order": 1
                },
                {
                    "category_id": created_categories[3].id,
                    "name_ru": "Кола",
                    "name_tk": "Кола",
                    "name_en": "Cola",
                    "description_ru": "Газированный напиток Кола",
                    "description_tk": "Газландырылмыш кола ичимлик",
                    "description_en": "Carbonated Cola beverage",
                    "price": 100.00,
                    "image_url": "/images/cola.jpg",
                    "preparation_type": "bar",
                    "estimated_time": 1,
                    "has_size_options": True,
                    "can_modify_ingredients": False,
                    "sort_order": 2
                },
                {
                    "category_id": created_categories[3].id,
                    "name_ru": "Сок апельсиновый",
                    "name_tk": "Портгал сок",
                    "name_en": "Orange juice",
                    "description_ru": "Свежевыжатый апельсиновый сок",
                    "description_tk": "Тазе сыхылмыш портгал сок",
                    "description_en": "Freshly squeezed orange juice",
                    "price": 150.00,
                    "image_url": "/images/orange_juice.jpg",
                    "preparation_type": "bar",
                    "estimated_time": 2,
                    "has_size_options": True,
                    "can_modify_ingredients": False,
                    "sort_order": 3
                },
                
                # Десерты
                {
                    "category_id": created_categories[4].id,
                    "name_ru": "Тирамису",
                    "name_tk": "Тирамису",
                    "name_en": "Tiramisu",
                    "description_ru": "Итальянский десерт с кофе",
                    "description_tk": "Кофе билен итальян татлы",
                    "description_en": "Italian dessert with coffee",
                    "price": 280.00,
                    "image_url": "/images/tiramisu.jpg",
                    "preparation_type": "kitchen",
                    "estimated_time": 5,
                    "has_size_options": False,
                    "can_modify_ingredients": False,
                    "sort_order": 1
                },
                {
                    "category_id": created_categories[4].id,
                    "name_ru": "Чизкейк",
                    "name_tk": "Чизкейк",
                    "name_en": "Cheesecake",
                    "description_ru": "Классический чизкейк с ягодами",
                    "description_tk": "Гилле билен классик чизкейк",
                    "description_en": "Classic cheesecake with berries",
                    "price": 320.00,
                    "image_url": "/images/cheesecake.jpg",
                    "preparation_type": "kitchen",
                    "estimated_time": 3,
                    "has_size_options": False,
                    "can_modify_ingredients": False,
                    "sort_order": 2
                }
            ]
            
            created_items = []
            for item_data in menu_items:
                item = MenuItem(**item_data)
                db.session.add(item)
                created_items.append(item)
            
            db.session.flush()  # Получаем ID блюд
            
            # Создание размеров порций для блюд с опциями размеров
            sizes_data = [
                # Размеры для стейка
                {
                    "menu_item_id": created_items[1].id,  # Стейк
                    "size_name_ru": "Маленькая порция",
                    "size_name_tk": "Кичик порция",
                    "size_name_en": "Small portion",
                    "price_modifier": 0.00,
                    "sort_order": 1
                },
                {
                    "menu_item_id": created_items[1].id,  # Стейк
                    "size_name_ru": "Большая порция",
                    "size_name_tk": "Улкан порция",
                    "size_name_en": "Large portion",
                    "price_modifier": 150.00,
                    "sort_order": 2
                },
                
                # Размеры для колы
                {
                    "menu_item_id": created_items[6].id,  # Кола
                    "size_name_ru": "0.33л",
                    "size_name_tk": "0.33л",
                    "size_name_en": "0.33L",
                    "price_modifier": 0.00,
                    "sort_order": 1
                },
                {
                    "menu_item_id": created_items[6].id,  # Кола
                    "size_name_ru": "0.5л",
                    "size_name_tk": "0.5л",
                    "size_name_en": "0.5L",
                    "price_modifier": 30.00,
                    "sort_order": 2
                },
                {
                    "menu_item_id": created_items[6].id,  # Кола
                    "size_name_ru": "1л",
                    "size_name_tk": "1л",
                    "size_name_en": "1L",
                    "price_modifier": 50.00,
                    "sort_order": 3
                },
                
                # Размеры для сока
                {
                    "menu_item_id": created_items[7].id,  # Сок
                    "size_name_ru": "200мл",
                    "size_name_tk": "200мл",
                    "size_name_en": "200ml",
                    "price_modifier": 0.00,
                    "sort_order": 1
                },
                {
                    "menu_item_id": created_items[7].id,  # Сок
                    "size_name_ru": "300мл",
                    "size_name_tk": "300мл",
                    "size_name_en": "300ml",
                    "price_modifier": 50.00,
                    "sort_order": 2
                }
            ]
            
            for size_data in sizes_data:
                size = MenuItemSize(**size_data)
                db.session.add(size)
            
            db.session.commit()
            
            logger.info(f"Menu seeded successfully: {len(created_categories)} categories, {len(created_items)} items")
            
            return {
                "status": "success",
                "message": f"Меню заполнено: {len(created_categories)} категорий, {len(created_items)} блюд"
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Menu seeding failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Ошибка при заполнении меню: {str(e)}"
            }


if __name__ == "__main__":
    """Запуск заполнения меню из командной строки."""
    app = create_app()
    
    with app.app_context():
        print("Заполнение меню тестовыми данными...")
        result = MenuSeeder.seed_menu()
        print(f"Результат: {result['message']}")
        
        if result["status"] == "error":
            sys.exit(1)
        else:
            print("✅ Меню успешно заполнено!") 