"""Утилиты для загрузки и обработки изображений."""

import os
import uuid
from pathlib import Path
from typing import Optional, Tuple
from werkzeug.utils import secure_filename
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class ImageUploadManager:
    """Менеджер загрузки изображений."""
    
    # Разрешенные форматы
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Максимальный размер файла (5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    # Стандартные размеры для разных типов изображений
    IMAGE_SIZES = {
        'banner': (1200, 600),      # Баннеры карусели
        'meal': (800, 600),         # Блюда
        'thumbnail': (300, 200),    # Миниатюры
        'icon': (100, 100),         # Иконки
    }
    
    @classmethod
    def allowed_file(cls, filename: str) -> bool:
        """Проверка разрешенного расширения файла."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def validate_file_size(cls, file_size: int) -> bool:
        """Проверка размера файла."""
        return file_size <= cls.MAX_FILE_SIZE
    
    @classmethod
    def generate_unique_filename(cls, original_filename: str) -> str:
        """Генерация уникального имени файла."""
        # Получаем расширение
        ext = original_filename.rsplit('.', 1)[1].lower()
        
        # Генерируем уникальное имя
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        
        return unique_name
    
    @classmethod
    def save_image(cls, file, image_type: str, base_path: str = 'app/static/assets') -> Tuple[bool, str, str]:
        """
        Сохранение загруженного изображения.
        
        Args:
            file: Файл для загрузки
            image_type: Тип изображения (banner, meal, thumbnail, icon)
            base_path: Базовый путь для сохранения
            
        Returns:
            Tuple[bool, str, str]: (успех, путь к файлу, сообщение об ошибке)
        """
        try:
            # Проверяем файл
            if not file or file.filename == '':
                return False, '', 'Файл не выбран'
            
            if not cls.allowed_file(file.filename):
                return False, '', f'Неподдерживаемый формат файла. Разрешены: {", ".join(cls.ALLOWED_EXTENSIONS)}'
            
            # Проверяем размер
            file.seek(0, 2)  # Перемещаемся в конец файла
            file_size = file.tell()
            file.seek(0)  # Возвращаемся в начало
            
            if not cls.validate_file_size(file_size):
                return False, '', f'Файл слишком большой. Максимальный размер: {cls.MAX_FILE_SIZE // (1024*1024)}MB'
            
            # Создаем директории
            upload_path = Path(base_path) / image_type
            upload_path.mkdir(parents=True, exist_ok=True)
            
            # Генерируем уникальное имя
            filename = cls.generate_unique_filename(file.filename)
            file_path = upload_path / filename
            
            # Сохраняем оригинальный файл
            file.save(str(file_path))
            
            # Обрабатываем изображение
            cls.process_image(str(file_path), image_type)
            
            # Возвращаем относительный путь для БД
            relative_path = f"{image_type}/{filename}"
            
            logger.info(f"Image uploaded successfully: {relative_path}")
            return True, relative_path, 'Изображение загружено успешно'
            
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            return False, '', f'Ошибка загрузки изображения: {str(e)}'
    
    @classmethod
    def process_image(cls, file_path: str, image_type: str) -> bool:
        """
        Обработка загруженного изображения.
        
        Args:
            file_path: Путь к файлу
            image_type: Тип изображения
            
        Returns:
            bool: Успех обработки
        """
        try:
            # Открываем изображение
            with Image.open(file_path) as img:
                # Конвертируем в RGB если нужно
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Получаем целевые размеры
                target_size = cls.IMAGE_SIZES.get(image_type, (800, 600))
                
                # Изменяем размер, сохраняя пропорции
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                # Сохраняем обработанное изображение
                img.save(file_path, quality=85, optimize=True)
                
            return True
            
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {e}")
            return False
    
    @classmethod
    def delete_image(cls, image_path: str, base_path: str = 'static/assets') -> bool:
        """
        Удаление изображения.
        
        Args:
            image_path: Относительный путь к изображению
            base_path: Базовый путь
            
        Returns:
            bool: Успех удаления
        """
        try:
            full_path = Path(base_path) / image_path
            
            if full_path.exists():
                full_path.unlink()
                logger.info(f"Image deleted: {image_path}")
                return True
            else:
                logger.warning(f"Image not found for deletion: {image_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting image {image_path}: {e}")
            return False
    
    @classmethod
    def get_image_url(cls, image_path: str) -> str:
        """
        Получение URL для изображения.
        
        Args:
            image_path: Относительный путь к изображению
            
        Returns:
            str: URL изображения
        """
        if not image_path:
            return ''
        
        # Убираем 'static/' из пути, так как Flask автоматически обслуживает static
        if image_path.startswith('static/'):
            image_path = image_path[7:]
        
        return f"/static/assets/{image_path}"
    
    @classmethod
    def cleanup_orphaned_images(cls, base_path: str = 'static/assets') -> int:
        """
        Очистка "осиротевших" изображений.
        
        Args:
            base_path: Базовый путь
            
        Returns:
            int: Количество удаленных файлов
        """
        deleted_count = 0
        
        try:
            assets_path = Path(base_path)
            
            if not assets_path.exists():
                return 0
            
            # Проходим по всем поддиректориям
            for image_type_dir in assets_path.iterdir():
                if image_type_dir.is_dir():
                    for image_file in image_type_dir.iterdir():
                        if image_file.is_file() and image_file.suffix.lower() in cls.ALLOWED_EXTENSIONS:
                            # Здесь можно добавить логику проверки использования в БД
                            # Пока просто логируем
                            logger.info(f"Found image: {image_file}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return deleted_count
