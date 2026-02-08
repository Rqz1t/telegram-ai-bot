import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def _get_base_dir() -> Path:
    """Определяет корневую директорию, учитывая запуск через PyInstaller."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

# =============================================================================
# Paths
# =============================================================================
BASE_DIR = _get_base_dir()
load_dotenv(BASE_DIR / ".env")

MODELS_DIR = BASE_DIR / "models"
DB_PATH = BASE_DIR / "bot.db"
LOG_PATH = BASE_DIR / "bot.log"

# =============================================================================
# Secrets & Environment
# =============================================================================
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    # Fail fast: нет смысла запускать бота без токена
    raise ValueError("Переменная окружения TOKEN не найдена!")

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# =============================================================================
# Application Constraints
# =============================================================================
MAX_VIDEO_SIZE_MB = 50
MAX_VIDEO_DURATION_SEC = 60
MAX_IMAGE_SIZE_MB = 10
UPSCALE_FACTOR = 4