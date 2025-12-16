"""Парсер и редактор SSH config (~/.ssh/config)."""

from pathlib import Path
from typing import Optional
import re


class SSHConfigError(Exception):
    """Ошибка работы с SSH config."""
    pass


class SSHConfigParser:
    """Парсер и редактор SSH config."""
    
    def __init__(self, config_path: Path = None):
        self.config_path = config_path or Path.home() / ".ssh" / "config"
    
    def _read_config(self) -> str:
        """Прочитать SSH config."""
        if not self.config_path.exists():
            return ""
        return self.config_path.read_text()
    
    def _write_config(self, content: str) -> None:
        """Записать SSH config."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(content)
        self.config_path.chmod(0o600)
    
    def _parse_hosts(self, content: str) -> list[dict]:
        """Распарсить SSH config в список хостов."""
        hosts = []
        current_host = None
        
        for line in content.split("\n"):
            line = line.strip()
            
            # Пропускаем пустые строки и комментарии
            if not line or line.startswith("#"):
                continue
            
            # Разбираем ключ-значение
            match = re.match(r"^(\w+)\s+(.+)$", line, re.IGNORECASE)
            if not match:
                continue
            
            key = match.group(1).lower()
            value = match.group(2).strip()
            
            if key == "host":
                # Новый хост
                if current_host:
                    hosts.append(current_host)
                current_host = {"name": value}
            elif current_host:
                # Параметр текущего хоста
                current_host[key] = value
        
        # Добавляем последний хост
        if current_host:
            hosts.append(current_host)
        
        return hosts
    
    def list_hosts(self) -> list[dict]:
        """Получить список хостов из SSH config."""
        content = self._read_config()
        return self._parse_hosts(content)
    
    def get_host(self, name: str) -> Optional[dict]:
        """Получить параметры хоста по имени."""
        for host in self.list_hosts():
            if host.get("name") == name:
                return host
        return None
    
    def add_host(
        self, 
        name: str, 
        hostname: str, 
        user: str = "root", 
        port: int = 22,
        identity_file: str = None
    ) -> None:
        """Добавить хост в SSH config."""
        # Проверяем что хост не существует
        if self.get_host(name):
            raise SSHConfigError(f"Host '{name}' already exists")
        
        # Формируем блок хоста
        lines = [
            f"\nHost {name}",
            f"    HostName {hostname}",
            f"    User {user}",
            f"    Port {port}",
        ]
        
        if identity_file:
            lines.append(f"    IdentityFile {identity_file}")
        
        lines.append("")  # Пустая строка в конце
        
        # Добавляем в конец файла
        content = self._read_config()
        content += "\n".join(lines)
        self._write_config(content)
    
    def remove_host(self, name: str) -> bool:
        """Удалить хост из SSH config."""
        content = self._read_config()
        lines = content.split("\n")
        
        new_lines = []
        skip_until_next_host = False
        found = False
        
        for line in lines:
            stripped = line.strip().lower()
            
            # Проверяем начало блока Host
            if stripped.startswith("host "):
                host_name = line.strip()[5:].strip()
                if host_name == name:
                    skip_until_next_host = True
                    found = True
                    continue
                else:
                    skip_until_next_host = False
            
            if not skip_until_next_host:
                new_lines.append(line)
        
        if found:
            # Убираем лишние пустые строки в конце
            while new_lines and not new_lines[-1].strip():
                new_lines.pop()
            new_lines.append("")  # Одна пустая строка в конце
            
            self._write_config("\n".join(new_lines))
        
        return found
