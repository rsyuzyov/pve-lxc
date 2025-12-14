"""GPU passthrough для LXC контейнеров."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os
import stat

import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from lib.logger import Logger


@dataclass
class GPUDevice:
    """GPU устройство."""
    path: str      # /dev/dri/renderD128
    major: int
    minor: int


class GPU:
    """Работа с GPU passthrough."""

    def __init__(self, logger: Logger):
        self.logger = logger

    def detect_devices(self) -> list[GPUDevice]:
        """Найти GPU устройства на хосте."""
        devices = []
        dri_path = Path("/dev/dri")
        
        if not dri_path.exists():
            self.logger.warn("No /dev/dri directory found")
            return devices
        
        for device in dri_path.iterdir():
            if device.name.startswith("render") or device.name.startswith("card"):
                try:
                    st = os.stat(device)
                    major = os.major(st.st_rdev)
                    minor = os.minor(st.st_rdev)
                    devices.append(GPUDevice(
                        path=str(device),
                        major=major,
                        minor=minor
                    ))
                    self.logger.info(f"Found GPU device: {device} ({major}:{minor})")
                except Exception as e:
                    self.logger.warn(f"Cannot stat {device}: {e}")
        
        return devices

    def configure_passthrough(self, ctid: int, devices: list[GPUDevice]) -> bool:
        """Настроить passthrough в конфиге контейнера."""
        if not devices:
            self.logger.warn("No GPU devices to configure")
            return False
        
        config_path = Path(f"/etc/pve/lxc/{ctid}.conf")
        if not config_path.exists():
            self.logger.error(f"Container config not found: {config_path}")
            return False
        
        self.logger.step(f"Configuring GPU passthrough for container {ctid}")
        
        # Читаем текущий конфиг
        config = config_path.read_text()
        
        # Добавляем устройства
        lines = []
        for i, device in enumerate(devices):
            lines.append(f"lxc.cgroup2.devices.allow: c {device.major}:{device.minor} rwm")
            lines.append(f"lxc.mount.entry: {device.path} dev/dri/{Path(device.path).name} none bind,optional,create=file")
        
        # Добавляем в конфиг
        with open(config_path, "a") as f:
            f.write("\n# GPU Passthrough\n")
            for line in lines:
                f.write(line + "\n")
        
        self.logger.success(f"GPU passthrough configured: {len(devices)} devices")
        return True
