import asyncio
import logging
from logging.handlers import RotatingFileHandler
from aiogram import Bot, Dispatcher
from .config import TOKEN, BASE_DIR, LOG_PATH
from .database import init_db
from .handlers import dp
import sys
import io

# Принудительно UTF-8 для stdout/stderr
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', errors='replace')

# ���� � ���� ����� � exe
handler = RotatingFileHandler(LOG_PATH, maxBytes=5*1024*1024, backupCount=5)
logging.basicConfig(
    level=logging.INFO,
    handlers=[handler],
    format='%(asctime)s - %(levelname)s - %(message)s'
)

bot = Bot(token=TOKEN)

async def main():
    init_db()
    logging.info("MaximusBot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("бот остановлен")