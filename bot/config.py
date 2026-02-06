import os
from pathlib import Path
from dotenv import load_dotenv

# Корень проекта — родительская папка от bot/
BASE_DIR = Path(__file__).resolve().parent.parent

env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)  # Явно указываем путь — на всякий случай

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN не найден в .env! Проверь файл.")

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

DB_PATH = BASE_DIR / "bot.db"
LOG_PATH = BASE_DIR / "bot.log"

MAX_VIDEO_SIZE_MB = 50
MAX_VIDEO_DURATION_SEC = 60
MAX_IMAGE_SIZE_MB = 10  # Максимальный размер изображения для upscale
UPSCALE_FACTOR = 4 # Коэффициент увеличения (2x по умолчанию)