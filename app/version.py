"""Версионирование приложения."""

import os
from datetime import datetime
from typing import Dict, Any

# Версия приложения
__version__ = "1.0.0"
__build__ = "dev"
__release_date__ = "2025-01-29"

def get_version_info() -> Dict[str, Any]:
    """Получение информации о версии."""
    return {
        "version": __version__,
        "build": __build__,
        "release_date": __release_date__,
        "build_time": datetime.utcnow().isoformat(),
        "python_version": os.sys.version,
        "environment": os.environ.get('FLASK_ENV', 'development'),
    }

def get_version_string() -> str:
    """Строковое представление версии."""
    return f"{__version__}-{__build__}"

# Для автоматического определения версии из git
def get_git_version() -> str:
    """Получение версии из git."""
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'describe', '--tags', '--always', '--dirty'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return get_version_string() 