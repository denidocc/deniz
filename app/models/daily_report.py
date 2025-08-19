"""Модель дневных отчетов."""

import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import TYPE_CHECKING, Dict, Any, Optional
from datetime import date
from decimal import Decimal
import json
from .base import BaseModel

if TYPE_CHECKING:
    pass

class DailyReport(BaseModel):
    """Модель дневных отчетов."""
    
    __tablename__ = 'daily_reports'
    
    # Основные поля
    report_date: so.Mapped[date] = so.mapped_column(
        sa.Date, nullable=False, index=True
    )
    total_orders: so.Mapped[int] = so.mapped_column(
        sa.Integer, default=0, nullable=False
    )
    total_revenue: so.Mapped[Decimal] = so.mapped_column(
        sa.Numeric(12, 2), default=0.00, nullable=False
    )
    total_service_charge: so.Mapped[Decimal] = so.mapped_column(
        sa.Numeric(12, 2), default=0.00, nullable=False
    )
    cancelled_orders: so.Mapped[int] = so.mapped_column(
        sa.Integer, default=0, nullable=False
    )
    average_order_value: so.Mapped[Decimal] = so.mapped_column(
        sa.Numeric(10, 2), default=0.00, nullable=False
    )
    peak_hour: so.Mapped[Optional[str]] = so.mapped_column(
        sa.String(5), nullable=True
    )  # HH:MM формат
    report_data: so.Mapped[Optional[str]] = so.mapped_column(
        sa.Text, nullable=True
    )  # JSON данные
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return f'<DailyReport {self.report_date} ({self.total_orders} orders)>'
    
    def get_report_data(self) -> Dict[str, Any]:
        """Получение данных отчета из JSON."""
        if self.report_data:
            return json.loads(self.report_data)
        return {}
    
    def set_report_data(self, data: Dict[str, Any]) -> None:
        """Установка данных отчета в JSON."""
        self.report_data = json.dumps(data, ensure_ascii=False)
    
    def calculate_average_order(self) -> None:
        """Расчет среднего чека."""
        if self.total_orders > 0:
            self.average_order_value = self.total_revenue / self.total_orders
        else:
            self.average_order_value = Decimal('0.00')
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        data = super().to_dict()
        data.update({
            'report_date': self.report_date.isoformat(),
            'total_orders': self.total_orders,
            'total_revenue': float(self.total_revenue),
            'total_service_charge': float(self.total_service_charge),
            'cancelled_orders': self.cancelled_orders,
            'average_order_value': float(self.average_order_value),
            'peak_hour': self.peak_hour,
            'report_data': self.get_report_data(),
        })
        return data
    
    @classmethod
    def get_by_date(cls, report_date: date) -> Optional['DailyReport']:
        """Получение отчета по дате."""
        return cls.query.filter_by(report_date=report_date).first()
    
    @classmethod
    def get_recent_reports(cls, days: int = 30) -> list['DailyReport']:
        """Получение отчетов за последние дни."""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        return cls.query.filter(
            cls.report_date >= start_date
        ).order_by(cls.report_date.desc()).all()
    
    @classmethod
    def generate_daily_report(cls, report_date: date) -> 'DailyReport':
        """Генерация дневного отчета."""
        from .order import Order
        
        # Получаем все заказы за день
        orders = Order.query.filter(
            sa.func.date(Order.created_at) == report_date
        ).all()
        
        # Подсчитываем статистику
        total_orders = len(orders)
        total_revenue = sum(order.total_amount for order in orders)
        total_service_charge = sum(order.service_charge for order in orders)
        cancelled_orders = len([o for o in orders if o.status == 'cancelled'])
        
        # Расчет среднего чека
        completed_orders = [o for o in orders if o.status == 'completed']
        average_order_value = (
            sum(o.total_amount for o in completed_orders) / len(completed_orders)
            if completed_orders else Decimal('0.00')
        )
        
        # Определение пикового часа
        hour_counts = {}
        for order in orders:
            hour = order.created_at.strftime('%H')
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        peak_hour = None
        if hour_counts:
            peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0] + ':00'
        
        # Детальные данные отчета
        report_data = {
            'orders_by_hour': hour_counts,
            'orders_by_status': {
                'pending': len([o for o in orders if o.status == 'pending']),
                'confirmed': len([o for o in orders if o.status == 'confirmed']),
                'completed': len([o for o in orders if o.status == 'completed']),
                'cancelled': cancelled_orders,
            },
            'top_menu_items': cls._get_top_menu_items(orders),
            'staff_performance': cls._get_staff_performance(report_date),
        }
        
        # Создаем или обновляем отчет
        report = cls.get_by_date(report_date)
        if not report:
            report = cls(report_date=report_date)
        
        report.total_orders = total_orders
        report.total_revenue = total_revenue
        report.total_service_charge = total_service_charge
        report.cancelled_orders = cancelled_orders
        report.average_order_value = average_order_value
        report.peak_hour = peak_hour
        report.set_report_data(report_data)
        
        db.session.add(report)
        db.session.commit()
        
        return report
    
    @classmethod
    def _get_top_menu_items(cls, orders: list) -> list:
        """Получение топ блюд."""
        from .order_item import OrderItem
        
        item_counts = {}
        for order in orders:
            for item in order.items:
                item_name = item.menu_item.name_ru
                item_counts[item_name] = item_counts.get(item_name, 0) + item.quantity
        
        # Сортируем по количеству
        sorted_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)
        return [{'name': name, 'count': count} for name, count in sorted_items[:10]]
    
    @classmethod
    def _get_staff_performance(cls, report_date: date) -> list:
        """Получение производительности персонала."""

        return [] 