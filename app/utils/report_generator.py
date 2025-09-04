"""Генератор отчетов в различных форматах."""

import os
from datetime import datetime
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io


def generate_z_report_pdf(report) -> bytes:
    """
    Генерация Z-отчета в формате PDF с поддержкой кириллицы.
    
    Args:
        report: Объект DailyReport
        
    Returns:
        bytes: Содержимое PDF файла
    """
    try:
        
        # Создаем буфер для PDF
        buffer = io.BytesIO()
        
        # Создаем PDF документ
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Регистрируем шрифт с поддержкой кириллицы
        font_name = 'Helvetica'  # По умолчанию используем Helvetica
        
        try:
            # Пытаемся найти и зарегистрировать шрифт с поддержкой кириллицы
            possible_fonts = [
                # macOS
                '/System/Library/Fonts/Arial.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
                '/Library/Fonts/Arial.ttf',
                # Linux
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                # Windows
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/calibri.ttf'
            ]
            
            for font_path in possible_fonts:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('CustomFont', font_path))
                        font_name = 'CustomFont'
                        break
                    except:
                        continue
                        
        except Exception as e:
            # Если не удалось зарегистрировать шрифт, используем встроенный
            font_name = 'Helvetica'
        
        # Стили для текста
        styles = getSampleStyleSheet()
        
        # Создаем стили с правильным шрифтом
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName=font_name,
            encoding='utf-8'  # Явно указываем кодировку
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue,
            fontName=font_name,
            encoding='utf-8'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            encoding='utf-8'
        )
        
        # Содержимое PDF
        story = []
        
        # Заголовок - используем простой текст без кириллицы для заголовка
        story.append(Paragraph("DENIZ RESTAURANT - Z-OTCHET", title_style))
        story.append(Spacer(1, 20))
        
        # Основная информация - используем транслитерацию для важных полей
        story.append(Paragraph(f"Data: {report.report_date.strftime('%d.%m.%Y')}", heading_style))
        
        # ✅ ДОБАВЛЯЕМ НОВЫЕ ПОЛЯ
        # Получаем количество завершенных заказов из report_data
        report_data = report.get_report_data()
        completed_orders_count = report_data.get('completed_orders_count', 0)
        story.append(Spacer(1, 12))
        
        # Детализация
        story.append(Paragraph("Detalizatsiya:", heading_style))
        
        # Таблица с данными - используем транслитерацию
        data = [
            ['Pokazatel', 'Znachenie'],
            ['Vsego zakazov sozdano', str(report.total_orders)],
            ['Zavershennyh zakazov', str(completed_orders_count)],
            ['Otmenennyh zakazov', str(report.cancelled_orders)],
            ['Obshchee kolichestvo gostey', str(report.total_guests or 0)],
            ['Vyruchka', f"{report.total_revenue:.2f} TMT"],
            ['Servisny sbor', f"{report.total_service_charge:.2f} TMT"]
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Подпись - используем транслитерацию
        story.append(Paragraph(f"Otchet sozdan: {report.created_at.strftime('%d.%m.%Y %H:%M:%S')}", normal_style))
        story.append(Spacer(1, 30))
        story.append(Paragraph("Podpis: _________________", normal_style))
        
        # Строим PDF
        doc.build(story)
        
        # Получаем содержимое
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except Exception as e:
        # В случае ошибки возвращаем простой PDF с сообщением об ошибке
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = [
            Paragraph("Error generating report", styles['Heading1']),
            Spacer(1, 20),
            Paragraph(f"Failed to generate report: {str(e)}", styles['Normal'])
        ]
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()
        return pdf_content


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
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .report-container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                border-bottom: 2px solid #007bff;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                color: #007bff;
                margin: 0;
                font-size: 28px;
            }}
            .info-section {{
                margin-bottom: 25px;
            }}
            .info-section h3 {{
                color: #333;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5px;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }}
            .info-item {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }}
            .info-item strong {{
                color: #007bff;
            }}
            .summary-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            .summary-table th,
            .summary-table td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            .summary-table th {{
                background-color: #007bff;
                color: white;
                font-weight: bold;
            }}
            .summary-table tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                text-align: center;
                color: #666;
            }}
            .signature {{
                margin-top: 30px;
                text-align: right;
            }}
            .signature-line {{
                border-top: 1px solid #333;
                width: 200px;
                display: inline-block;
                margin-left: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="report-container">
            <div class="header">
                <h1>DENIZ RESTAURANT</h1>
                <h2>Z-ОТЧЕТ № {report.id}</h2>
            </div>
            
            <div class="info-section">
                <h3>Основная информация</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <strong>Дата отчета:</strong><br>
                        {report.report_date.strftime('%d.%m.%Y')}
                    </div>
                    <div class="info-item">
                        <strong>Номер отчета:</strong><br>
                        {report.id}
                    </div>
                    <div class="info-item">
                        <strong>Всего заказов:</strong><br>
                        {report.total_orders}
                    </div>
                    <div class="info-item">
                        <strong>Выручка:</strong><br>
                        {report.total_revenue:.2f} TMT
                    </div>
                </div>
            </div>
            
            <div class="info-section">
                <h3>Детализация</h3>
                <table class="summary-table">
                    <thead>
                        <tr>
                            <th>Показатель</th>
                            <th>Значение</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Всего заказов</td>
                            <td>{report.total_orders}</td>
                        </tr>
                        <tr>
                            <td>Выручка</td>
                            <td>{report.total_revenue:.2f} TMT</td>
                        </tr>
                        <tr>
                            <td>Отмененные заказы</td>
                            <td>{report.cancelled_orders}</td>
                        </tr>
                        <tr>
                            <td>Сервисный сбор</td>
                            <td>{report.total_service_charge or 0:.2f} TMT</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                <p>Z-отчет создан: {report.created_at.strftime('%d.%m.%Y %H:%M:%S')}</p>
                
                <div class="signature">
                    Подпись: <span class="signature-line"></span>
                </div>
            </div>
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
        # current_app.logger.error(f"Excel generation failed: {e}") # This line was removed as per the new_code
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
        # current_app.logger.error(f"CSV generation failed: {e}") # This line was removed as per the new_code
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