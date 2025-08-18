"""Генератор отчетов в различных форматах."""

from datetime import datetime
from typing import Dict, Any, Optional
from flask import current_app
import json


def generate_z_report_pdf(report) -> bytes:
    """
    Генерация Z-отчета в формате PDF.
    
    Args:
        report: Объект DailyReport
        
    Returns:
        bytes: Содержимое PDF файла
    """
    try:
        # Для демонстрации создаем простой HTML-to-PDF
        # В реальном проекте лучше использовать ReportLab или WeasyPrint
        
        html_content = generate_z_report_html(report)
        
        # Простая заглушка для PDF - в реальности здесь должен быть
        # полноценный генератор PDF (например, WeasyPrint)
        pdf_content = f"""
%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
50 750 Td
(DENIZ RESTAURANT - Z-ОТЧЕТ #{report.id}) Tj
0 -30 Td
(Дата: {report.report_date.strftime('%d.%m.%Y')}) Tj
0 -30 Td
(Заказов: {report.total_orders}) Tj
0 -30 Td
(Выручка: {report.total_revenue:.2f} руб.) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000275 00000 n 
0000000525 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
608
%%EOF
        """.encode('utf-8')
        
        return pdf_content
        
    except Exception as e:
        current_app.logger.error(f"PDF generation failed: {e}")
        raise Exception(f"Ошибка генерации PDF: {str(e)}")


