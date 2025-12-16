"""Управление PVE хостами."""

from pathlib import Path
from typing import Optional
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.core.ssh_config import SSHConfigParser
from cli.core.executor import CommandExecutor, LocalExecutor, SSHExecutor
from lib.config import ConfigLoader
from lib.exceptions import HostNotFoundError


class HostManager:
    """Управление PVE хостами."""
    
    def __init__(
        self, 
        ssh_config: SSHConfigParser = None,
        config_path: Path = None
    ):
        self.ssh_config = ssh_config or SSHConfigParser()
        self.config_path = config_path or Path.home() / ".pve-lxc" / "config.yaml"
    
    def add(
        self, 
        name: str, 
        hostname: str, 
        user: str = "root", 
        port: int = 22,
        key: str = None
    ) -> None:
        """Добавить хост."""
        self.ssh_config.add_host(
            name=name,
            hostname=hostname,
            user=user,
            port=port,
            identity_file=key
        )
    
    def remove(self, name: str) -> bool:
        """Удалить хост."""
        # Если это default host, сбрасываем
        if self.get_default() == name:
            self._save_default(None)
        return self.ssh_config.remove_host(name)
    
    def list(self) -> list[dict]:
        """Список хостов."""
        return self.ssh_config.list_hosts()
    
    def get(self, name: str) -> Optional[dict]:
        """Получить хост по имени."""
        return self.ssh_config.get_host(name)
    
    def test(self, name: str) -> dict:
        """Проверить подключение и PVE."""
        result = {
            "name": name,
            "connected": False,
            "pve_version": None,
            "error": None
        }
        
        try:
            executor = self.get_executor(name)
            
            # Проверяем подключение
            pve_result = executor.run(["pveversion"])
            
            if pve_result.success:
                result["connected"] = True
                result["pve_version"] = pve_result.stdout.strip()
            else:
                result["error"] = "PVE tools not found"
            
            executor.close()
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def get_executor(self, name: str = None) -> CommandExecutor:
        """Получить executor для хоста."""
        # Если имя не указано, используем default
        if not name:
            name = self.get_default()
        
        # Если всё ещё нет имени, используем локальный executor
        if not name:
            return LocalExecutor()
        
        # Получаем конфигурацию хоста
        host_config = self.ssh_config.get_host(name)
        if not host_config:
            available = [h["name"] for h in self.list()]
            raise HostNotFoundError(name, available)
        
        return SSHExecutor(
            host=host_config.get("hostname", name),
            user=host_config.get("user", "root"),
            port=int(host_config.get("port", 22)),
            key_path=Path(host_config["identityfile"]) if host_config.get("identityfile") else None
        )
    
    def set_default(self, name: str) -> None:
        """Установить хост по умолчанию."""
        # Проверяем что хост существует
        if not self.ssh_config.get_host(name):
            available = [h["name"] for h in self.list()]
            raise HostNotFoundError(name, available)
        
        self._save_default(name)
    
    def get_default(self) -> Optional[str]:
        """Получить хост по умолчанию."""
        config = self._load_config()
        return config.get("default_host")
    
    def _load_config(self) -> dict:
        """Загрузить конфигурацию pve-lxc."""
        if not self.config_path.exists():
            return {}
        
        try:
            with open(self.config_path) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}
    
    def _save_default(self, name: Optional[str]) -> None:
        """Сохранить default_host в конфиг."""
        config = self._load_config()
        
        if name:
            config["default_host"] = name
        elif "default_host" in config:
            del config["default_host"]
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
