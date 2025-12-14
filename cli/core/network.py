"""Сетевые операции: IP, ping, автовыбор из диапазона."""

from dataclasses import dataclass
from typing import Optional
import re
import subprocess
import socket

import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from lib.logger import Logger


@dataclass
class HostNetwork:
    """Сетевые параметры хоста."""
    ip: str
    mask: str
    gateway: str
    interface: str


class Network:
    """Работа с сетью."""

    def __init__(self, logger: Logger):
        self.logger = logger

    def get_host_network(self) -> HostNetwork:
        """Получить сетевые параметры PVE хоста."""
        # Получаем default gateway и интерфейс
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True, text=True
        )
        # default via 192.168.1.1 dev vmbr0
        match = re.search(r"default via ([\d.]+) dev (\S+)", result.stdout)
        if not match:
            raise RuntimeError("Cannot determine default gateway")
        
        gateway = match.group(1)
        interface = match.group(2)
        
        # Получаем IP и маску интерфейса
        result = subprocess.run(
            ["ip", "-o", "addr", "show", interface],
            capture_output=True, text=True
        )
        # 2: vmbr0 inet 192.168.1.10/24 brd ...
        match = re.search(r"inet ([\d.]+)/(\d+)", result.stdout)
        if not match:
            raise RuntimeError(f"Cannot get IP for interface {interface}")
        
        ip = match.group(1)
        mask = match.group(2)
        
        return HostNetwork(ip=ip, mask=mask, gateway=gateway, interface=interface)

    def ping(self, ip: str, timeout: float = 1.0) -> bool:
        """Проверить доступность IP через ping."""
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(int(timeout)), ip],
            capture_output=True
        )
        return result.returncode == 0

    def resolve_ip(self, ip_arg: str) -> tuple[str, str, str]:
        """Разрешить IP аргумент.
        
        Args:
            ip_arg: "21-50" или "192.168.1.100/24"
            
        Returns:
            (ip, mask, gateway)
        """
        # Диапазон: "21-50"
        range_pattern = r"^(\d{1,3})-(\d{1,3})$"
        if match := re.match(range_pattern, ip_arg):
            start, end = int(match.group(1)), int(match.group(2))
            host = self.get_host_network()
            subnet = ".".join(host.ip.split(".")[:3])
            
            free_ip = self.find_free_ip(start, end, subnet)
            if not free_ip:
                raise RuntimeError(f"No free IP in range {ip_arg}")
            
            return (free_ip, host.mask, host.gateway)
        
        # Полный IP: "192.168.1.100/24" или "192.168.1.100"
        ip_pattern = r"^([\d.]+)(?:/(\d+))?$"
        if match := re.match(ip_pattern, ip_arg):
            ip = match.group(1)
            mask = match.group(2) or "24"
            
            # Определяем gateway из подсети
            octets = ip.split(".")
            gateway = ".".join(octets[:3]) + ".1"
            
            return (ip, mask, gateway)
        
        raise ValueError(f"Invalid IP format: {ip_arg}")

    def find_free_ip(self, start: int, end: int, subnet: str) -> Optional[str]:
        """Найти первый свободный IP в диапазоне через ping."""
        for i in range(start, end + 1):
            ip = f"{subnet}.{i}"
            if not self.ping(ip, timeout=1.0):
                return ip
        return None

    def list_free_ips(self, ip_range: str) -> list[str]:
        """Список всех свободных IP в диапазоне."""
        # Парсим диапазон
        range_pattern = r"^(?:([\d.]+)\.)?(\d{1,3})-(\d{1,3})$"
        if match := re.match(range_pattern, ip_range):
            subnet = match.group(1)
            start = int(match.group(2))
            end = int(match.group(3))
            
            if not subnet:
                host = self.get_host_network()
                subnet = ".".join(host.ip.split(".")[:3])
        else:
            raise ValueError(f"Invalid IP range: {ip_range}")
        
        free_ips = []
        for i in range(start, end + 1):
            ip = f"{subnet}.{i}"
            if not self.ping(ip, timeout=1.0):
                free_ips.append(ip)
        
        return free_ips
