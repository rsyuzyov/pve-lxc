"""Базовый класс для установщиков приложений."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
from lib.logger import Logger
from lib.system import System


@dataclass
class InstallResult:
    """Результат установки приложения."""
    success: bool
    message: str
    access_url: Optional[str] = None
    credentials: Optional[dict] = None
    log_path: Optional[Path] = None


class AppInstaller(ABC):
    """Базовый класс для установщиков приложений."""
    
    name: str = "base"
    description: str = ""
    default_cores: int = 2
    default_memory: int = 2048
    default_disk: int = 10
    parameters: list = field(default_factory=list)
    
    def __init__(self, logger: Logger, system: System, config: dict):
        self.logger = logger
        self.system = system
        self.config = config
        self._validation_error: Optional[str] = None
        self._install_log: list[str] = []
    
    def run(self) -> InstallResult:
        """Выполнить полный цикл установки."""
        self.logger.step("Validating", current=1, total=5)
        if not self.validate():
            return InstallResult(
                success=False,
                message=f"Validation failed: {self._validation_error}",
                log_path=self._save_log()
            )
        
        try:
            self.logger.step("Pre-install", current=2, total=5)
            self.pre_install()
            
            self.logger.step("Installing", current=3, total=5)
            self.install()
            
            self.logger.step("Post-install", current=4, total=5)
            self.post_install()
            
            self.logger.step("Configuring", current=5, total=5)
            self.configure()
            
            return self.get_result()
        except Exception as e:
            self.logger.error(f"Installation failed: {e}")
            return InstallResult(
                success=False,
                message=str(e),
                log_path=self._save_log()
            )

    @abstractmethod
    def validate(self) -> bool:
        """Валидация параметров. Вернуть False и установить _validation_error при ошибке."""
        pass
    
    def pre_install(self) -> None:
        """Подготовка к установке (опционально)."""
        pass
    
    @abstractmethod
    def install(self) -> None:
        """Основная установка."""
        pass
    
    def post_install(self) -> None:
        """Пост-обработка (опционально)."""
        pass
    
    def configure(self) -> None:
        """Конфигурация (опционально)."""
        pass
    
    @abstractmethod
    def get_result(self) -> InstallResult:
        """Получить результат установки."""
        pass
    
    def _save_log(self) -> Path:
        """Сохранить лог установки."""
        log_dir = Path("/var/log/pve-lxc")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_path = log_dir / f"{self.name}-install.log"
        log_path.write_text("\n".join(self._install_log))
        return log_path
    
    def log(self, message: str) -> None:
        """Добавить сообщение в лог."""
        self._install_log.append(message)
        self.logger.info(message)
