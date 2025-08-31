import sys
import usb.core
import usb.util

def check_usb_printers():
    """Проверка USB принтеров"""
    print("Поиск USB принтеров...")
    print("=" * 50)
    
    try:
        # Поиск всех USB устройств
        devices = usb.core.find(find_all=True)
        
        if devices is None:
            print("USB устройства не найдены")
            return
        
        printer_count = 0
        for device in devices:
            try:
                vendor_id = device.idVendor
                product_id = device.idProduct
                
                # Попытка получить описание устройства
                try:
                    vendor_name = usb.util.get_string(device, device.iManufacturer)
                except:
                    vendor_name = "Unknown"
                
                try:
                    product_name = usb.util.get_string(device, device.iProduct)
                except:
                    product_name = "Unknown"
                
                print(f"USB устройство:")
                print(f"   Vendor ID: 0x{vendor_id:04x}")
                print(f"   Product ID: 0x{product_id:04x}")
                print(f"   Vendor: {vendor_name}")
                print(f"   Product: {product_name}")
                print(f"   Bus: {device.bus}")
                print(f"   Address: {device.address}")
                print("-" * 30)
                
                # Проверяем, похоже ли на принтер
                if any(keyword in product_name.lower() for keyword in ['printer', 'print', 'zywell', '5890k', 'pos-58', 'eml']):
                    print("ВОЗМОЖНО ЭТО ПРИНТЕР!")
                    printer_count += 1
                
            except Exception as e:
                print(f"Ошибка чтения устройства: {e}")
                continue
        
        print(f"Найдено устройств: {len(list(devices))}")
        print(f"Возможных принтеров: {printer_count}")
        
    except Exception as e:
        print(f"Ошибка при поиске USB устройств: {e}")

def check_escpos_printers():
    """Проверка через python-escpos"""
    print("\nПроверка через python-escpos...")
    print("=" * 50)
    
    try:
        from escpos.printer import Usb, Network
        
        print("python-escpos импортирован успешно")
        
        # Попробуем найти USB принтеры через escpos
        print("\nПоиск USB принтеров через escpos...")
        
        # Список известных Vendor ID для принтеров
        known_vendors = {
            0x1CB0: "ZyWell",
            0x0483: "STMicroelectronics (EML POS-58)",
            0x04B8: "Epson",
            0x0525: "PLX Technology",
            0x0BDA: "Realtek",
            0x1A86: "QinHeng Electronics"
        }
        
        for vendor_id in known_vendors:
            try:
                print(f"\nПроверка {known_vendors[vendor_id]} (0x{vendor_id:04x})...")
                
                # Поиск устройств с этим Vendor ID
                devices = usb.core.find(find_all=True, idVendor=vendor_id)
                
                if devices:
                    for device in devices:
                        try:
                            product_id = device.idProduct
                            print(f"   Найден: 0x{product_id:04x}")
                            
                            # Попытка подключения через escpos
                            try:
                                printer = Usb(vendor_id, product_id)
                                print(f"   Успешное подключение через escpos!")
                                print(f"   Bus: {device.bus}, Address: {device.address}")
                            except Exception as e:
                                print(f"   Ошибка подключения: {e}")
                                
                        except Exception as e:
                            print(f"   Ошибка чтения: {e}")
                else:
                    print(f"   Устройства не найдены")
                    
            except Exception as e:
                print(f"   Ошибка проверки: {e}")
        
    except ImportError:
        print("python-escpos не установлен")
    except Exception as e:
        print(f"Ошибка при проверке escpos: {e}")

def check_network_printers():
    """Проверка сетевых принтеров"""
    print("\nПроверка сетевых принтеров...")
    print("=" * 50)
    
    # Список IP адресов для проверки
    network_ips = [
        "192.168.1.101",  # Кухонный принтер из документации
        "192.168.1.1",    # Роутер
        "192.168.1.10",   # Сервер
    ]
    
    import socket
    
    for ip in network_ips:
        try:
            print(f"Проверка {ip}...")
            
            # Проверка доступности порта 9100 (стандартный для принтеров)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, 9100))
            
            if result == 0:
                print(f"   Порт 9100 открыт - возможно это принтер!")
            else:
                print(f"   Порт 9100 закрыт")
                
            sock.close()
            
        except Exception as e:
            print(f"   Ошибка проверки: {e}")

if __name__ == "__main__":
    print("Проверка подключенных принтеров")
    print("=" * 50)
    
    check_usb_printers()
    check_escpos_printers()
    check_network_printers()
    
    print("\nПроверка завершена!")