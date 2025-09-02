"""WTForms для настроек системы (админка)."""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, BooleanField, SelectField, FieldList, FormField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class BaseJsonForm(FlaskForm):
    class Meta:
        csrf = False


class SystemSettingForm(BaseJsonForm):
    """Форма для обновления системной настройки."""
    setting_key = StringField(validators=[DataRequired(), Length(min=1, max=100)])
    setting_value = StringField(validators=[DataRequired()])
    description = StringField(validators=[Optional(), Length(max=500)])


class ServiceChargeForm(BaseJsonForm):
    """Форма для настройки сервисного сбора."""
    percentage = DecimalField(places=2, validators=[DataRequired(), NumberRange(min=0, max=50)])


class ClientPinForm(BaseJsonForm):
    """Форма для настройки PIN-кода клиентов."""
    pin = StringField(validators=[DataRequired(), Length(min=4, max=8)])


class PrinterSettingsForm(BaseJsonForm):
    """Форма для настроек принтеров."""
    kitchen_printer_ip = StringField(validators=[Optional(), Length(max=50)])
    bar_printer_ip = StringField(validators=[Optional(), Length(max=50)])
    receipt_printer_ip = StringField(validators=[Optional(), Length(max=50)])
    enable_printing = BooleanField(validators=[Optional()])


class TableSettingsForm(BaseJsonForm):
    """Форма для настройки столов."""
    table_number = IntegerField(validators=[DataRequired(), NumberRange(min=1, max=100)])
    capacity = IntegerField(validators=[DataRequired(), NumberRange(min=1, max=20)])
    is_active = BooleanField(validators=[Optional()], default=True)


class LanguageSettingsForm(BaseJsonForm):
    """Форма для настройки языков."""
    primary_language = SelectField(
        'Основной язык',
        choices=[
            ('ru', 'Русский'),
            ('en', 'English'),
            ('tk', 'Türkmençe')
        ],
        validators=[DataRequired()]
    )
    
    secondary_languages = SelectField(
        'Дополнительные языки',
        choices=[
            ('ru', 'Русский'),
            ('en', 'English'),
            ('tk', 'Türkmençe')
        ],
        validators=[Optional()],
        multiple=True
    )
