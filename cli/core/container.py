"""Высокоуровневые операции с контейнерами."""

from dataclasses import dataclass
from typing import Optional

import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from lib.logger import Logger
from lib.config import ConfigLoader
from .pve import PVE, Container
from .network import Network


@dataclass
class CreateResult:
    """Результат создания контейнера."""
    success: bool
    ctid: Optional[int] = None
    ip: Optional[str] = None
    message: str = ""


def create_container(
    logger: Logger,
    name: str,
    cores: int = None,
    memory: int = None,
    disk: int = None,
    ip: str = None,
    gateway: str = None,
    template: str = None,
    storage: str = None,
    gpu: bool = False
) -> CreateResult:
    """Создать контейнер с автоматическим выбором параметров."""
    
    # Загружаем конфигурацию
    config = ConfigLoader().load_user_config().merge()
    defaults = config.get("container", {})
    
    # Применяем дефолты
    cores = cores or defaults.get("cores", 2)
    memory = memory or defaults.get("memory", 2048)
    disk = disk or defaults.get("disk", 10)
    template = template or defaults.get("template", "debian-12-standard")
    storage = storage or defaults.get("storage", "local-lvm")
    
    pve = PVE(logger)
    network = Network(logger)
    
    # Получаем CTID
    ctid = pve.next_ctid()
    
    # Разрешаем IP
    if ip:
        resolved_ip, mask, gw = network.resolve_ip(ip)
        net_ip = f"{resolved_ip}/{mask}"
        gateway = gateway or gw
    else:
        net_ip = "dhcp"
        resolved_ip = None

    # Формируем путь к шаблону
    template_path = f"local:vztmpl/{template}_amd64.tar.zst"
    
    # Создаём контейнер
    success = pve.create(
        ctid=ctid,
        template=template_path,
        hostname=name,
        storage=storage,
        rootfs_size=disk,
        cores=cores,
        memory=memory,
        net_ip=net_ip,
        net_gw=gateway
    )
    
    if not success:
        return CreateResult(success=False, message="Failed to create container")
    
    # GPU passthrough
    if gpu:
        from .gpu import GPU
        gpu_handler = GPU(logger)
        devices = gpu_handler.detect_devices()
        if devices:
            gpu_handler.configure_passthrough(ctid, devices)
    
    return CreateResult(
        success=True,
        ctid=ctid,
        ip=resolved_ip,
        message=f"Container {ctid} created"
    )


def destroy_container(logger: Logger, ctid: int, force: bool = False) -> bool:
    """Удалить контейнер."""
    pve = PVE(logger)
    return pve.destroy(ctid, force=force)


def bootstrap_container(logger: Logger, ctid: int) -> bool:
    """Выполнить базовую настройку контейнера."""
    config = ConfigLoader().load_user_config().merge()
    bootstrap_config = config.get("bootstrap", {})
    
    pve = PVE(logger)
    
    # Настройка locale
    locale = bootstrap_config.get("locale", "en_US.UTF-8")
    logger.step("Setting locale", current=1, total=4)
    pve.exec(ctid, ["locale-gen", locale])
    pve.exec(ctid, ["update-locale", f"LANG={locale}"])
    
    # Настройка timezone
    timezone = bootstrap_config.get("timezone", "UTC")
    logger.step("Setting timezone", current=2, total=4)
    pve.exec(ctid, ["ln", "-sf", f"/usr/share/zoneinfo/{timezone}", "/etc/localtime"])
    
    # Обновление пакетов
    logger.step("Updating packages", current=3, total=4)
    pve.exec(ctid, ["apt-get", "update", "-qq"])
    
    # Установка базовых пакетов
    packages = bootstrap_config.get("packages", ["curl", "wget", "git", "vim", "htop"])
    logger.step(f"Installing packages: {', '.join(packages)}", current=4, total=4)
    pve.exec(ctid, ["apt-get", "install", "-y", "-qq"] + packages)
    
    logger.success("Bootstrap completed")
    return True
