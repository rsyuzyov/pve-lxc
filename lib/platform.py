"""Определение платформы."""

import sys
from enum import Enum


class OSType(Enum):
    """Тип операционной системы."""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"


def _detect_os() -> OSType:
    """Определить текущую ОС."""
    if sys.platform == 'win32':
        return OSType.WINDOWS
    elif sys.platform == 'darwin':
        return OSType.MACOS
    return OSType.LINUX  # default для Linux и других Unix-like


OS_TYPE = _detect_os()
