"""Контроллер аутентификации."""

from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import LoginForm
from app.models import Staff
from app.errors import ValidationError, AuthenticationError, AuthorizationError
from app.utils.decorators import audit_action, admin_required
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@audit_action("user_login_attempt", table_affected=False, order_affected=False)
def login():
    """Вход в систему."""
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
            
            login_user(staff, remember=form.remember_me.data)
            flash(f'Добро пожаловать, {staff.name}!', 'success')
            
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
            flash('Неверное имя пользователя или пароль', 'error')
    
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