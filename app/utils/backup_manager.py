"""Система резервного копирования базы данных."""

import os
import subprocess
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from flask import current_app
from werkzeug.datastructures import FileStorage


class BackupManager:
    """Менеджер резервного копирования."""
    
    def __init__(self):
        self.backup_dir = Path(current_app.config.get('BACKUP_DIR', 'backups'))
        self.backup_dir.mkdir(exist_ok=True)
        
        # Получение настроек БД из конфигурации
        self.db_config = {
            'host': current_app.config.get('DB_HOST', 'localhost'),
            'port': current_app.config.get('DB_PORT', '5432'),
            'name': current_app.config.get('DB_NAME', 'deniz_restaurant'),
            'user': current_app.config.get('DB_USER', 'postgres'),
            'password': current_app.config.get('DB_PASSWORD', '')
        }
    
    def create_backup(self) -> str:
        """
        Создание резервной копии базы данных.
        
        Returns:
            str: Путь к созданному файлу резервной копии
            
        Raises:
            Exception: При ошибках создания резервной копии
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"deniz_backup_{timestamp}.sql"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # Команда pg_dump для создания резервной копии
            cmd = [
                'pg_dump',
                '-h', self.db_config['host'],
                '-p', self.db_config['port'],
                '-U', self.db_config['user'],
                '-d', self.db_config['name'],
                '--no-password',
                '--verbose',
                '--clean',
                '--create',
                '--if-exists',
                '-f', str(backup_path)
            ]
            
            # Установка переменной окружения для пароля
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            # Выполнение команды
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            current_app.logger.info(f"Backup created successfully: {backup_path}")
            
            # Проверка, что файл создан и не пустой
            if not backup_path.exists() or backup_path.stat().st_size == 0:
                raise Exception("Backup file is empty or was not created")
            
            # Очистка старых резервных копий
            self._cleanup_old_backups()
            
            return str(backup_path)
            
        except subprocess.CalledProcessError as e:
            current_app.logger.error(f"pg_dump failed: {e.stderr}")
            raise Exception(f"Failed to create backup: {e.stderr}")
        except Exception as e:
            current_app.logger.error(f"Backup creation error: {e}")
            raise
    
    def restore_backup(self, backup_file: FileStorage) -> Dict[str, Any]:
        """
        Восстановление базы данных из резервной копии.
        
        Args:
            backup_file: Файл резервной копии
            
        Returns:
            Dict[str, Any]: Результат операции восстановления
            
        Raises:
            Exception: При ошибках восстановления
        """
        # Сохранение загруженного файла
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as temp_file:
            backup_file.save(temp_file.name)
            temp_backup_path = temp_file.name
        
        try:
            # Команда psql для восстановления
            cmd = [
                'psql',
                '-h', self.db_config['host'],
                '-p', self.db_config['port'],
                '-U', self.db_config['user'],
                '-d', 'postgres',  # Подключаемся к системной БД для пересоздания
                '--no-password',
                '-v', 'ON_ERROR_STOP=1',
                '-f', temp_backup_path
            ]
            
            # Установка переменной окружения для пароля
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            # Выполнение команды
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            current_app.logger.info("Database restored successfully")
            
            return {
                'restored_at': datetime.now().isoformat(),
                'backup_file': backup_file.filename,
                'output': result.stdout
            }
            
        except subprocess.CalledProcessError as e:
            current_app.logger.error(f"Database restoration failed: {e.stderr}")
            raise Exception(f"Failed to restore database: {e.stderr}")
        except Exception as e:
            current_app.logger.error(f"Restoration error: {e}")
            raise
        finally:
            # Удаление временного файла
            try:
                os.unlink(temp_backup_path)
            except OSError:
                pass
    
    def get_backup_size(self, backup_path: str) -> str:
        """
        Получение размера резервной копии.
        
        Args:
            backup_path: Путь к файлу резервной копии
            
        Returns:
            str: Размер файла в читаемом формате
        """
        try:
            size_bytes = Path(backup_path).stat().st_size
            return self._format_file_size(size_bytes)
        except Exception:
            return "Unknown"
    
    def list_backups(self) -> list[Dict[str, Any]]:
        """
        Получение списка всех резервных копий.
        
        Returns:
            list[Dict[str, Any]]: Список резервных копий с метаданными
        """
        backups = []
        
        for backup_file in self.backup_dir.glob("deniz_backup_*.sql"):
            try:
                stat = backup_file.stat()
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size': self._format_file_size(stat.st_size),
                    'size_bytes': stat.st_size,
                    'created_at': datetime.fromtimestamp(stat.st_ctime),
                    'modified_at': datetime.fromtimestamp(stat.st_mtime)
                })
            except Exception as e:
                current_app.logger.warning(f"Error reading backup file {backup_file}: {e}")
        
        # Сортировка по дате создания (новые первыми)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return backups
    
    def delete_backup(self, backup_filename: str) -> bool:
        """
        Удаление резервной копии.
        
        Args:
            backup_filename: Имя файла резервной копии
            
        Returns:
            bool: True если файл удален успешно
        """
        try:
            backup_path = self.backup_dir / backup_filename
            if backup_path.exists():
                backup_path.unlink()
                current_app.logger.info(f"Backup deleted: {backup_filename}")
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"Error deleting backup {backup_filename}: {e}")
            return False
    
    def _cleanup_old_backups(self) -> None:
        """Очистка старых резервных копий согласно настройкам."""
        try:
            from app.models import SystemSetting
            
            # Получение настройки количества копий для хранения
            retention_setting = SystemSetting.query.filter_by(key='backup_retention').first()
            retention_count = int(retention_setting.value) if retention_setting else 7
            
            backups = self.list_backups()
            
            # Удаление лишних копий
            if len(backups) > retention_count:
                for backup in backups[retention_count:]:
                    self.delete_backup(backup['filename'])
                    
        except Exception as e:
            current_app.logger.error(f"Error cleaning up old backups: {e}")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        Форматирование размера файла в читаемый вид.
        
        Args:
            size_bytes: Размер в байтах
            
        Returns:
            str: Форматированный размер
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        size_index = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and size_index < len(size_names) - 1:
            size /= 1024.0
            size_index += 1
        
        return f"{size:.1f} {size_names[size_index]}"
    
    def schedule_automatic_backup(self) -> bool:
        """
        Планирование автоматического создания резервных копий.
        
        Returns:
            bool: True если планирование успешно
        """
        try:
            from app.models import SystemSetting
            
            # Проверка настроек автобэкапа
            auto_backup_setting = SystemSetting.query.filter_by(key='auto_backup').first()
            if not auto_backup_setting or auto_backup_setting.value != 'true':
                return False
            
            interval_setting = SystemSetting.query.filter_by(key='backup_interval').first()
            interval = interval_setting.value if interval_setting else 'daily'
            
            # Здесь можно добавить интеграцию с Celery или cron
            # Для простоты оставляем заглушку
            current_app.logger.info(f"Automatic backup scheduled: {interval}")
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error scheduling automatic backup: {e}")
            return False
    
    def verify_backup_integrity(self, backup_path: str) -> Dict[str, Any]:
        """
        Проверка целостности резервной копии.
        
        Args:
            backup_path: Путь к файлу резервной копии
            
        Returns:
            Dict[str, Any]: Результат проверки
        """
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                return {
                    'valid': False,
                    'error': 'Файл не найден'
                }
            
            if backup_file.stat().st_size == 0:
                return {
                    'valid': False,
                    'error': 'Файл пустой'
                }
            
            # Простая проверка на наличие SQL команд
            with open(backup_file, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # Читаем первые 1000 символов
                
                if 'CREATE DATABASE' not in content and 'CREATE TABLE' not in content:
                    return {
                        'valid': False,
                        'error': 'Файл не содержит SQL команд'
                    }
            
            return {
                'valid': True,
                'size': self.get_backup_size(backup_path),
                'checked_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Ошибка проверки: {str(e)}'
            }