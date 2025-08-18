"""WTForms для управления меню (админка)."""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, DecimalField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, URL


class BaseJsonForm(FlaskForm):
    class Meta:
        # CSRF проверяется глобальным CSRFProtect + X-CSRFToken в заголовках
        csrf = False


class MenuCategoryForm(BaseJsonForm):
    name_ru = StringField(validators=[DataRequired(), Length(min=1, max=255)])
    name_en = StringField(validators=[Optional(), Length(max=255)])
    name_tk = StringField(validators=[Optional(), Length(max=255)])
    sort_order = IntegerField(validators=[Optional(), NumberRange(min=0)])
    is_active = BooleanField(validators=[Optional()])


class MenuItemForm(BaseJsonForm):
    category_id = SelectField('Категория', coerce=int, validators=[DataRequired()], choices=[])
    name_ru = StringField(validators=[DataRequired(), Length(min=1, max=255)])
    name_en = StringField(validators=[Optional(), Length(max=255)])
    name_tk = StringField(validators=[Optional(), Length(max=255)])
    description_ru = StringField(validators=[Optional()])
    description_en = StringField(validators=[Optional()])
    description_tk = StringField(validators=[Optional()])
    price = DecimalField(places=2, rounding=None, validators=[DataRequired(), NumberRange(min=0)])
    estimated_time = IntegerField(validators=[Optional(), NumberRange(min=0, max=24*60)])
    image_url = StringField(validators=[Optional(), URL(require_tld=False, message='Неверный URL')])
    preparation_type = SelectField(choices=[('kitchen', 'Кухня'), ('bar', 'Бар')], validators=[Optional()])
    has_size_options = BooleanField(validators=[Optional()])
    can_modify_ingredients = BooleanField(validators=[Optional()])
    is_active = BooleanField(validators=[Optional()])
    sort_order = IntegerField(validators=[Optional(), NumberRange(min=0)])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Choices для category_id будут заполнены в контроллере
        # Здесь мы не заполняем choices, так как это делается в контроллере


