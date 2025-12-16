# Design Document: Cross-Platform Support

## Overview

Добавление модуля определения платформы и адаптация существующего кода для корректной работы на Windows, Linux и macOS. Основной принцип — явные проверки OS_TYPE вместо try/except обёрток.

## Architecture

```
lib/
├── platform.py      # NEW: Определение ОС, OSType enum, OS_TYPE
├── system.py        # MODIFY: Использовать OS_TYPE для chmod
└── ...

cli/core/
├── ssh_config.py    # MODIFY: Использовать OS_TYPE для chmod
├── pve.py           # MODIFY: Заменить rsplit("/") на Path
├── container.py     # MODIFY: Заменить rsplit("/") на Path
└── ...
```

## Components and Interfaces

### lib/platform.py (новый модуль)

```python
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
```

### Изменения в существующих модулях

**lib/system.py** — метод `write_file`:
```python
from lib.platform import OS_TYPE, OSType

def write_file(self, path: Path, content: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    if OS_TYPE != OSType.WINDOWS:
        path.chmod(mode)
```

**cli/core/ssh_config.py** — метод `_write_config`:
```python
from lib.platform import OS_TYPE, OSType

def _write_config(self, content: str) -> None:
    self.config_path.parent.mkdir(parents=True, exist_ok=True)
    self.config_path.write_text(content)
    if OS_TYPE != OSType.WINDOWS:
        self.config_path.chmod(0o600)
```

**cli/core/pve.py** и **cli/core/container.py** — замена:
```python
# Было:
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])

# Стало:
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

## Data Models

### OSType Enum

| Value | Description |
|-------|-------------|
| WINDOWS | Windows (win32) |
| LINUX | Linux и другие Unix-like |
| MACOS | macOS (darwin) |

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

После анализа prework:
- Свойства 1.1 и 1.2 можно объединить в одно свойство о валидности OS_TYPE
- Свойства 2.1 и 2.2 — примеры, не свойства (зависят от конкретной платформы)
- Свойства 3.x — требования к коду, не тестируемые свойствами

### Properties

**Property 1: OS_TYPE is always valid**
*For any* import of lib.platform, OS_TYPE SHALL be a valid member of OSType enum (WINDOWS, LINUX, or MACOS)
**Validates: Requirements 1.1, 1.2**

## Error Handling

- Неизвестная платформа → fallback на LINUX (большинство Unix-like систем совместимы)
- chmod на Windows просто пропускается, ошибки не генерируются

## Testing Strategy

### Unit Tests
- Проверка что OS_TYPE корректно определяется на текущей платформе
- Проверка что _detect_os() возвращает правильный тип для известных sys.platform значений

### Property-Based Tests
- Библиотека: hypothesis (уже в requirements.txt)
- Минимум 100 итераций
- Формат комментария: `**Feature: cross-platform, Property {number}: {property_text}**`

**Property 1**: Генерируем случайные значения sys.platform, проверяем что _detect_os() всегда возвращает валидный OSType
