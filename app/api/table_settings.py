"""API для настроек столов и PIN-кодов."""

from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import SystemSetting, Table
from app.utils.decorators import admin_required
from app.errors import ValidationError
import re
import hashlib

table_settings_api = Blueprint('table_settings_api', __name__)


@table_settings_api.route('/pin/verify', methods=['POST'])
def verify_table_pin():
    """Проверка PIN-кода для доступа к столам."""
    try:
        data = request.get_json()
        
        if not data or 'pin' not in data:
            raise ValidationError("PIN-код не указан", field="pin")
        
        pin = data['pin'].strip()
        
        # Валидация PIN-кода (должен быть числовым)
        if not re.match(r'^\d{4,6}$', pin):
            raise ValidationError("PIN-код должен содержать 4-6 цифр", field="pin")
        
        # Получаем сохраненный PIN-код
        stored_pin_setting = SystemSetting.get_value('table_access_pin')
        
        if not stored_pin_setting:
            # Если PIN не настроен, создаем дефолтный
            default_pin = '1234'
            SystemSetting.set_value(
                'table_access_pin',
                hashlib.sha256(default_pin.encode()).hexdigest(),
                'PIN-код для доступа к выбору столов'
            )
            stored_pin_hash = hashlib.sha256(default_pin.encode()).hexdigest()
        else:
            stored_pin_hash = stored_pin_setting
        
        # Проверяем PIN-код
        provided_pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        
        if provided_pin_hash != stored_pin_hash:
            return jsonify({
                "status": "error",
                "message": "Неверный PIN-код",
                "data": {}
            }), 401
        
        return jsonify({
            "status": "success",
            "message": "PIN-код верный",
            "data": {"access_granted": True}
        })
        
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "message": e.message,
            "errors": {e.field: e.message} if e.field else None,
            "data": {}
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error verifying table PIN: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка проверки PIN-кода",
            "data": {}
        }), 500


@table_settings_api.route('/tables', methods=['GET'])
def get_tables():
    """Получение списка столов с их статусами."""
    try:
        tables = Table.query.order_by(Table.table_number).all()
        
        tables_data = []
        for table in tables:
            tables_data.append({
                'id': table.id,
                'table_number': table.table_number,
                'status': table.status,
                'is_available': table.status == 'available',
                'assigned_waiter_id': table.assigned_waiter_id,
                'assigned_waiter_name': table.assigned_waiter.name if table.assigned_waiter else None
            })
        
        return jsonify({
            "status": "success",
            "message": "Столы получены",
            "data": {"tables": tables_data}
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting tables: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка получения столов",
            "data": {}
        }), 500


@table_settings_api.route('/pin', methods=['GET'])
@admin_required
def get_table_pin():
    """Получение текущего PIN-кода (только для админов)."""
    try:
        # Возвращаем только информацию о том, что PIN установлен
        pin_setting = SystemSetting.get_value('table_access_pin')
        
        return jsonify({
            "status": "success",
            "message": "Информация о PIN-коде",
            "data": {
                "pin_configured": pin_setting is not None,
                "last_updated": SystemSetting.query.filter_by(
                    setting_key='table_access_pin'
                ).first().updated_at.isoformat() if pin_setting else None
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting table PIN info: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка получения информации о PIN-коде",
            "data": {}
        }), 500


@table_settings_api.route('/pin', methods=['POST'])
@admin_required
def set_table_pin():
    """Установка нового PIN-кода для доступа к столам."""
    try:
        data = request.get_json()
        
        if not data or 'pin' not in data:
            raise ValidationError("PIN-код не указан", field="pin")
        
        pin = data['pin'].strip()
        
        # Валидация PIN-кода
        if not re.match(r'^\d{4,6}$', pin):
            raise ValidationError("PIN-код должен содержать 4-6 цифр", field="pin")
        
        # Хешируем PIN-код
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        
        # Сохраняем в настройках
        SystemSetting.set_value(
            'table_access_pin',
            pin_hash,
            'PIN-код для доступа к выбору столов'
        )
        
        current_app.logger.info("Table access PIN updated by admin")
        
        return jsonify({
            "status": "success",
            "message": "PIN-код обновлен",
            "data": {"pin_configured": True}
        })
        
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "message": e.message,
            "errors": {e.field: e.message} if e.field else None,
            "data": {}
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error setting table PIN: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка установки PIN-кода",
            "data": {}
        }), 500


@table_settings_api.route('/settings', methods=['GET'])
@admin_required
def get_table_settings():
    """Получение всех настроек столов."""
    try:
        settings = {
            'table_access_pin_configured': SystemSetting.get_value('table_access_pin') is not None,
            'order_cancel_timeout_minutes': int(SystemSetting.get_value('order_cancel_timeout_minutes', 5)),
            'service_charge_percent': float(SystemSetting.get_value('service_charge_percent', 10)),
            'max_tables_count': int(SystemSetting.get_value('max_tables_count', 50)),
        }
        
        return jsonify({
            "status": "success",
            "message": "Настройки получены",
            "data": settings
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting table settings: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка получения настроек",
            "data": {}
        }), 500


@table_settings_api.route('/settings', methods=['POST'])
@admin_required
def update_table_settings():
    """Обновление настроек столов."""
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("Данные не указаны")
        
        updated_settings = []
        
        # Обновляем настройки
        if 'order_cancel_timeout_minutes' in data:
            timeout = int(data['order_cancel_timeout_minutes'])
            if not 1 <= timeout <= 30:
                raise ValidationError("Время отмены должно быть от 1 до 30 минут", field="order_cancel_timeout_minutes")
            
            SystemSetting.set_value(
                'order_cancel_timeout_minutes',
                str(timeout),
                'Время в минутах для отмены заказа клиентом'
            )
            updated_settings.append('order_cancel_timeout_minutes')
        
        if 'service_charge_percent' in data:
            service_charge = float(data['service_charge_percent'])
            if not 0 <= service_charge <= 25:
                raise ValidationError("Сервисный сбор должен быть от 0 до 25%", field="service_charge_percent")
            
            SystemSetting.set_value(
                'service_charge_percent',
                str(service_charge),
                'Процент сервисного сбора'
            )
            updated_settings.append('service_charge_percent')
        
        if 'max_tables_count' in data:
            max_tables = int(data['max_tables_count'])
            if not 1 <= max_tables <= 200:
                raise ValidationError("Количество столов должно быть от 1 до 200", field="max_tables_count")
            
            SystemSetting.set_value(
                'max_tables_count',
                str(max_tables),
                'Максимальное количество столов'
            )
            updated_settings.append('max_tables_count')
        
        current_app.logger.info(f"Table settings updated: {', '.join(updated_settings)}")
        
        return jsonify({
            "status": "success",
            "message": "Настройки обновлены",
            "data": {"updated_settings": updated_settings}
        })
        
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "message": e.message,
            "errors": {e.field: e.message} if e.field else None,
            "data": {}
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error updating table settings: {e}")
        return jsonify({
            "status": "error",
            "message": "Ошибка обновления настроек",
            "data": {}
        }), 500