#!/usr/bin/env python3
"""Тестовый скрипт для проверки API статусов заказов."""

import requests
import json

def test_order_statuses_api():
    """Тестирование API статусов заказов."""
    
    # Базовый URL (замените на ваш)
    base_url = "http://localhost:5000"
    
    try:
        # Тестируем endpoint статусов
        print("🔍 Тестируем API статусов заказов...")
        
        response = requests.get(f"{base_url}/waiter/api/order-statuses")
        
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API работает!")
            print(f"📋 Получено статусов: {len(data.get('data', []))}")
            
            for status in data.get('data', []):
                print(f"  📌 {status['code']}: {status['name']}")
                print(f"     Цвет: {status['color']}, Иконка: {status['icon']}")
                print(f"     Переходы: {status['can_transition_to']}")
                print()
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к серверу")
        print("💡 Убедитесь, что Flask приложение запущено")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    test_order_statuses_api()
