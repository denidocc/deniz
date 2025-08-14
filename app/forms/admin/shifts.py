"""WTForms для управления сменами (админка)."""

from flask_wtf import FlaskForm
from wtforms import IntegerField, BooleanField, StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, NumberRange, Optional, Length


class BaseJsonForm(FlaskForm):
    class Meta:
        csrf = False


class StartShiftForm(BaseJsonForm):
    """Форма начала смены."""
    staff_id = SelectField('Сотрудник', coerce=int, validators=[DataRequired()], choices=[])
    # table_ids будем валидировать вручную из JSON (список int)
    auto_assign = BooleanField('Автоназначение столов', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Динамически заполняем choices для staff_id
        from app.models import Staff
        active_waiters = Staff.query.filter_by(role='waiter', is_active=True).all()
        self.staff_id.choices = [(waiter.id, waiter.name) for waiter in active_waiters]


class EndShiftForm(BaseJsonForm):
    """Форма завершения смены."""
    notes = TextAreaField(validators=[Optional(), Length(max=500)])


