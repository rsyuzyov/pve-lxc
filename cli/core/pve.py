"""Обёртка над Proxmox VE командами: pct, pvesm, pveam."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import re
import subprocess

import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from lib.logger import Logger
from lib.system import CommandResult


@dataclass
class Container:
    """Информация о контейнере."""
    ctid: int
    name: str
    status: str  # running, stopped
    ip: Optional[str]
    cores: int
    memory: int
    disk: int


class PVE:
    """Работа с Proxmox VE."""

    def __init__(self, logger: Logger):
        self.logger = logger

    def _run(self, cmd: list[str], check: bool = True) -> CommandResult:
        """Выполнить команду."""
        self.logger.debug(f"PVE: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        return CommandResult(
            returncode=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or ""
        )

    def create(
        self,
        ctid: int,
        template: str,
        hostname: str,
        storage: str = "local-lvm",
        rootfs_size: int = 10,
        cores: int = 2,
        memory: int = 2048,
        net_bridge: str = "vmbr0",
        net_ip: str = "dhcp",
        net_gw: str = None,
        **kwargs
    ) -> bool:
        """Создать контейнер."""
        self.logger.step(f"Creating container {ctid}")

        # Формируем net0
        if net_ip == "dhcp":
            net0 = f"name=eth0,bridge={net_bridge},ip=dhcp"
        else:
            net0 = f"name=eth0,bridge={net_bridge},ip={net_ip}"
            if net_gw:
                net0 += f",gw={net_gw}"

        cmd = [
            "pct", "create", str(ctid), template,
            "--hostname", hostname,
            "--storage", storage,
            "--rootfs", f"{storage}:{rootfs_size}",
            "--cores", str(cores),
            "--memory", str(memory),
            "--net0", net0,
            "--unprivileged", "1",
            "--features", "nesting=1",
            "--start", "1"
        ]
        
        result = self._run(cmd)
        if not result.success:
            self.logger.error(f"Failed to create container: {result.stderr}")
        return result.success

    def destroy(self, ctid: int, force: bool = False) -> bool:
        """Удалить контейнер."""
        self.logger.step(f"Destroying container {ctid}")
        
        # Сначала останавливаем если запущен
        container = self.get_container(ctid)
        if container and container.status == "running":
            if not force:
                return False  # Требуется подтверждение
            self.stop(ctid)
        
        cmd = ["pct", "destroy", str(ctid), "--purge"]
        result = self._run(cmd)
        return result.success

    def start(self, ctid: int) -> bool:
        """Запустить контейнер."""
        result = self._run(["pct", "start", str(ctid)])
        return result.success

    def stop(self, ctid: int) -> bool:
        """Остановить контейнер."""
        result = self._run(["pct", "stop", str(ctid)])
        return result.success

    def exec(self, ctid: int, cmd: list[str]) -> CommandResult:
        """Выполнить команду в контейнере."""
        full_cmd = ["pct", "exec", str(ctid), "--"] + cmd
        return self._run(full_cmd, check=False)

    def push(self, ctid: int, src: Path, dst: Path) -> bool:
        """Скопировать файл в контейнер."""
        result = self._run(["pct", "push", str(ctid), str(src), str(dst)])
        return result.success

    def list_containers(self) -> list[Container]:
        """Получить список контейнеров."""
        result = self._run(["pct", "list"])
        if not result.success:
            return []
        
        containers = []
        for line in result.stdout.strip().split("\n")[1:]:  # Skip header
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 3:
                ctid = int(parts[0])
                status = parts[1]
                name = parts[2] if len(parts) > 2 else ""
                
                # Получаем детали контейнера
                config = self._get_config(ctid)
                containers.append(Container(
                    ctid=ctid,
                    name=name,
                    status=status,
                    ip=config.get("ip"),
                    cores=config.get("cores", 1),
                    memory=config.get("memory", 512),
                    disk=config.get("disk", 8)
                ))
        
        return containers

    def get_container(self, ctid: int) -> Optional[Container]:
        """Получить информацию о контейнере."""
        for c in self.list_containers():
            if c.ctid == ctid:
                return c
        return None

    def _get_config(self, ctid: int) -> dict:
        """Получить конфигурацию контейнера."""
        result = self._run(["pct", "config", str(ctid)])
        if not result.success:
            return {}
        
        config = {}
        for line in result.stdout.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                
                if key == "cores":
                    config["cores"] = int(value)
                elif key == "memory":
                    config["memory"] = int(value)
                elif key == "net0":
                    # Парсим IP из net0
                    if match := re.search(r"ip=([\d./]+)", value):
                        config["ip"] = match.group(1).split("/")[0]
        
        return config

    def next_ctid(self) -> int:
        """Получить следующий свободный CTID."""
        result = self._run(["pvesh", "get", "/cluster/nextid"])
        if result.success:
            return int(result.stdout.strip())
        
        # Fallback: найти максимальный CTID + 1
        containers = self.list_containers()
        if containers:
            return max(c.ctid for c in containers) + 1
        return 100

    def list_templates(self, storage: str = "local") -> list[str]:
        """Список доступных шаблонов."""
        result = self._run(["pveam", "list", storage])
        if not result.success:
            return []
        
        templates = []
        for line in result.stdout.strip().split("\n")[1:]:
            if line.strip():
                parts = line.split()
                if parts:
                    templates.append(parts[0])
        return templates

    def download_template(self, template: str, storage: str = "local") -> bool:
        """Скачать шаблон."""
        self.logger.step(f"Downloading template {template}")
        result = self._run(["pveam", "download", storage, template])
        return result.success
