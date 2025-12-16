"""Системные операции: выполнение команд, apt, systemctl, файлы."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import subprocess

from .logger import Logger


@dataclass
class CommandResult:
    """Результат выполнения команды."""
    returncode: int
    stdout: str
    stderr: str
    
    @property
    def success(self) -> bool:
        return self.returncode == 0


class System:
    """Обёртка над системными операциями."""

    def __init__(self, logger: Logger):
        self.logger = logger

    def run(self, cmd: list[str], check: bool = True, capture: bool = True) -> CommandResult:
        """Выполнить команду."""
        self.logger.debug(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture,
                text=True,
                check=False
            )
            cmd_result = CommandResult(
                returncode=result.returncode,
                stdout=result.stdout or "",
                stderr=result.stderr or ""
            )
            
            if check and not cmd_result.success:
                self.logger.error(f"Command failed: {' '.join(cmd)}", stderr=cmd_result.stderr)
            
            return cmd_result
        except Exception as e:
            self.logger.error(f"Command error: {e}")
            return CommandResult(returncode=1, stdout="", stderr=str(e))

    def apt_update(self) -> CommandResult:
        """Обновить списки пакетов."""
        self.logger.step("Updating package lists")
        return self.run(["apt-get", "update", "-qq"])

    def apt_install(self, packages: list[str]) -> CommandResult:
        """Установить пакеты."""
        self.logger.step(f"Installing packages: {', '.join(packages)}")
        cmd = ["apt-get", "install", "-y", "-qq"] + packages
        return self.run(cmd)

    def systemctl(self, action: str, service: str) -> CommandResult:
        """Управление systemd сервисом."""
        self.logger.step(f"Systemctl {action} {service}")
        return self.run(["systemctl", action, service])

    def write_file(self, path: Path, content: str, mode: int = 0o644) -> None:
        """Записать файл."""
        self.logger.debug(f"Writing file: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        path.chmod(mode)

    def read_file(self, path: Path) -> str:
        """Прочитать файл."""
        return path.read_text()

    def file_exists(self, path: Path) -> bool:
        """Проверить существование файла."""
        return path.exists()

    def mkdir(self, path: Path, mode: int = 0o755) -> None:
        """Создать директорию."""
        path.mkdir(parents=True, exist_ok=True)
        path.chmod(mode)
