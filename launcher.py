import customtkinter as ctk
import sys
import threading
import asyncio
import logging
from datetime import datetime

# Импортируем твоего бота
from bot.main import main
from bot.config import LOG_PATH

# Настройка внешнего вида (Темная тема, как в играх)
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class TextRedirector(object):
    """Класс, который перехватывает print и отправляет его в виджет окна"""
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal")
        # Добавляем время к каждой строке, если это не просто перенос строки
        if str.strip():
            timestamp = datetime.now().strftime("[%H:%M:%S] ")
            self.widget.insert("end", timestamp + str + "\n", self.tag)
        self.widget.see("end") # Автопрокрутка вниз
        self.widget.configure(state="disabled")

    def flush(self):
        pass

class BotLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Настройка окна
        self.title("MaximusBot Launcher")
        self.geometry("700x500")
        self.resizable(False, False)

        # 2. Заголовок
        self.header = ctk.CTkLabel(self, text="🚀 MAXIMUS BOT CONTROL", font=("Roboto Medium", 20))
        self.header.pack(pady=10)

        # 3. Консоль (Текстовое поле)
        self.console_frame = ctk.CTkFrame(self)
        self.console_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.console = ctk.CTkTextbox(
            self.console_frame, 
            font=("Consolas", 12), 
            text_color="#00FF00", # Зеленый текст хакера
            fg_color="black"      # Черный фон
        )
        self.console.pack(fill="both", expand=True, padx=5, pady=5)
        self.console.insert("0.0", "System initialized...\nWaiting for start...\n")
        self.console.configure(state="disabled")

        # 4. Кнопки управления
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=20)

        self.start_btn = ctk.CTkButton(self.btn_frame, text="ЗАПУСТИТЬ БОТА", command=self.start_bot_thread, width=200, height=40)
        self.start_btn.pack(side="left", padx=10)

        self.stop_btn = ctk.CTkButton(self.btn_frame, text="ВЫХОД", command=self.on_close, width=100, height=40, fg_color="#550000", hover_color="#880000")
        self.stop_btn.pack(side="left", padx=10)

        # Перенаправление потоков
        sys.stdout = TextRedirector(self.console, "stdout")
        sys.stderr = TextRedirector(self.console, "stderr")
        
        # Настройка логгера, чтобы он тоже писал сюда
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    def start_bot_thread(self):
        self.start_btn.configure(state="disabled", text="БОТ РАБОТАЕТ...")
        print("Запуск ядра бота...")
        
        # Запускаем бота в отдельном потоке, чтобы окно не зависло
        thread = threading.Thread(target=self.run_async_bot, daemon=True)
        thread.start()

    def run_async_bot(self):
        # Создаем новый цикл событий для потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(main())
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")

    def on_close(self):
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = BotLauncher()
    app.mainloop()