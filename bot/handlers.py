import asyncio
import logging
import contextlib
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Union

# Сторонние библиотеки
from aiogram import Router, F, types, BaseMiddleware
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, CallbackQuery, Message

# Совместимость с MoviePy v2.0+
from moviepy.video.io.VideoFileClip import VideoFileClip
import moviepy.video.fx.all as vfx

# Локальные импорты
from bot.monitor import monitor
from bot.ai.upscale import UpscaleService
from .config import (
    ADMIN_ID,
    MAX_VIDEO_SIZE_MB,
    MAX_VIDEO_DURATION_SEC,
    MAX_IMAGE_SIZE_MB,
    UPSCALE_FACTOR,
)
from .database import set_status, log_action, get_stats, get_status as db_get_status
from .keyboards import main_menu, projects_menu, back_button, converter_menu

# Инициализация роутера (Best practice: использовать Router для модульности)
router = Router()
logger = logging.getLogger(__name__)

# Синглтон сервиса
UPSCALE_SERVICE = UpscaleService()


class Form(StatesGroup):
    """Состояния FSM для сценариев обработки."""
    waiting_for_video = State()
    waiting_for_image = State()


class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования входящих обновлений."""
    
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = getattr(event, "from_user", None)
        user_id = user.id if user else "unknown"
        event_type = event.__class__.__name__
        logger.info(f"Входящее событие {event_type} от user={user_id}")
        return await handler(event, data)


# Применяем middleware к роутеру
router.message.middleware(LoggingMiddleware())
router.callback_query.middleware(LoggingMiddleware())


# =============================================================================
# Вспомогательные функции и контекстные менеджеры
# =============================================================================

@contextlib.contextmanager
def temp_files_manager(*paths: Union[str, Path]):
    """
    Контекстный менеджер для автоматической очистки временных файлов.
    Гарантирует удаление файлов даже в случае возникновения исключений.
    """
    clean_paths = [Path(p) for p in paths]
    try:
        yield
    finally:
        for path in clean_paths:
            with contextlib.suppress(OSError):
                if path.exists():
                    path.unlink()


def _process_video_sync(input_path: str, output_path: str) -> None:
    """
    CPU-зависимая логика обработки видео (MoviePy).
    Должна запускаться в отдельном потоке/экзекьюторе, чтобы не блокировать event loop.
    """
    with VideoFileClip(input_path) as clip:
        # Обрезаем длительность
        if clip.duration > MAX_VIDEO_DURATION_SEC:
            clip = clip.subclip(0, MAX_VIDEO_DURATION_SEC)

        # Кропаем в квадрат и меняем размер
        w, h = clip.size
        side = min(w, h)
        
        # Синтаксис MoviePy 2.0+ (через vfx)
        clip = vfx.crop(clip, x_center=w / 2, y_center=h / 2, width=side, height=side)
        clip = vfx.resize(clip, height=400)

        clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            logger=None,
            preset="fast"  # Оптимизация скорости
        )


# =============================================================================
# Админские хендлеры
# =============================================================================

@router.message(Command("set_status"))
async def set_status_command(message: Message) -> None:
    if message.from_user.id != ADMIN_ID:
        return

    status = message.text.replace("/set_status", "").strip()
    if not status:
        await message.answer("Использование: `/set_status <текст>`", parse_mode="Markdown")
        return

    set_status(status)
    log_action(message.from_user.id, "set_status")
    await message.answer(f"✅ Статус обновлен:\n<b>{status}</b>", parse_mode="HTML")


@router.message(Command("stats"))
async def stats_command(message: Message) -> None:
    if message.from_user.id != ADMIN_ID:
        return

    users, conversions, upscales = get_stats()
    await message.answer(
        f"📊 <b>Статистика:</b>\n"
        f"Пользователей: {users}\n"
        f"Конвертаций видео: {conversions}\n"
        f"Upscale операций: {upscales}",
        parse_mode="HTML"
    )


# =============================================================================
# Меню и Навигация
# =============================================================================

@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    log_action(message.from_user.id, "start")
    monitor.log_event(message.from_user.full_name, "Бот запущен")
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\nВыбери раздел:",
        reply_markup=main_menu(),
    )


@router.callback_query(F.data == "about")
async def about_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    info = (
        "👤 <b>Разработчик Telegram-ботов</b>\n"
        "🆔 Специализируюсь на создании масштабируемых систем.\n"
        "📛 Чистый код и стабильность.\n"
        "🌐 Меня зовут Максим."
    )
    await callback.message.edit_text(
        text=info, 
        parse_mode="HTML", 
        reply_markup=back_button()
    )


@router.callback_query(F.data == "contacts")
async def contacts_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        text=(
            "📬 <b>Связь с разработчиком:</b>\n\n"
            "@MagaManiero\n"
            "GitHub: github.com/rqz1t"
        ),
        parse_mode="HTML",
        reply_markup=back_button()
    )


@router.callback_query(F.data == "status")
async def status_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    
    try:
        current_status = db_get_status()
    except Exception:
        logger.exception("Не удалось получить статус из БД")
        current_status = None
        
    status_text = current_status or "🟢 Работаю над кодом..."
    
    await callback.message.edit_text(
        text=f"ℹ️ <b>Текущий статус:</b>\n{status_text}", 
        parse_mode="HTML", 
        reply_markup=back_button()
    )


@router.callback_query(F.data == "projects")
async def projects_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        text="🛠 Выбери инструмент:",
        reply_markup=projects_menu(),
    )


@router.callback_query(F.data == "back")
async def back_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    
    # Проверка контекста: если сообщение с кнопками - редактируем, иначе шлем новое
    try:
        await callback.message.edit_text(
            text="Главное меню:", 
            reply_markup=main_menu()
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer("Главное меню:", reply_markup=main_menu())


# =============================================================================
# Запуск сценариев обработки
# =============================================================================

@router.callback_query(F.data == "run_v2r")
async def run_video_converter(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Form.waiting_for_video)
    await callback.message.edit_text(
        text="🎬 Пришли видео (до 50 МБ, до 60 сек)",
        reply_markup=converter_menu(),
    )


@router.callback_query(F.data == "run_ai_upscale")
async def run_ai_upscale(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Form.waiting_for_image)
    await callback.message.edit_text(
        text="🖼 Пришли изображение КАК ФАЙЛ 📎\nФото Telegram сжимает.",
        reply_markup=back_button(),
    )


# =============================================================================
# Логика обработки медиа
# =============================================================================

@router.message(Form.waiting_for_video, F.video)
async def process_video(message: Message, state: FSMContext) -> None:
    """Обрабатывает получение видео, валидацию и конвертацию."""
    user_id = message.from_user.id
    monitor.log_event(message.from_user.full_name, "Старт Video2Round")

    # Валидация
    if message.video.file_size > MAX_VIDEO_SIZE_MB * 1024 * 1024:
        await message.answer("❌ Видео слишком большое.", reply_markup=main_menu())
        return

    status_msg = await message.answer("⏳ Скачиваю и обрабатываю...")
    
    input_path = Path(f"temp_in_{user_id}.mp4")
    output_path = Path(f"temp_out_{user_id}.mp4")

    # Используем контекстный менеджер для авто-очистки
    with temp_files_manager(input_path, output_path):
        try:
            await message.bot.download(message.video, destination=input_path)

            # Запускаем тяжелую задачу в пуле потоков, чтобы не блокировать asyncio
            await asyncio.to_thread(
                _process_video_sync, 
                str(input_path), 
                str(output_path)
            )

            await message.answer_video_note(FSInputFile(output_path))
            await message.answer("✅ Готово!", reply_markup=main_menu())
            
            log_action(user_id, "conversion")

        except Exception as e:
            logger.error(f"Ошибка обработки видео для user {user_id}: {e}", exc_info=True)
            await message.answer("❌ Ошибка при обработке видео.")
        finally:
            with contextlib.suppress(Exception):
                await status_msg.delete()
            await state.clear()


@router.message(Form.waiting_for_image, F.document)
async def process_image(message: Message, state: FSMContext) -> None:
    """Обрабатывает получение изображения и AI upscale."""
    user_id = message.from_user.id
    monitor.log_event(message.from_user.full_name, "Старт AI Upscale")

    document = message.document
    if not document.mime_type or not document.mime_type.startswith("image/"):
        await message.answer("❌ Это не изображение.", reply_markup=main_menu())
        return

    if document.file_size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        await message.answer("❌ Изображение слишком большое.", reply_markup=main_menu())
        return

    status_msg = await message.answer("⏳ Улучшаю изображение...")
    
    input_path = Path(f"temp_up_in_{user_id}.png")
    output_path = Path(f"temp_up_out_{user_id}.png")

    with temp_files_manager(input_path, output_path):
        try:
            file_info = await message.bot.get_file(document.file_id)
            await message.bot.download_file(file_info.file_path, input_path)

            # Предполагаем, что upscale блокирующий, запускаем в потоке
            await asyncio.to_thread(
                UPSCALE_SERVICE.upscale, 
                input_path, 
                output_path
            )

            await message.answer_document(
                FSInputFile(output_path),
                caption=f"✅ Качество улучшено ×{UPSCALE_FACTOR}",
            )
            await message.answer("Готово! Что делаем дальше?", reply_markup=main_menu())
            
            log_action(user_id, "ai_upscale")

        except Exception as e:
            logger.error(f"Ошибка Upscale для user {user_id}: {e}", exc_info=True)
            await status_msg.edit_text("❌ Ошибка при обработке изображения.")
        finally:
            with contextlib.suppress(Exception):
                await status_msg.delete()
            await state.clear()


@router.message(Form.waiting_for_image)
async def not_image_handler(message: Message) -> None:
    await message.answer(
        "Жду изображение, отправленное как файл 📎", 
        reply_markup=back_button()
    )


# =============================================================================
# Обработка ошибок (Глобальная)
# =============================================================================

@router.errors()
async def global_error_handler(event: types.ErrorEvent) -> None:
    logger.exception(f"Необработанное исключение: {event.exception}")
    try:
        await event.update.bot.send_message(
            ADMIN_ID,
            f"❌ Критическая ошибка:\n<pre>{event.exception}</pre>",
            parse_mode="HTML"
        )
    except Exception:
        pass