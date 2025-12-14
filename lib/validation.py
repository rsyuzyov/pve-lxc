"""Валидация параметров CLI."""

import re
from typing import Optional


class ValidationError(Exception):
    """Ошибка валидации параметра."""
    pass


def validate_ctid(ctid: int) -> int:
    """Валидация CTID контейнера (100-999999999)."""
    if not isinstance(ctid, int) or ctid < 100 or ctid > 999999999:
        raise ValidationError(f"CTID must be integer between 100 and 999999999, got: {ctid}")
    return ctid


def validate_ip(ip: str) -> str:
    """Валидация IP адреса или диапазона.
    
    Форматы:
    - "21-50" — диапазон последних октетов
    - "192.168.1.100" — полный IP
    - "192.168.1.100/24" — IP с маской
    """
    # Диапазон: "21-50"
    range_pattern = r"^(\d{1,3})-(\d{1,3})$"
    if match := re.match(range_pattern, ip):
        start, end = int(match.group(1)), int(match.group(2))
        if not (1 <= start <= 254 and 1 <= end <= 254):
            raise ValidationError(f"IP range octets must be 1-254, got: {ip}")
        if start > end:
            raise ValidationError(f"IP range start must be <= end, got: {ip}")
        return ip
    
    # Полный IP с опциональной маской: "192.168.1.100" или "192.168.1.100/24"
    ip_pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})(/\d{1,2})?$"
    if match := re.match(ip_pattern, ip):
        octets = [int(match.group(i)) for i in range(1, 5)]
        if not all(0 <= o <= 255 for o in octets):
            raise ValidationError(f"IP octets must be 0-255, got: {ip}")
        return ip
    
    raise ValidationError(f"Invalid IP format: {ip}. Use '21-50' or '192.168.1.100/24'")


def validate_name(name: str) -> str:
    """Валидация имени контейнера.
    
    Правила:
    - Только буквы, цифры, дефис
    - Начинается с буквы
    - Длина 1-63 символа
    """
    if not name:
        raise ValidationError("Container name cannot be empty")
    
    if len(name) > 63:
        raise ValidationError(f"Container name too long (max 63): {name}")
    
    pattern = r"^[a-zA-Z][a-zA-Z0-9-]*$"
    if not re.match(pattern, name):
        raise ValidationError(
            f"Invalid container name: {name}. "
            "Must start with letter, contain only letters, digits, hyphens"
        )
    return name


def validate_resources(
    cores: Optional[int] = None,
    memory: Optional[int] = None,
    disk: Optional[int] = None
) -> dict:
    """Валидация ресурсов контейнера."""
    result = {}
    
    if cores is not None:
        if not isinstance(cores, int) or cores < 1 or cores > 128:
            raise ValidationError(f"Cores must be 1-128, got: {cores}")
        result["cores"] = cores
    
    if memory is not None:
        if not isinstance(memory, int) or memory < 128 or memory > 1048576:
            raise ValidationError(f"Memory must be 128-1048576 MB, got: {memory}")
        result["memory"] = memory
    
    if disk is not None:
        if not isinstance(disk, int) or disk < 1 or disk > 10240:
            raise ValidationError(f"Disk must be 1-10240 GB, got: {disk}")
        result["disk"] = disk
    
    return result
