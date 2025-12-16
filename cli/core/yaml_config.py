"""Загрузка параметров команд из YAML файлов."""

from pathlib import Path
from typing import Any, Optional
import yaml


def load_yaml_config(config_path: Optional[str]) -> dict[str, Any]:
    """Загрузить конфигурацию из YAML файла.
    
    Args:
        config_path: Путь к YAML файлу или None
        
    Returns:
        Словарь с параметрами или пустой словарь
    """
    if not config_path:
        return {}
    
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    return data if data else {}


def merge_config(yaml_config: dict[str, Any], **cli_args) -> dict[str, Any]:
    """Объединить yaml конфиг с аргументами CLI.
    
    CLI аргументы имеют приоритет над yaml.
    None значения из CLI игнорируются.
    
    Args:
        yaml_config: Параметры из YAML
        **cli_args: Параметры из командной строки
        
    Returns:
        Объединённый словарь параметров
    """
    result = yaml_config.copy()
    
    for key, value in cli_args.items():
        # CLI переопределяет yaml только если значение явно указано
        if value is not None and value is not False:
            result[key] = value
        # Для bool False - проверяем был ли он в yaml
        elif isinstance(value, bool) and value is False:
            if key not in result:
                result[key] = value
    
    return result
