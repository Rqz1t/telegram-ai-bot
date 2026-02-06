from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types

def main_menu() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🤖 Мои проекты", callback_data="projects"))
    builder.row(types.InlineKeyboardButton(text="👤 Кто я?", callback_data="about"))
    builder.row(
        types.InlineKeyboardButton(text="📍 Статус", callback_data="status"),
        types.InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")
    )
    return builder.as_markup()

def back_button() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
    return builder.as_markup()

def converter_menu() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="❌ Отмена / Назад", callback_data="back"))
    return builder.as_markup()

def projects_menu() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎬 Запустить Video2Round", callback_data="run_v2r"))
    builder.row(types.InlineKeyboardButton(text="🖼️ Запустить AI Upscale", callback_data="run_ai_upscale"))  # Новая кнопка
    builder.row(types.InlineKeyboardButton(text="📚 FAQ по Video2Round", callback_data="faq_v2r"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back"))
    return builder.as_markup()