"""Модель аудита действий."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional, TYPE_CHECKING, Dict, Any
from datetime import datetime
import json
from .base import BaseModel
from app import db

if TYPE_CHECKING:
    from .staff import Staff

class AuditLog(BaseModel):
    """Модель аудита действий."""
    
    __tablename__ = 'audit_log'
    
    # Основные поля
    staff_id: so.Mapped[Optional[int]] = so.mapped_column(
        sa.Integer, sa.ForeignKey('staff.id'), nullable=True, index=True
    )
    action: so.Mapped[str] = so.mapped_column(
        sa.String(100), nullable=False, index=True
    )
    table_affected: so.Mapped[Optional[int]] = so.mapped_column(
        sa.Integer, nullable=True, index=True
    )
    order_affected: so.Mapped[Optional[int]] = so.mapped_column(
        sa.Integer, nullable=True, index=True
    )
    details: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )  # JSON данные
    ip_address: so.Mapped[Optional[str]] = so.mapped_column(
        sa.String(45), nullable=True
    )  # IPv6 может быть до 45 символов
    
    # Отношения
    staff: so.Mapped[Optional["Staff"]] = so.relationship(
        lazy='selectin'
    )
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return f'<AuditLog {self.action} by {self.staff.name if self.staff else "System"}>'
    
    def get_details(self) -> Dict[str, Any]:
        """Получение деталей из JSON."""
        if self.details:
            try:
                return json.loads(self.details)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def set_details(self, data: Dict[str, Any]) -> None:
        """Установка деталей в JSON."""
        self.details = json.dumps(data, ensure_ascii=False, default=str)
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'staff': {
                'id': self.staff.id,
                'name': self.staff.name,
                'login': self.staff.login,
            } if self.staff else None,
            'action': self.action,
            'table_affected': self.table_affected,
            'order_affected': self.order_affected,
            'details': self.get_details(),
            'ip_address': self.ip_address,
        })
        return data
    
    @classmethod
    def log_action(cls, action: str, staff_id: Optional[int] = None, 
                   table_affected: Optional[int] = None, order_affected: Optional[int] = None,
                   details: Dict[str, Any] = None, ip_address: Optional[str] = None) -> 'AuditLog':
        """Логирование действия."""
        log_entry = cls(
            staff_id=staff_id,
            action=action,
            table_affected=table_affected,
            order_affected=order_affected,
            ip_address=ip_address
        )
        
        if details:
            log_entry.set_details(details)
        
        try:
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Логируем в обычный лог если не можем записать в аудит
            from flask import current_app
            current_app.logger.error(f"Failed to log audit action '{action}': {e}")
            raise
        
        return log_entry
    
    @classmethod
    def get_by_staff(cls, staff_id: int, limit: int = 100) -> list['AuditLog']:
        """Получение логов по сотруднику."""
        return cls.query.filter_by(staff_id=staff_id).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_by_action(cls, action: str, limit: int = 100) -> list['AuditLog']:
        """Получение логов по действию."""
        return cls.query.filter_by(action=action).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_recent_logs(cls, hours: int = 24, limit: int = 500) -> list['AuditLog']:
        """Получение последних логов за указанное время."""
        from datetime import datetime, timedelta
        since = datetime.utcnow() - timedelta(hours=hours)
        return cls.query.filter(cls.created_at >= since).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_logs_by_ip(cls, ip_address: str, limit: int = 100) -> list['AuditLog']:
        """Получение логов по IP адресу."""
        return cls.query.filter_by(ip_address=ip_address).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_error_logs(cls, limit: int = 100) -> list['AuditLog']:
        """Получение логов ошибок."""
        return cls.query.filter(cls.action.like('%_error')).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_by_table(cls, table_id: int, limit: int = 100) -> list['AuditLog']:
        """Получение логов по столу."""
        return cls.query.filter_by(table_affected=table_id).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_by_order(cls, order_id: int, limit: int = 100) -> list['AuditLog']:
        """Получение логов по заказу."""
        return cls.query.filter_by(order_affected=order_id).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_recent_logs_simple(cls, limit: int = 100) -> list['AuditLog']:
        """Получение последних логов."""
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_logs_by_date_range(cls, start_date: datetime, end_date: datetime) -> list['AuditLog']:
        """Получение логов за период."""
        return cls.query.filter(
            cls.created_at >= start_date,
            cls.created_at <= end_date
        ).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_statistics(cls, days: int = 7) -> Dict[str, Any]:
        """Получение статистики по аудиту за указанное количество дней."""
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        since = datetime.utcnow() - timedelta(days=days)
        
        # Общее количество действий
        total_actions = cls.query.filter(cls.created_at >= since).count()
        
        # Топ действий
        top_actions = db.session.query(
            cls.action, 
            func.count(cls.id).label('count')
        ).filter(
            cls.created_at >= since
        ).group_by(cls.action).order_by(func.count(cls.id).desc()).limit(10).all()
        
        # Топ пользователей
        top_users = db.session.query(
            cls.staff_id,
            func.count(cls.id).label('count')
        ).filter(
            cls.created_at >= since,
            cls.staff_id.isnot(None)
        ).group_by(cls.staff_id).order_by(func.count(cls.id).desc()).limit(10).all()
        
        # Количество ошибок
        error_count = cls.query.filter(
            cls.created_at >= since,
            cls.action.like('%_error')
        ).count()
        
        return {
            'period_days': days,
            'total_actions': total_actions,
            'error_count': error_count,
            'error_percentage': round((error_count / total_actions * 100) if total_actions > 0 else 0, 2),
            'top_actions': [{'action': action, 'count': count} for action, count in top_actions],
            'top_users': [{'staff_id': staff_id, 'count': count} for staff_id, count in top_users]
        } 