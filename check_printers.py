from escpos.printer import Serial

def test_com3_printer():
    """Тест принтера через COM3"""
    try:
        print("Подключение к принтеру через COM3...")
        
        printer = Serial(
            devfile='COM3',
            baudrate=9600,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1,
            dsrdtr=True
        )
        
        print("✅ COM3 подключен!")
        
        # Устанавливаем кодировку для кириллицы
        printer._raw(bytes([0x1b, 0x74, 37]))  # Code Page 37
        
        # Тест печати
        printer.text("=== COM3 ПРИНТЕР ===\n")
        printer.text("Порт: COM3\n")
        printer.text("Скорость: 9600\n")
        printer.text("Тест кириллицы: Привет мир!\n")
        printer.text("Дата: 29 января 2025\n")
        printer.text("Принтер: EML POS-58\n")
        printer.text("========================\n\n")
        
        printer.text("Я ЧЕБУРЕК\n\n")
        
        # QR код
        printer.text("QR код COM3:\n")
        printer.qr("COM3-TEST", size=8)
        printer.text("\n")
        
        printer.cut()
        print("COM3 тест завершен!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка COM3: {e}")
        return False

def test_com4_printer():
    """Тест принтера через COM4"""
    try:
        print("Подключение к принтеру через COM4...")
        
        printer = Serial(
            devfile='COM4',
            baudrate=9600,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1,
            dsrdtr=True
        )
        
        print("✅ COM4 подключен!")
        
        # Устанавливаем кодировку для кириллицы
        printer._raw(bytes([0x1b, 0x74, 37]))  # Code Page 37
        
        # Тест печати
        printer.text("=== COM4 ПРИНТЕР ===\n")
        printer.text("Порт: COM4\n")
        printer.text("Скорость: 9600\n")
        printer.text("Тест кириллицы: Привет мир!\n")
        printer.text("Дата: 29 января 2025\n")
        printer.text("Принтер: EML POS-58\n")
        printer.text("========================\n\n")
        
        printer.text("А Я ПИРАЖКИ\n\n")
        
        # QR код
        printer.text("QR код COM4:\n")
        printer.qr("COM4-TEST", size=8)
        printer.text("\n")
        
        printer.cut()
        print("COM4 тест завершен!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка COM4: {e}")
        return False

def test_both_ports():
    """Тест обоих COM-портов"""
    print("Тест принтеров EML POS-58 через COM3 и COM4")
    print("=" * 50)
    
    # Тестируем COM3
    print("\n1. Тестирование COM3:")
    print("-" * 20)
    com3_success = test_com3_printer()
    
    # Тестируем COM4
    print("\n2. Тестирование COM4:")
    print("-" * 20)
    com4_success = test_com4_printer()
    
    # Результаты
    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"COM3: {'✅ РАБОТАЕТ' if com3_success else '❌ НЕ РАБОТАЕТ'}")
    print(f"COM4: {'✅ РАБОТАЕТ' if com4_success else '❌ НЕ РАБОТАЕТ'}")
    
    if com3_success and com4_success:
        print("\n�� Оба порта работают!")
    elif com3_success or com4_success:
        print("\n⚠️ Работает только один порт")
    else:
        print("\n💥 Ни один порт не работает")

if __name__ == "__main__":
    test_both_ports()