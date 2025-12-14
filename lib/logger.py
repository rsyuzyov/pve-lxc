"""Структурированное логирование для pve-lxc."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
import json
import sys


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class Logger:
    """Логгер с поддержкой цветного и JSON вывода."""

    COLORS = {
        LogLevel.DEBUG: "\033[0;37m",    # Gray
        LogLevel.INFO: "\033[0;34m",     # Blue
        LogLevel.WARN: "\033[1;33m",     # Yellow
        LogLevel.ERROR: "\033[0;31m",    # Red
        LogLevel.SUCCESS: "\033[0;32m",  # Green
    }
    NC = "\033[0m"

    def __init__(self, json_output: bool = False):
        self.json_output = json_output
        self.context: dict[str, Any] = {}

    def set_context(self, **kwargs) -> None:
        """Добавить контекст ко всем последующим логам."""
        self.context.update(kwargs)

    def clear_context(self) -> None:
        """Очистить контекст."""
        self.context.clear()

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _log(self, level: LogLevel, message: str, **kwargs) -> None:
        data = {
            "level": level.value,
            "message": message,
            "timestamp": self._timestamp(),
        }
        if self.context:
            data["context"] = self.context.copy()
        if kwargs:
            data.update(kwargs)

        if self.json_output:
            print(json.dumps(data), file=sys.stderr if level == LogLevel.ERROR else sys.stdout)
        else:
            color = self.COLORS.get(level, "")
            print(f"{color}[{level.value}]{self.NC} {message}", file=sys.stderr if level == LogLevel.ERROR else sys.stdout)

    def debug(self, message: str, **kwargs) -> None:
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        self._log(LogLevel.INFO, message, **kwargs)

    def warn(self, message: str, **kwargs) -> None:
        self._log(LogLevel.WARN, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        self._log(LogLevel.ERROR, message, **kwargs)

    def success(self, message: str, **kwargs) -> None:
        self._log(LogLevel.SUCCESS, message, **kwargs)

    def step(self, message: str, current: int = None, total: int = None) -> None:
        """Вывод шага с опциональным прогрессом."""
        if current is not None and total is not None:
            progress = f"[{current}/{total}] "
            if self.json_output:
                self._log(LogLevel.INFO, message, current=current, total=total)
            else:
                print(f"\033[0;32m[STEP]{self.NC} {progress}{message}")
        else:
            self._log(LogLevel.INFO, message)

    def result(self, success: bool, data: dict = None) -> None:
        """Финальный результат команды."""
        result_data = {
            "level": "SUCCESS" if success else "ERROR",
            "message": "Command completed" if success else "Command failed",
            "timestamp": self._timestamp(),
            "success": success,
        }
        if not success:
            result_data["error_code"] = 1
        if data:
            result_data.update(data)
        if self.context:
            result_data["context"] = self.context.copy()

        if self.json_output:
            print(json.dumps(result_data))
        else:
            status = "SUCCESS" if success else "FAILED"
            color = self.COLORS[LogLevel.SUCCESS] if success else self.COLORS[LogLevel.ERROR]
            print(f"{color}[{status}]{self.NC} {result_data['message']}")
