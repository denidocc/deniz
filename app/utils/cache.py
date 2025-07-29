"""Система кеширования."""

from functools import wraps
from flask import request, current_app
from app import cache
import json
import hashlib
from typing import Any, Optional, Callable

class CacheManager:
    """Менеджер кеширования."""
    
    def __init__(self, cache_instance):
        self.cache = cache_instance
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Генерация ключа кеша."""
        key_data = {
            'args': args,
            'kwargs': kwargs,
            'user_id': getattr(request, 'user_id', None) if request else None,
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def cached_result(self, timeout: int = 300, key_prefix: str = None):
        """Декоратор для кеширования результатов функций."""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if current_app.config.get('TESTING'):
                    return f(*args, **kwargs)
                
                prefix = key_prefix or f"func:{f.__name__}"
                key = self.generate_key(prefix, *args, **kwargs)
                
                # Попытка получить из кеша
                cached_result = self.cache.get(key)
                if cached_result is not None:
                    return cached_result
                
                # Выполнение функции и кеширование
                result = f(*args, **kwargs)
                self.cache.set(key, result, timeout=timeout)
                return result
            
            return decorated_function
        return decorator
    
    def invalidate_pattern(self, pattern: str) -> None:
        """Инвалидация кеша по паттерну."""
        try:
            import redis
            r = redis.from_url(current_app.config['CACHE_REDIS_URL'])
            keys = r.keys(pattern)
            if keys:
                r.delete(*keys)
                current_app.logger.info(f"Invalidated {len(keys)} cache keys")
        except Exception as e:
            current_app.logger.error(f"Cache invalidation failed: {e}")

# Глобальный экземпляр
cache_manager = CacheManager(cache)

# Использование:
# @cache_manager.cached_result(timeout=300)
# def get_all_users():
#     """Получение всех пользователей с кешированием"""
#     return User.query.filter_by(is_active=True).all() 