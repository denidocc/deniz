"""WTForms для управления персоналом (админка)."""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Length, Optional, EqualTo


class BaseJsonForm(FlaskForm):
    class Meta:
        csrf = False


class StaffCreateForm(BaseJsonForm):
    """Форма создания сотрудника."""
    name = StringField(validators=[DataRequired(), Length(min=1, max=100)])
    role = SelectField(
        choices=[
            ('admin', 'Администратор'), 
            ('waiter', 'Официант'), 
            ('kitchen', 'Кухня'), 
            ('bar', 'Бар')
        ],
        validators=[DataRequired()]
    )
    login = StringField(validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField(validators=[DataRequired(), Length(min=6)])
    password_confirm = PasswordField(
        validators=[DataRequired(), EqualTo('password', message='Пароли должны совпадать')]
    )
    is_active = BooleanField(default=True, validators=[Optional()], false_values=())


class StaffUpdateForm(BaseJsonForm):
    """Форма обновления сотрудника."""
    name = StringField(validators=[Optional(), Length(min=1, max=100)])
    role = SelectField(
        choices=[
            ('admin', 'Администратор'), 
            ('waiter', 'Официант'), 
            ('kitchen', 'Кухня'), 
            ('bar', 'Бар')
        ],
        validators=[Optional()]
    )
    login = StringField(validators=[Optional(), Length(min=3, max=50)])
    password = PasswordField(validators=[Optional(), Length(min=6)])
    is_active = BooleanField(default=True, validators=[Optional()], false_values=())
