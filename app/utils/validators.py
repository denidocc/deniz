"""Кастомные валидаторы."""

import re
from typing import Any, Optional

def validate_phone(phone: str) -> bool:
    """Валидация номера телефона."""
    pattern = r'^\+?1?\d{9,15}$'
    return bool(re.match(pattern, phone))

def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """Проверка силы пароля."""
    errors = []
    
    if len(password) < 8:
        errors.append("Пароль должен содержать минимум 8 символов")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Пароль должен содержать заглавную букву")
    
    if not re.search(r'[a-z]', password):
        errors.append("Пароль должен содержать строчную букву")
    
    if not re.search(r'\d', password):
        errors.append("Пароль должен содержать цифру")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Пароль должен содержать специальный символ")
    
    return len(errors) == 0, errors

def sanitize_input(value: Any) -> str:
    """Очистка пользовательского ввода."""
    if not isinstance(value, str):
        value = str(value)
    
    # Удаление потенциально опасных символов
    value = re.sub(r'[<>"\']', '', value)
    return value.strip()

def validate_table_number(table_number: int) -> bool:
    """Валидация номера стола."""
    return 1 <= table_number <= 50

def validate_guest_count(guest_count: int) -> bool:
    """Валидация количества гостей."""
    return 1 <= guest_count <= 20

def validate_price(price: float) -> bool:
    """Валидация цены."""
    return 0 <= price <= 10000

def validate_order_timeout(timeout_minutes: int) -> bool:
    """Валидация времени для отмены заказа."""
    return 1 <= timeout_minutes <= 30 