def generate_z_report_html(report) -> str:
    """
    Генерация Z-отчета в формате HTML.
    
    Args:
        report: Объект DailyReport
        
    Returns:
        str: HTML содержимое отчета
    """
    # Налоги не применяются (НДС отсутствует)
    total_with_vat = report.total_revenue
    total_without_vat = report.total_revenue
    vat_amount = 0
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Z-отчет № {report.id}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .company-name {{ font-size: 20px; font-weight: bold; }}
            .report-title {{ font-size: 18px; margin: 10px 0; }}
            .report-date {{ font-size: 14px; color: #666; }}
            
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f5f5f5; font-weight: bold; }}
            .amount {{ text-align: right; }}
            .total-row {{ font-weight: bold; background-color: #f0f8ff; }}
            
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            .signature {{ margin-top: 40px; }}
            .signature-line {{ border-bottom: 1px solid #000; width: 200px; display: inline-block; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="company-name">DENIZ RESTAURANT</div>
            <div class="report-title">Z-ОТЧЕТ № {report.id}</div>
            <div class="report-date">за {report.report_date.strftime('%d.%m.%Y')}</div>
        </div>
        
        <table>
            <tr>
                <th>Показатель</th>
                <th class="amount">Значение</th>
            </tr>
            <tr>
                <td>Количество заказов</td>
                <td class="amount">{report.total_orders}</td>
            </tr>
            <!-- Налоговые строки скрыты по требованиям -->
            <!--
            <tr>
                <td>Сумма без НДС</td>
                <td class="amount">{total_without_vat:.2f} TMT</td>
            </tr>
            <tr>
                <td>НДС (20%)</td>
                <td class="amount">{vat_amount:.2f} TMT</td>
            </tr>
            <tr class="total-row">
                <td>ИТОГО с НДС</td>
                <td class="amount">{total_with_vat:.2f} TMT</td>
            </tr>
            -->
        </table>
        
        <div class="footer">
            <p>Отчет создан: {report.created_at.strftime('%d.%m.%Y %H:%M:%S')}</p>
            <p>Создал: {report.generated_by.name} ({report.generated_by.role})</p>
            
            <div class="signature">
                <p>Подпись ответственного лица: <span class="signature-line"></span></p>
            </div>
            
            <p style="text-align: center; margin-top: 30px;">
                <small>
                    Данный отчет является официальным документом<br>
                    и содержит полную информацию о продажах за указанный период
                </small>
            </p>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_sales_report_excel(data: Dict[str, Any]) -> bytes:
    """
    Генерация отчета по продажам в формате Excel.
    
    Args:
        data: Данные для отчета
        
    Returns:
        bytes: Содержимое Excel файла
    """
    try:
        # Заглушка для Excel генерации
        # В реальном проекте использовать openpyxl или xlsxwriter
        
        csv_content = "Дата,Заказов,Выручка,Средний чек\n"
        
        for stat in data.get('daily_stats', []):
            avg_order = stat['revenue'] / stat['orders'] if stat['orders'] > 0 else 0
            csv_content += f"{stat['date']},{stat['orders']},{stat['revenue']:.2f},{avg_order:.2f}\n"
        
        return csv_content.encode('utf-8')
        
    except Exception as e:
        current_app.logger.error(f"Excel generation failed: {e}")
        raise Exception(f"Ошибка генерации Excel: {str(e)}")


def generate_audit_logs_csv(logs: list) -> bytes:
    """
    Экспорт логов аудита в формат CSV.
    
    Args:
        logs: Список логов аудита
        
    Returns:
        bytes: Содержимое CSV файла
    """
    try:
        csv_content = "Timestamp,Action,Staff,IP Address,Table,Order,Status\n"
        
        for log in logs:
            staff_name = log.staff.name if log.staff else "System"
            status = log.details.get('result_status', 'unknown') if log.details else 'unknown'
            
            csv_content += f'"{log.timestamp.isoformat()}","{log.action}","{staff_name}","{log.ip_address or ""}","{log.table_affected or ""}","{log.order_affected or ""}","{status}"\n'
        
        return csv_content.encode('utf-8')
        
    except Exception as e:
        current_app.logger.error(f"CSV generation failed: {e}")
        raise Exception(f"Ошибка генерации CSV: {str(e)}")


def generate_staff_performance_report(staff_data: Dict[str, Any]) -> str:
    """
    Генерация отчета по производительности персонала.
    
    Args:
        staff_data: Данные о персонале
        
    Returns:
        str: HTML отчет
    """
    html = """
    <div class="staff-performance-report">
        <h3>Отчет по производительности персонала</h3>
        <table class="table">
            <thead>
                <tr>
                    <th>Сотрудник</th>
                    <th>Роль</th>
                    <th>Часов работы</th>
                    <th>Заказов обслужено</th>
                    <th>Средний чек</th>
                    <th>Оценка</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for staff in staff_data.get('staff_list', []):
        rating = calculate_staff_rating(staff)
        html += f"""
                <tr>
                    <td>{staff.get('name', 'N/A')}</td>
                    <td>{staff.get('role', 'N/A')}</td>
                    <td>{staff.get('hours_worked', 0)}</td>
                    <td>{staff.get('orders_served', 0)}</td>
                    <td>{staff.get('avg_check', 0):.2f} TMT</td>
                    <td>{rating}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
    </div>
    """
    
    return html


def calculate_staff_rating(staff_data: Dict[str, Any]) -> str:
    """
    Расчет рейтинга сотрудника.
    
    Args:
        staff_data: Данные сотрудника
        
    Returns:
        str: Рейтинг сотрудника
    """
    hours = staff_data.get('hours_worked', 0)
    orders = staff_data.get('orders_served', 0)
    avg_check = staff_data.get('avg_check', 0)
    
    if hours == 0:
        return "Нет данных"
    
    orders_per_hour = orders / hours
    
    if orders_per_hour >= 3 and avg_check >= 1500:
        return "Отлично"
    elif orders_per_hour >= 2 and avg_check >= 1000:
        return "Хорошо"
    elif orders_per_hour >= 1:
        return "Удовлетворительно"
    else:
        return "Требует внимания"


def generate_menu_popularity_report(menu_data: Dict[str, Any]) -> str:
    """
    Генерация отчета по популярности блюд.
    
    Args:
        menu_data: Данные о продажах блюд
        
    Returns:
        str: HTML отчет
    """
    html = """
    <div class="menu-popularity-report">
        <h3>Отчет по популярности блюд</h3>
        <table class="table">
            <thead>
                <tr>
                    <th>Блюдо</th>
                    <th>Категория</th>
                    <th>Продано</th>
                    <th>Выручка</th>
                    <th>% от общих продаж</th>
                </tr>
            </thead>
            <tbody>
    """
    
    total_revenue = sum(item.get('revenue', 0) for item in menu_data.get('items', []))
    
    for item in menu_data.get('items', []):
        percentage = (item.get('revenue', 0) / total_revenue * 100) if total_revenue > 0 else 0
        html += f"""
                <tr>
                    <td>{item.get('name', 'N/A')}</td>
                    <td>{item.get('category', 'N/A')}</td>
                    <td>{item.get('quantity_sold', 0)}</td>
                    <td>{item.get('revenue', 0):.2f} TMT</td>
                    <td>{percentage:.1f}%</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
    </div>
    """
    
    return html