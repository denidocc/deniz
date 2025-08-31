# Техническая спецификация для программиста - Система печати DENIZ

## Архитектура системы

```
                    ┌─────────────────┐
                    │   Интернет      │
                    │   провайдер     │
                    └─────────┬───────┘
                              │
                    ┌─────────▼───────┐
                    │  WiFi Роутер    │
                    │  192.168.1.1    │
                    └─────────┬───────┘
                              │
                    ┌─────────▼───────┐ Ethernet
                    │ Кухонный принтер│◄──────────────────┐
                    │ XV-URAT 80US    │                   │
                    │ 192.168.1.101   │                   │
                    └─────────────────┘                   │
                              │                           │
                              │ WiFi                      │
                    ┌─────────▼───────┐                   │
                    │ Сервер-ноутбук  │ ◄─────────────────┘
                    │ Flask App       │
                    │ 192.168.1.10    │
                    └─────┬─────┬─────┘
                          │     │
                     USB  │     │ USB
                          │     │
               ┌──────────▼─┐ ┌─▼──────────┐
               │  Барный    │ │  Чековый   │
               │ принтер    │ │ принтер    │
               │ ZyWell     │ │ ZyWell     │
               │ 5890K      │ │ 5890K      │
               │ (58mm)     │ │ (58mm)     │
               └────────────┘ └────────────┘
                              
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │   Планшет       │ │   Планшет       │ │   Планшет       │
    │   Стол #1       │ │   Стол #2       │ │   Стол #N       │
    │ (WiFi клиент)   │ │ (WiFi клиент)   │ │ (WiFi клиент)   │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Логика работы программы

### 1. Обработка заказа
```python
def process_order(order_data):
    """
    order_data = {
        'table_id': 5,
        'waiter_id': 2,  
        'items': [
            {'name': 'Борщ классический', 'quantity': 2, 'type': 'kitchen', 'comments': 'Без сметаны'},
            {'name': 'Кола 0.5л', 'quantity': 1, 'type': 'bar', 'comments': ''}
        ]
    }
    """
    
    # Разделить заказ на кухню и бар
    kitchen_items = filter_items_by_type(order_data['items'], 'kitchen')
    bar_items = filter_items_by_type(order_data['items'], 'bar')
    
    # Печать на кухню (если есть позиции кухни)
    if kitchen_items:
        print_kitchen_receipt(order_data, kitchen_items)
    
    # Печать в бар (если есть позиции бара)  
    if bar_items:
        print_bar_receipt(order_data, bar_items)
```

### 2. Печать кухонного чека (Ethernet)
```python
from escpos.printer import Network

def print_kitchen_receipt(order_data, kitchen_items):
    try:
        # Подключение к сетевому принтеру
        printer = Network("192.168.1.101", port=9100, timeout=5)
        
        # Заголовок (80mm = 48 символов)
        printer.set(align='center', text_type='B', height=2, width=2)
        printer.text("КУХНЯ - DENIZ\n")
        printer.text("=" * 48 + "\n")
        
        # Информация о заказе
        printer.set(align='left', text_type='normal', height=1, width=1)
        printer.text(f"Стол: {order_data['table_id']}                   #{order_data['order_number']}\n")
        printer.text(f"Официант: {order_data['waiter_name']}\n\n")
        
        # Позиции кухни (БЕЗ ЦЕН!)
        for item in kitchen_items:
            printer.text(f"{item['quantity']}x {item['name']}\n")
            if item['comments']:
                printer.text(f"   - {item['comments']}\n")
        
        printer.text(f"\nЗаказан: {order_data['time']}\n")
        printer.text("=" * 48 + "\n")
        
        # Обрезка
        printer.cut()
        printer.close()
        
    except Exception as e:
        log_error(f"Kitchen printer error: {e}")
        # Сохранить в очередь для повтора
        add_to_retry_queue('kitchen', order_data, kitchen_items)
```

### 3. Печать барного чека (USB)
```python
from escpos.printer import Usb

def print_bar_receipt(order_data, bar_items):
    try:
        # USB подключение (Vendor ID и Product ID для ZyWell 5890K)
        printer = Usb(0x1CB0, 0x0007)  # Нужно определить для ZyWell
        
        # Заголовок (58mm = 32 символа)
        printer.set(align='center', text_type='B', height=2, width=1)
        printer.text("БАР - DENIZ\n")
        printer.text("=" * 32 + "\n")
        
        # Информация о заказе  
        printer.set(align='left', text_type='normal', height=1, width=1)
        printer.text(f"Стол: {order_data['table_id']}            #{order_data['order_number']}\n")
        printer.text(f"Официант: {order_data['waiter_name']}\n\n")
        
        # Позиции бара (БЕЗ ЦЕН!)
        for item in bar_items:
            printer.text(f"{item['quantity']}x {item['name']}\n")
            if item['comments']:
                printer.text(f"   - {item['comments']}\n")
        
        printer.text(f"\nЗаказан: {order_data['time']}\n")
        printer.text("=" * 32 + "\n")
        
        printer.cut()
        printer.close()
        
    except Exception as e:
        log_error(f"Bar printer error: {e}")
        add_to_retry_queue('bar', order_data, bar_items)
