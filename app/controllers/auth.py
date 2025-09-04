"""Контроллер аутентификации."""

from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import LoginForm
from app.models import Staff, SystemSetting
from app.errors import ValidationError, AuthenticationError, AuthorizationError
from app.utils.decorators import audit_action, admin_required
from app import db
from datetime import datetime, timedelta
from typing import Dict

auth_bp = Blueprint('auth', __name__)

# Хранилище попыток входа (в продакшене лучше использовать Redis)
login_attempts: Dict[str, Dict] = {}

def get_client_ip() -> str:
    """Получить реальный IP адрес клиента."""
    # Проверяем заголовки прокси в порядке приоритета
    if request.headers.get('X-Forwarded-For'):
        # X-Forwarded-For может содержать несколько IP через запятую
        # Берем первый (самый близкий к клиенту)
        forwarded_ips = request.headers.get('X-Forwarded-For').split(',')
        client_ip = forwarded_ips[0].strip()
        current_app.logger.debug(f"Client IP from X-Forwarded-For: {client_ip}")
        return client_ip
    elif request.headers.get('X-Real-IP'):
        client_ip = request.headers.get('X-Real-IP').strip()
        current_app.logger.debug(f"Client IP from X-Real-IP: {client_ip}")
        return client_ip
    elif request.headers.get('CF-Connecting-IP'):  # Cloudflare
        client_ip = request.headers.get('CF-Connecting-IP').strip()
        current_app.logger.debug(f"Client IP from CF-Connecting-IP: {client_ip}")
        return client_ip
    else:
        # Fallback к стандартному remote_addr
        client_ip = request.remote_addr or 'unknown'
        
        # Дополнительная информация для отладки в локальных сетях
        user_agent = request.headers.get('User-Agent', 'Unknown')
        current_app.logger.debug(f"Client IP from remote_addr: {client_ip}, User-Agent: {user_agent[:100]}")
        
        # В локальной сети каждое устройство должно иметь свой IP
        # Например: 192.168.100.101, 192.168.100.102, и т.д.
        if client_ip.startswith(('192.168.', '10.', '172.')):
            current_app.logger.info(f"Local network client: {client_ip}")
        
        return client_ip

def get_login_attempts(ip: str) -> Dict:
    """Получить информацию о попытках входа для IP."""
    return login_attempts.get(ip, {'count': 0, 'blocked_until': None, 'attempts': []})

def record_failed_login(ip: str):
    """Записать неудачную попытку входа."""
    max_attempts = int(SystemSetting.get_setting('max_login_attempts', '5'))
    block_duration = int(SystemSetting.get_setting('block_duration', '30'))
    
    if ip not in login_attempts:
        login_attempts[ip] = {'count': 0, 'blocked_until': None, 'attempts': []}
    
    login_attempts[ip]['count'] += 1
    login_attempts[ip]['attempts'].append(datetime.now())
    
    # Очистка старых попыток (старше часа)
    hour_ago = datetime.now() - timedelta(hours=1)
    login_attempts[ip]['attempts'] = [
        attempt for attempt in login_attempts[ip]['attempts'] 
        if attempt > hour_ago
    ]
    
    # Обновляем счетчик на основе попыток за последний час
    login_attempts[ip]['count'] = len(login_attempts[ip]['attempts'])
    
    # Блокировка при превышении лимита
    if login_attempts[ip]['count'] >= max_attempts:
        login_attempts[ip]['blocked_until'] = datetime.now() + timedelta(minutes=block_duration)
        current_app.logger.warning(f"IP {ip} blocked for {block_duration} minutes after {max_attempts} failed login attempts")

def clear_login_attempts(ip: str):
    """Очистить попытки входа для IP после успешного входа."""
    if ip in login_attempts:
        del login_attempts[ip]

def is_ip_blocked(ip: str) -> bool:
    """Проверить, заблокирован ли IP."""
    if ip not in login_attempts:
        return False
    
    blocked_until = login_attempts[ip].get('blocked_until')
    if blocked_until and datetime.now() < blocked_until:
        return True
    
    # Разблокировать если время истекло
    if blocked_until and datetime.now() >= blocked_until:
        current_app.logger.info(f"IP {ip} automatically unblocked after timeout")
        login_attempts[ip]['blocked_until'] = None
        login_attempts[ip]['count'] = 0
        login_attempts[ip]['attempts'] = []
    
    return False

def cleanup_expired_blocks():
    """Очистить истекшие блокировки."""
    current_time = datetime.now()
    expired_ips = []
    
    for ip, data in login_attempts.items():
        blocked_until = data.get('blocked_until')
        if blocked_until and current_time >= blocked_until:
            expired_ips.append(ip)
    
    for ip in expired_ips:
        current_app.logger.info(f"Cleaning up expired block for IP {ip}")
        login_attempts[ip]['blocked_until'] = None
        login_attempts[ip]['count'] = 0
        login_attempts[ip]['attempts'] = []

