"""Формы аутентификации."""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    """Форма входа в систему."""
    
    username = StringField(
        'Логин',
        validators=[
            DataRequired(message='Введите логин'),
            Length(min=3, max=50, message='Логин должен быть от 3 до 50 символов')
        ],
        render_kw={'placeholder': 'Введите логин', 'class': 'form-control'}
    )
    
    password = PasswordField(
        'Пароль',
        validators=[
            DataRequired(message='Введите пароль'),
            Length(min=3, message='Пароль должен содержать минимум 3 символа')
        ],
        render_kw={'placeholder': 'Введите пароль', 'class': 'form-control'}
    )
    
    remember_me = BooleanField(
        'Запомнить меня',
        render_kw={'class': 'form-check-input'}
    )
    
    submit = SubmitField(
        'Войти',
        render_kw={'class': 'btn btn-primary btn-lg w-100'}
    )