"""WTForms для отчетов (админка)."""

from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, IntegerField
from wtforms.validators import DataRequired, Optional, NumberRange
from datetime import date


class BaseJsonForm(FlaskForm):
    class Meta:
        csrf = False


class ReportFilterForm(BaseJsonForm):
    """Форма для фильтрации отчетов."""
    date_from = DateField(validators=[Optional()])
    date_to = DateField(validators=[Optional()])
    report_type = SelectField(
        choices=[('daily', 'daily'), ('weekly', 'weekly'), ('monthly', 'monthly')],
        validators=[Optional()]
    )


class ZReportForm(BaseJsonForm):
    """Форма для генерации Z-отчета."""
    report_date = DateField(validators=[DataRequired()], default=date.today)


class AuditFilterForm(BaseJsonForm):
    """Форма для фильтрации логов аудита."""
    staff_id = IntegerField(validators=[Optional(), NumberRange(min=1)])
    date_from = DateField(validators=[Optional()])
    date_to = DateField(validators=[Optional()])
    action_type = SelectField(
        choices=[('', 'Все действия'), ('login', 'Вход в систему'), ('create_order', 'Создание заказа'), 
                ('confirm_order', 'Подтверждение заказа')],
        validators=[Optional()]
    )
