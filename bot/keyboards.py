from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu() -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру главного меню.
    
    Схема:
    [ Мои проекты ]
    [   Кто я?    ]
    [ Статус ] [ Контакты ]
    """
    builder = InlineKeyboardBuilder()
    
    # Вертикальные кнопки
    builder.row(
        InlineKeyboardButton(text="🤖 Мои проекты", callback_data="projects")
    )
    builder.row(
        InlineKeyboardButton(text="👤 Кто я?", callback_data="about")
    )
    # Горизонтальный блок
    builder.row(
        InlineKeyboardButton(text="📍 Статус", callback_data="status"),
        InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")
    )
    
    return builder.as_markup()

def projects_menu() -> InlineKeyboardMarkup:
    """Генерирует меню выбора инструментов."""
    builder = InlineKeyboardBuilder()
    
    # Список инструментов для легкого расширения
    tools = [
        ("🎬 Запустить Video2Round", "run_v2r"),
        ("🖼️ Запустить AI Upscale", "run_ai_upscale"),
        ("📚 FAQ по Video2Round", "faq_v2r"),
        ("⬅️ Назад в меню", "back"),
    ]

    for text, data in tools:
        builder.button(text=text, callback_data=data)
    
    # Форматируем в одну колонку
    builder.adjust(1)
    
    return builder.as_markup()

def back_button() -> InlineKeyboardMarkup:
    """Универсальная кнопка 'Назад'."""
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="back")
    return builder.as_markup()

def converter_menu() -> InlineKeyboardMarkup:
    """Меню действий внутри конвертера."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена / Назад", callback_data="back")
    return builder.as_markup()