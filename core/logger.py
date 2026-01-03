import sys
from datetime import datetime
from rich.console import Console

console = Console()

class Logger:
    @staticmethod
    def _timestamp():
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def info(msg):
        console.print(f"[dim]{Logger._timestamp()}[/] [bold green]INFO[/]  {msg}")

    @staticmethod
    def debug(msg):
        # 如果不想看太細，可以註解掉這行
        console.print(f"[dim]{Logger._timestamp()}[/] [cyan]DEBUG[/] {msg}")

    @staticmethod
    def warn(msg):
        console.print(f"[dim]{Logger._timestamp()}[/] [bold yellow]WARN[/]  {msg}")

    @staticmethod
    def error(msg):
        console.print(f"[dim]{Logger._timestamp()}[/] [bold red]ERROR[/] {msg}")

    @staticmethod
    def success(msg):
        console.print(f"[dim]{Logger._timestamp()}[/] [bold green]SUCCESS[/] {msg}")