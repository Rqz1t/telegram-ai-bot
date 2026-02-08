import time
from datetime import datetime, timedelta
from colorama import Fore, Style, init

# Инициализация colorama с автосбросом цвета
init(autoreset=True)

class ConsoleMonitor:
    """
    Класс для отображения статуса бота в консоли (Dashboard).
    """
    def __init__(self):
        # monotonic гарантирует, что время всегда идет вперед, даже если меняется время ОС
        self._start_time = time.monotonic()
        self.current_task = "Ожидание"
        self.last_user = "Нет данных"

    @property
    def uptime(self) -> str:
        """Возвращает время работы в формате HH:MM:SS."""
        elapsed = time.monotonic() - self._start_time
        return str(timedelta(seconds=int(elapsed)))

    def log_event(self, user_name: str, action: str) -> None:
        """Обновляет состояние и выводит лог в консоль."""
        self.last_user = user_name
        self.current_task = action
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {Fore.GREEN}OK{Style.RESET_ALL} | {user_name} -> {action}")

    def refresh_header(self) -> None:
        """
        Перерисовывает 'шапку' дашборда. 
        Примечание: для полноценного TUI лучше использовать библиотеки вроде `rich`.
        """
        # os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"{Fore.CYAN}{'='*50}")
        print(f"{Fore.GREEN}🚀 MaximusBot DASHBOARD")
        print(f"{Fore.WHITE}Время работы:   {Fore.YELLOW}{self.uptime}")
        print(f"{Fore.WHITE}Текущий процесс:{Fore.MAGENTA} {self.current_task}")
        print(f"{Fore.WHITE}Последний юзер: {Fore.BLUE}   {self.last_user}")
        print(f"{Fore.CYAN}{'='*50}\n")

# Singleton instance
monitor = ConsoleMonitor()