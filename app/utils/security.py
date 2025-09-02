"""Middleware и утилиты безопасности."""

from flask import Flask, request, abort, current_app, g
import re
from datetime import datetime, timedelta
from typing import Set, List, Dict, Any
import ipaddress
import hashlib
import time

class SecurityMiddleware:
    """Middleware для дополнительной безопасности."""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.blocked_ips: Set[str] = set()
        self.rate_limit_store: Dict[str, List[float]] = {}
        self.suspicious_patterns = [
            r'<script.*?>.*?</script>',  # XSS
            r'union.*select',            # SQL injection
            r'drop.*table',              # SQL injection
            r'exec\s*\(',               # Code injection
            r'\.\./',                   # Path traversal
            r'/etc/passwd',             # File access
            r'<iframe',                 # Iframe injection
            r'javascript:',             # Javascript injection
            r'vbscript:',              # VBScript injection
            r'onload\s*=',             # Event handler injection
            r'onerror\s*=',            # Event handler injection
        ]
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Инициализация middleware."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Настройки безопасности
        self.max_requests_per_minute = app.config.get('SECURITY_MAX_REQUESTS_PER_MINUTE', 100)
        self.request_timeout = app.config.get('SECURITY_REQUEST_TIMEOUT', 30)
        self.enable_ip_blocking = app.config.get('SECURITY_ENABLE_IP_BLOCKING', True)
        self.enable_content_filtering = app.config.get('SECURITY_ENABLE_CONTENT_FILTERING', True)
    
    def before_request(self):
        """Проверки перед обработкой запроса."""
        try:
            current_app.logger.info(f"Security check for: {request.method} {request.path}")
            current_app.logger.info(f"User-Agent: {request.headers.get('User-Agent', 'None')}")
            
            # Проверка IP адреса
            if self.enable_ip_blocking and self.is_ip_blocked(request.remote_addr):
                current_app.logger.warning(f"Blocked IP attempted access: {request.remote_addr}")
                abort(403)
            
            # Проверка rate limiting
            if not self.check_rate_limit(request.remote_addr):
                current_app.logger.warning(f"Rate limit exceeded for IP: {request.remote_addr}")
                abort(429)
            
            # Проверка на подозрительные паттерны
            if self.enable_content_filtering and self.has_suspicious_content():
                current_app.logger.warning(
                    f"SECURITY: Suspicious content detected from {request.remote_addr}: {request.url}"
                )
                self.block_ip(request.remote_addr, "Suspicious content detected")
                abort(400)
            
            # Проверка размера запроса
            max_content_length = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
            if request.content_length and request.content_length > max_content_length:
                current_app.logger.warning(f"SECURITY: Request too large from {request.remote_addr}: {request.content_length}")
                abort(413)
            
            # Проверка User-Agent
            user_agent = request.headers.get('User-Agent', '')
            if not self.is_valid_user_agent(user_agent):
                current_app.logger.warning(f"SECURITY: Invalid User-Agent from {request.remote_addr}: {user_agent}")
                abort(400)
            
            # Добавление security headers в g для использования в after_request
            g.security_start_time = time.time()
            
        except Exception as e:
            current_app.logger.error(f"Security middleware error: {e}", exc_info=True)
            # В случае ошибки в middleware, не блокируем запрос полностью
    
    def after_request(self, response):
        """Установка заголовков безопасности."""
        try:
            # HSTS (Strict Transport Security)
            if request.is_secure:
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
            
            # Предотвращение clickjacking
            response.headers['X-Frame-Options'] = 'DENY'
            
            # XSS защита
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Content type sniffing
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            # Referrer policy
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Permissions policy
            response.headers['Permissions-Policy'] = (
                'geolocation=(), microphone=(), camera=(), '
                'payment=(), usb=(), magnetometer=(), accelerometer=(), gyroscope=()'
            )
            
            # CSP (Content Security Policy)
            if not current_app.debug:
                csp_policy = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: https:; "
                    "font-src 'self' https:; "
                    "connect-src 'self'; "
                    "frame-ancestors 'none'; "
                    "base-uri 'self'; "
                    "form-action 'self';"
                )
                response.headers['Content-Security-Policy'] = csp_policy
            
            # Логирование времени обработки
            if hasattr(g, 'security_start_time'):
                duration = time.time() - g.security_start_time
                if duration > 1.0:  # Логируем только медленные запросы
                    current_app.logger.warning(f"Slow request: {duration:.2f}s for {request.path}")
            
        except Exception as e:
            current_app.logger.error(f"Security headers error: {e}", exc_info=True)
        
        return response
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Проверка, заблокирован ли IP."""
        if not ip:
            return False
        return ip in self.blocked_ips
    
    def block_ip(self, ip: str, reason: str = "Security violation"):
        """Блокировка IP адреса."""
        if ip and self.enable_ip_blocking:
            self.blocked_ips.add(ip)
            current_app.logger.warning(f"IP blocked: {ip}, reason: {reason}")
    
    def unblock_ip(self, ip: str):
        """Разблокировка IP адреса."""
        if ip in self.blocked_ips:
            self.blocked_ips.remove(ip)
            current_app.logger.info(f"IP unblocked: {ip}")
    
    def check_rate_limit(self, ip: str) -> bool:
        """Проверка rate limiting."""
        if not ip:
            return True
        
        now = time.time()
        minute_ago = now - 60
        
        # Очистка старых записей
        if ip in self.rate_limit_store:
            self.rate_limit_store[ip] = [
                timestamp for timestamp in self.rate_limit_store[ip] 
                if timestamp > minute_ago
            ]
        else:
            self.rate_limit_store[ip] = []
        
        # Проверка лимита
        if len(self.rate_limit_store[ip]) >= self.max_requests_per_minute:
            return False
        
        # Добавление текущего запроса
        self.rate_limit_store[ip].append(now)
        return True
    
    def has_suspicious_content(self) -> bool:
        """Проверка на подозрительный контент."""
        # Для API endpoints отключаем строгую проверку
        if request.path.startswith('/api/') or request.path.startswith('/client/api/'):
            return False
            
        content_to_check = [
            request.url,
            request.get_data(as_text=True) if request.content_length else '',
            str(request.headers),
            ' '.join(request.args.values()),
        ]
        
        for content in content_to_check:
            if content:
                content_lower = content.lower()
                for pattern in self.suspicious_patterns:
                    if re.search(pattern, content_lower, re.IGNORECASE):
                        return True
        
        return False
    
    def is_valid_user_agent(self, user_agent: str) -> bool:
        """Проверка валидности User-Agent."""
        if not user_agent:
            return True  # Разрешаем пустой User-Agent
        
        # Проверка на подозрительные User-Agent
        suspicious_agents = [
            'sqlmap',
            'nikto',
            'nmap',
            'masscan',
            'curl',  # Можно разрешить для API
            'wget',
            'python-requests',  # Можно разрешить для API
        ]
        
        user_agent_lower = user_agent.lower()
        
        # Для API endpoints разрешаем программные User-Agent
        if request.path.startswith('/api/') or request.path.startswith('/client/api/'):
            return True
        
        # Блокируем известные сканеры для веб-интерфейса
        for suspicious in suspicious_agents[:6]:  # Исключаем curl, wget, python-requests для API
            if suspicious in user_agent_lower:
                return False
        
        return True
    
    def get_client_info(self) -> Dict[str, Any]:
        """Получение информации о клиенте."""
        return {
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'referer': request.headers.get('Referer', ''),
            'method': request.method,
            'path': request.path,
            'query_string': request.query_string.decode(),
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Логирование событий безопасности."""
        event_data = {
            'event_type': event_type,
            'client_info': self.get_client_info(),
            'details': details,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        current_app.logger.warning(f"Security event: {event_type}", extra=event_data)

# Глобальный экземпляр
security_middleware = SecurityMiddleware()

def init_security(app: Flask):
    """Инициализация системы безопасности."""
    security_middleware.init_app(app)
    app.logger.info("Security middleware initialized")
    
    return security_middleware 