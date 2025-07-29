"""Контроллер аутентификации для веб-интерфейса."""

from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Staff
from app.errors import AuthenticationError, AuthorizationError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа для персонала."""
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        
        if not login or not password:
            flash('Пожалуйста, заполните все поля', 'error')
            return render_template('auth/login.html')
        
        # Поиск пользователя
        user = Staff.query.filter_by(login=login, is_active=True).first()
        
        if user and user.check_password(password):
            login_user(user)
            current_app.logger.info(f"User {user.login} logged in successfully")
            
            # Перенаправление в зависимости от роли
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'waiter':
                return redirect(url_for('waiter.dashboard'))
            else:
                return redirect(url_for('auth.login'))
        else:
            flash('Неверный логин или пароль', 'error')
            current_app.logger.warning(f"Failed login attempt for user: {login}")
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Выход из системы."""
    current_app.logger.info(f"User {current_user.login} logged out")
    logout_user()
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Профиль пользователя."""
    return render_template('auth/profile.html', user=current_user)

def admin_required(f):
    """Декоратор для проверки прав администратора."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            raise AuthenticationError("Требуется авторизация")
        
        if current_user.role != 'admin':
            raise AuthorizationError("Недостаточно прав доступа")
        
        return f(*args, **kwargs)
    return decorated_function

def waiter_required(f):
    """Декоратор для проверки прав официанта."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            raise AuthenticationError("Требуется авторизация")
        
        if current_user.role not in ['waiter', 'admin']:
            raise AuthorizationError("Недостаточно прав доступа")
        
        return f(*args, **kwargs)
    return decorated_function 