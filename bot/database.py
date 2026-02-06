import sqlite3
from .config import DB_PATH

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            user_id INTEGER,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('status', 'Работаю над проектами 🚀')")
    conn.commit()
    conn.close()

def get_status() -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'status'")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Работаю над проектами 🚀"  # Возврат дефолтного значения, если нет записи

def set_status(new_status: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = 'status'", (new_status,))
    conn.commit()
    conn.close()

def log_action(user_id: int, action: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stats (user_id, action) VALUES (?, ?)", (user_id, action))
    conn.commit()
    conn.close()

def get_stats() -> tuple[int, int, int]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM stats")
    users: int = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM stats WHERE action = 'conversion'")
    conversions: int = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM stats WHERE action = 'ai_upscale'")
    upscales: int = cursor.fetchone()[0]
    conn.close()
    return users, conversions, upscales  # Единственная версия с поддержкой AI Upscale