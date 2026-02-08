import sqlite3
import logging
from contextlib import contextmanager
from typing import Generator, Tuple, Optional

from .config import DB_PATH

logger = logging.getLogger(__name__)

@contextmanager
def db_connection() -> Generator[sqlite3.Cursor, None, None]:
    """
    Контекстный менеджер для безопасной работы с SQLite.
    Автоматически делает commit при успехе и rollback при ошибке.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Ошибка базы данных: {e}")
        raise
    finally:
        conn.close()

def init_db() -> None:
    """Инициализирует структуру БД и дефолтные значения."""
    schema = """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS stats (
            user_id INTEGER,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        INSERT OR IGNORE INTO settings (key, value) VALUES ('status', 'Работаю над проектами 🚀');
    """
    with db_connection() as cursor:
        cursor.executescript(schema)

def get_status() -> str:
    """Возвращает текущий статус бота."""
    with db_connection() as cursor:
        cursor.execute("SELECT value FROM settings WHERE key = 'status'")
        result = cursor.fetchone()
    return result[0] if result else "Работаю над проектами 🚀"

def set_status(new_status: str) -> None:
    """Обновляет статус бота."""
    with db_connection() as cursor:
        cursor.execute("UPDATE settings SET value = ? WHERE key = 'status'", (new_status,))

def log_action(user_id: int, action: str) -> None:
    """Логирует действие пользователя в статистику."""
    with db_connection() as cursor:
        cursor.execute("INSERT INTO stats (user_id, action) VALUES (?, ?)", (user_id, action))

def get_stats() -> Tuple[int, int, int]:
    """
    Возвращает статистику:
    (всего пользователей, кол-во конвертаций, кол-во апскейлов)
    """
    with db_connection() as cursor:
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM stats")
        users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stats WHERE action = 'conversion'")
        conversions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stats WHERE action = 'ai_upscale'")
        upscales = cursor.fetchone()[0]
        
    return users, conversions, upscales