```

### 4. Печать финального чека (USB)
```python
def print_final_receipt(order_data):
    try:
        # Второй USB принтер (возможно другой Product ID)
        printer = Usb(0x1CB0, 0x0008)  # Или тот же принтер через USB hub
        
        # Заголовок (58mm = 32 символа)
        printer.set(align='center', text_type='B')
        printer.text("РЕСТОРАН DENIZ\n")
        printer.text("=" * 32 + "\n")
        
        # Контактная информация
        printer.set(align='center', text_type='normal')
        printer.text("Адрес: [Адрес ресторана]\n")
        printer.text("Телефон: +993 12 XX-XX-XX\n\n")
        
        # Детали заказа
        printer.set(align='left')
        printer.text(f"Стол: {order_data['table_id']}        Заказ: #{order_data['order_number']}\n")
        printer.text(f"Дата: {order_data['date']}  Время: {order_data['time']}\n")
        printer.text(f"Гостей: {order_data['guests']}      Официант: {order_data['waiter_name']}\n\n")
        
        # Все позиции С ЦЕНАМИ
        total = 0
        for item in order_data['items']:
            item_total = item['quantity'] * item['price']
            total += item_total
            
            printer.text(f"{item['quantity']}x {item['name']}")
            printer.text(f"{item_total:.2f}".rjust(32 - len(f"{item['quantity']}x {item['name']}")) + "\n")
            
            if item['comments']:
                printer.text(f"   - {item['comments']}\n")
        
        # Расчеты
        printer.text("-" * 32 + "\n")
        printer.text(f"Подытог:{total:.2f}".rjust(32) + "\n")
        
        service_charge = total * (order_data['service_percent'] / 100)
        printer.text(f"Сервисный сбор ({order_data['service_percent']}%):{service_charge:.2f}".rjust(32) + "\n")
        
        subtotal_with_service = total + service_charge
        
        # Скидочная карта (если есть)
        if order_data.get('discount_card'):
            printer.text(f"Промежуточный итог:{subtotal_with_service:.2f}".rjust(32) + "\n")
            
            discount = subtotal_with_service * (order_data['discount_percent'] / 100)
            printer.text(f"Скидка по карте {order_data['discount_card']} ({order_data['discount_percent']}%):")
            printer.text(f"-{discount:.2f}".rjust(32 - len(f"Скидка по карте {order_data['discount_card']} ({order_data['discount_percent']}%):")) + "\n")
            
            final_total = subtotal_with_service - discount
        else:
            final_total = subtotal_with_service
        
        printer.text("-" * 32 + "\n")
        printer.set(text_type='B')
        printer.text(f"ИТОГО:{final_total:.2f}".rjust(32) + "\n")
        printer.set(text_type='normal')
        printer.text("=" * 32 + "\n")
        
        # Информация об оплате
        printer.text(f"Способ оплаты: Наличные\n")
        printer.text(f"Время оплаты: {order_data['payment_time']}\n\n")
        
        printer.set(align='center')
        printer.text("Благодарим за посещение!\n")
        printer.text("=" * 32 + "\n")
        
        printer.cut()
        printer.close()
        
    except Exception as e:
        log_error(f"Receipt printer error: {e}")
```

## Конфигурация системы

### Файл config.py
```python
PRINTERS = {
    'kitchen': {
        'type': 'network',
        'ip': '192.168.1.101',
        'port': 9100,
        'width': 80,  # mm
        'chars_per_line': 48
    },
    'bar': {
        'type': 'usb',
        'vendor_id': 0x1CB0,  # Определить для ZyWell 5890K
        'product_id': 0x0007,
        'width': 58,  # mm  
        'chars_per_line': 32
    },
    'receipt': {
        'type': 'usb',
        'vendor_id': 0x1CB0,
        'product_id': 0x0008,  # Или через USB hub
        'width': 58,  # mm
        'chars_per_line': 32
    }
}

RESTAURANT_INFO = {
    'name': 'DENIZ',
    'address': '[Адрес ресторана]',
    'phone': '+993 12 XX-XX-XX',
    'service_charge_percent': 10
}
```

### Обработка ошибок печати
```python
import queue
import threading
import time

retry_queue = queue.Queue()

def add_to_retry_queue(printer_type, order_data, items):
    retry_queue.put({
        'printer': printer_type,
        'order': order_data,
        'items': items,
        'timestamp': time.time(),
        'attempts': 0
    })

def retry_failed_prints():
    """Фоновый поток для повтора неуспешной печати"""
    while True:
        try:
            if not retry_queue.empty():
                job = retry_queue.get()
                
                if job['attempts'] < 3:  # Максимум 3 попытки
                    job['attempts'] += 1
                    
                    if job['printer'] == 'kitchen':
                        print_kitchen_receipt(job['order'], job['items'])
                    elif job['printer'] == 'bar':
                        print_bar_receipt(job['order'], job['items'])
                    elif job['printer'] == 'receipt':
                        print_final_receipt(job['order'])
                else:
                    log_error(f"Failed to print after 3 attempts: {job}")
                    
        except Exception as e:
            log_error(f"Retry thread error: {e}")
            
        time.sleep(30)  # Проверять каждые 30 секунд

# Запустить фоновый поток
threading.Thread(target=retry_failed_prints, daemon=True).start()
```

## API для Flask приложения

```python
@app.route('/api/print/order', methods=['POST'])
def print_order():
    try:
        order_data = request.json
        process_order(order_data)
        return {'status': 'success', 'message': 'Order sent to printers'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/print/receipt', methods=['POST']) 
def print_receipt():
    try:
        order_data = request.json
        print_final_receipt(order_data)
        return {'status': 'success', 'message': 'Receipt printed'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500
```

## Зависимости Python

```bash
pip install python-escpos
pip install flask
pip install pyusb  # Для USB принтеров
```

## Команды для определения USB принтеров

```bash
# Linux
lsusb | grep -i printer

# Python код для поиска USB принтеров
import usb.core
devices = usb.core.find(find_all=True)
for device in devices:
    print(f"Vendor ID: 0x{device.idVendor:04x}, Product ID: 0x{device.idProduct:04x}")
```