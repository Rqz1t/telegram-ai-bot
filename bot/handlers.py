"""
handlers.py

Все хендлеры Telegram-бота:
- команды
- callback-кнопки
- FSM
- видео-конвертер
- AI Upscale (Real-ESRGAN, production-ready)
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from pathlib import Path
from bot.ai.upscale import UpscaleService

import torch
import torchvision

print(torch.__version__)
print(torchvision.__version__)
print(torch.cuda.is_available())


from aiogram import Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from moviepy.video.io.VideoFileClip import VideoFileClip
from PIL import Image

from .config import (
    ADMIN_ID,
    MAX_VIDEO_SIZE_MB,
    MAX_VIDEO_DURATION_SEC,
    MAX_IMAGE_SIZE_MB,
    UPSCALE_FACTOR,
)
from .database import get_status, set_status, log_action, get_stats
from .keyboards import main_menu, projects_menu, back_button, converter_menu

# =============================================================================
# Dispatcher
# =============================================================================

dp: Dispatcher = Dispatcher()
UPSCALE_SERVICE = UpscaleService()


# =============================================================================
# FSM States
# =============================================================================

class Form(StatesGroup):
    """
    FSM состояния.

    waiting_for_video — ожидаем видео
    waiting_for_image — ожидаем изображение (ТОЛЬКО document)
    """
    waiting_for_video: State = State()
    waiting_for_image: State = State()

# =============================================================================
# Middleware
# =============================================================================

async def logging_middleware(
    handler: Any,
    event: Any,
    data: dict[str, Any],
) -> Any:
    """
    Минимальное логирование апдейтов.

    Не логируем payload целиком — это мусор и риск утечек.
    """
    user_id = getattr(getattr(event, "from_user", None), "id", "unknown")
    event_type = "message" if isinstance(event, types.Message) else "callback"
    logging.info("Incoming %s from user=%s", event_type, user_id)
    return await handler(event, data)


dp.message.middleware(logging_middleware)
dp.callback_query.middleware(logging_middleware)

# =============================================================================
# Global error handler
# =============================================================================

@dp.errors()
async def error_handler(event: types.ErrorEvent) -> None:
    """
    Глобальный перехват ошибок.

    Пользователь видит молчаливый фейл,
    админ — полный текст ошибки.
    """
    logging.exception("Unhandled exception")

    try:
        await event.update.bot.send_message(
            ADMIN_ID,
            f"❌ Ошибка:\n{event.exception}",
        )
    except Exception:
        pass

# =============================================================================
# Admin commands
# =============================================================================

@dp.message(Command("set_status"))
async def set_status_command(message: types.Message) -> None:
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещён.")
        return

    status = message.text.replace("/set_status", "").strip()
    if not status:
        await message.answer("Пример: `/set_status Сплю`", parse_mode="Markdown")
        return

    set_status(status)
    log_action(message.from_user.id, "set_status")

    await message.answer(
        f"✅ Статус обновлён:\n<b>{status}</b>",
        parse_mode="HTML",
    )

@dp.message(Command("stats"))
async def stats_command(message: types.Message) -> None:
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещён.")
        return

    users, conversions, upscales = get_stats()
    await message.answer(
        f"📊 Статистика:\n"
        f"Пользователей: {users}\n"
        f"Видео: {conversions}\n"
        f"Upscale: {upscales}"
    )

# =============================================================================
# Base handlers
# =============================================================================

@dp.message(Command("start"))
async def start_handler(message: types.Message) -> None:
    log_action(message.from_user.id, "start")

    try:
        await message.bot.send_message(
            ADMIN_ID,
            f"🆕 Новый пользователь: {message.from_user.id}",
        )
    except Exception:
        pass

    await message.answer(
        "Привет! 👋\nВыбери раздел:",
        reply_markup=main_menu(),
    )

# =============================================================================
# Callback handlers
# =============================================================================

@dp.callback_query(F.data == "projects")
async def projects_handler(callback: types.CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "🛠 Проекты:\n\n"
        "1. Видео → кружок\n"
        "2. AI Upscale изображений",
        reply_markup=projects_menu(),
    )

@dp.callback_query(F.data == "run_v2r")
async def run_video_converter(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Form.waiting_for_video)
    await callback.message.edit_text(
        "🎬 Пришли видео (до 50 МБ, до 60 сек)",
        reply_markup=converter_menu(),
    )

@dp.callback_query(F.data == "run_ai_upscale")
async def run_ai_upscale(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Form.waiting_for_image)
    await callback.message.edit_text(
        "🖼 Пришли изображение КАК ФАЙЛ 📎\n"
        "Фото Telegram сжимает.",
        reply_markup=back_button(),
    )

@dp.callback_query(F.data == "back")
async def back_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu())

# =============================================================================
# Video processing
# =============================================================================

@dp.message(Form.waiting_for_video, F.video)
async def process_video(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id

    if message.video.file_size > MAX_VIDEO_SIZE_MB * 1024 * 1024:
        await message.answer("❌ Видео слишком большое.")
        return

    status = await message.answer("⏳ Обрабатываю видео...")
    input_path = f"input_{user_id}.mp4"
    output_path = f"round_{user_id}.mp4"
    clip: Optional[VideoFileClip] = None

    try:
        await message.bot.download(message.video, input_path)
        clip = VideoFileClip(input_path)

        if clip.duration > MAX_VIDEO_DURATION_SEC:
            clip = clip.subclip(0, MAX_VIDEO_DURATION_SEC)

        w, h = clip.size
        side = min(w, h)
        clip = clip.crop(x_center=w / 2, y_center=h / 2, width=side, height=side)
        clip = clip.resize(height=400)

        clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )

        await message.answer_video_note(types.FSInputFile(output_path))
        log_action(user_id, "conversion")
        await status.delete()

    finally:
        if clip:
            clip.close()
        for p in (input_path, output_path):
            if os.path.exists(p):
                os.remove(p)
        await state.clear()

# =============================================================================
# AI Upscale (REAL Real-ESRGAN)
# =============================================================================

@dp.message(Form.waiting_for_image, F.document)
async def process_image(message: types.Message, state: FSMContext) -> None:
    """
    Обработка изображения для AI Upscale.

    ВАЖНО:
    - принимаем ТОЛЬКО document (Telegram не сжимает)
    - апскейл выполняется через Python Real-ESRGAN
    """

    user_id = message.from_user.id
    document = message.document

    # Дополнительная защита: Telegram может прислать document не-картинкой
    if not document.mime_type or not document.mime_type.startswith("image/"):
        await message.answer("❌ Это не изображение.")
        return

    if document.file_size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        await message.answer("❌ Изображение слишком большое.")
        return

    input_path = Path(f"input_{user_id}.png")
    output_path = Path(f"upscaled_{user_id}.png")

    status_msg = await message.answer("⏳ Улучшаю изображение...")

    try:
        # 1️⃣ Скачиваем файл
        file = await message.bot.get_file(document.file_id)
        await message.bot.download_file(file.file_path, input_path)

        # 2️⃣ Апскейл (синхронный, но модель уже загружена)
        UPSCALE_SERVICE.upscale(input_path, output_path)

        # 3️⃣ Отправляем результат
        await message.answer_document(
            types.FSInputFile(output_path),
            caption=f"✅ Качество улучшено ×{UPSCALE_FACTOR}",
        )

        log_action(user_id, "ai_upscale")
        await status_msg.delete()

    except Exception as exc:
        logging.exception("AI upscale error")
        await status_msg.edit_text("❌ Ошибка при обработке изображения.")
        await message.bot.send_message(ADMIN_ID, f"Upscale error:\n{exc}")

    finally:
        # Чистим временные файлы и FSM
        for path in (input_path, output_path):
            if path.exists():
                path.unlink()
        await state.clear()

@dp.message(Form.waiting_for_image)
async def not_image_handler(message: types.Message) -> None:
    await message.answer("Жду изображение, отправленное как файл 📎")