@auth_bp.route('/login', methods=['GET', 'POST'])
@audit_action("user_login_attempt", table_affected=False, order_affected=False)
def login():
    """Вход в систему."""
    client_ip = get_client_ip()
    
    # Проверка блокировки IP
    if is_ip_blocked(client_ip):
        attempts_info = get_login_attempts(client_ip)
        blocked_until = attempts_info.get('blocked_until')
        if blocked_until:
            time_left = blocked_until - datetime.now()
            total_seconds = int(time_left.total_seconds())
            
            if total_seconds >= 60:
                minutes_left = int(total_seconds / 60)
                flash(f'IP адрес заблокирован на {minutes_left} минут из-за превышения лимита попыток входа', 'error')
            else:
                flash(f'IP адрес заблокирован на {total_seconds} секунд из-за превышения лимита попыток входа', 'error')
            current_app.logger.warning(f"Blocked IP {client_ip} attempted login")
            return render_template('auth/login.html', form=LoginForm(), blocked=True)
    
    if current_user.is_authenticated:
        # Перенаправление в зависимости от роли для авторизованных пользователей
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'waiter':
            return redirect(url_for('waiter.dashboard'))
        else:
            return redirect(url_for('auth.profile'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        staff = Staff.query.filter_by(login=form.username.data).first()
        
        if staff and staff.check_password(form.password.data):
            if not staff.is_active:
                flash('Аккаунт деактивирован', 'error')
                return render_template('auth/login.html', form=form)
            
            # Успешный вход - очищаем попытки
            clear_login_attempts(client_ip)
            
            login_user(staff, remember=form.remember_me.data)
            flash(f'Добро пожаловать, {staff.name}!', 'success')
            
            current_app.logger.info(f"Successful login for {staff.login} from {client_ip}")
            
            # Перенаправление в зависимости от роли
            if staff.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif staff.role == 'waiter':
                return redirect(url_for('waiter.dashboard'))
            elif staff.role == 'kitchen':
                return redirect(url_for('auth.profile'))  # На профиль для кухни
            elif staff.role == 'bar':
                return redirect(url_for('auth.profile'))  # На профиль для бара
            else:
                return redirect(url_for('auth.profile'))  # На профиль для остальных
        else:
            # Неудачный вход - записываем попытку
            record_failed_login(client_ip)
            attempts_info = get_login_attempts(client_ip)
            
            max_attempts = int(SystemSetting.get_setting('max_login_attempts', '5'))
            remaining = max_attempts - attempts_info['count']
            
            if remaining > 0:
                flash(f'Неверное имя пользователя или пароль. Осталось попыток: {remaining}', 'error')
            else:
                flash('Превышен лимит попыток входа. IP адрес заблокирован.', 'error')
            
            current_app.logger.warning(f"Failed login attempt for {form.username.data} from {client_ip}. Attempts: {attempts_info['count']}")
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
@audit_action("user_logout", table_affected=False, order_affected=False)
def logout():
    """Выход из системы."""
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Профиль пользователя."""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/api/blocked-ips')
@admin_required
def get_blocked_ips():
    """API для получения списка заблокированных IP (только для админов)."""
    from flask import jsonify
    
    # Сначала очищаем истекшие блокировки
    cleanup_expired_blocks()
    
    blocked_ips = []
    current_time = datetime.now()
    
    for ip, data in login_attempts.items():
        blocked_until = data.get('blocked_until')
        if blocked_until and blocked_until > current_time:
            time_left = blocked_until - current_time
            total_seconds = int(time_left.total_seconds())
            
            blocked_ips.append({
                'ip': ip,
                'attempts': data.get('count', 0),
                'blocked_until': blocked_until.isoformat(),
                'minutes_left': int(total_seconds / 60),
                'seconds_left': total_seconds % 60,
                'total_seconds': total_seconds
            })
    
    return jsonify({
        'status': 'success',
        'data': {
            'blocked_ips': blocked_ips,
            'total_blocked': len(blocked_ips)
        }
    })

@auth_bp.route('/api/unblock-ip/<ip>', methods=['POST'])
@admin_required
def unblock_ip(ip: str):
    """API для разблокировки IP (только для админов)."""
    from flask import jsonify
    
    if ip in login_attempts:
        del login_attempts[ip]
        current_app.logger.info(f"IP {ip} manually unblocked by admin {current_user.login}")
        return jsonify({
            'status': 'success',
            'message': f'IP {ip} разблокирован'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'IP {ip} не найден в списке заблокированных'
        }), 404 