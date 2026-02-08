import asyncio
import io
import logging
import sys

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import TOKEN
from bot.database import init_db
from bot.handlers import dp

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _configure_io_encoding() -> None:
    """
    Принудительно устанавливает кодировку UTF-8 для stdout/stderr.
    Это предотвращает UnicodeEncodeError в Windows-консолях или Docker-контейнерах.
    """
    for stream_name in ('stdout', 'stderr'):
        stream = getattr(sys, stream_name)
        if stream is not None:
            try:
                # Переоборачиваем поток с явным указанием кодировки
                new_stream = io.TextIOWrapper(
                    stream.detach(), 
                    encoding='utf-8', 
                    errors='replace'
                )
                setattr(sys, stream_name, new_stream)
            except AttributeError:
                # Игнорируем, если поток уже настроен или недоступен
                pass


async def main() -> None:
    """Точка входа в приложение."""
    _configure_io_encoding()
    
    logger.info("🚀 Инициализация базы данных...")
    try:
        init_db()
    except Exception as e:
        logger.critical(f"❌ Ошибка инициализации БД: {e}")
        return

    logger.info("🚀 Запуск бота...")
    
    # Инициализируем бота с дефолтными настройками (HTML-парсинг везде)
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    try:
        # Удаляем вебхук и сбрасываем обновления, накопившиеся пока бот спал
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаем поллинг (long-polling)
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Критическая ошибка в работе бота: {e}")
    finally:
        # Гарантированно закрываем сессию при выходе
        await bot.session.close()
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен вручную.")