"""Загрузка и слияние YAML конфигураций."""

from pathlib import Path
from typing import Any
import yaml


class ConfigError(Exception):
    """Ошибка конфигурации с номером строки."""
    def __init__(self, message: str, line: int = None):
        self.line = line
        super().__init__(f"Line {line}: {message}" if line else message)


class ConfigLoader:
    """Загрузчик конфигурации с поддержкой слоёв."""

    DEFAULTS = {
        "container": {
            "cores": 2,
            "memory": 2048,
            "disk": 10,
            "template": "debian-12-standard",
            "storage": "local-lvm",
        },
        "network": {
            "bridge": "vmbr0",
            "ping_timeout": 1.0,
        },
        "bootstrap": {
            "locale": "en_US.UTF-8",
            "timezone": "UTC",
            "packages": ["curl", "wget", "git", "vim", "htop"],
        },
        "logging": {
            "level": "INFO",
            "json": False,
        },
    }

    def __init__(self):
        self.layers: list[dict] = [self.DEFAULTS.copy()]

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Глубокое слияние словарей."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _load_yaml(self, path: Path) -> dict:
        """Загрузить YAML с обработкой ошибок."""
        try:
            with open(path) as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            line = getattr(e, "problem_mark", None)
            line_num = line.line + 1 if line else None
            raise ConfigError(str(e), line=line_num)

    def load_defaults(self, path: Path) -> "ConfigLoader":
        """Загрузить глобальные дефолты из файла."""
        if path.exists():
            data = self._load_yaml(path)
            self.layers.append(data)
        return self

    def load_app_config(self, app_name: str, apps_dir: Path = None) -> "ConfigLoader":
        """Загрузить конфигурацию приложения."""
        if apps_dir is None:
            apps_dir = Path(__file__).parent.parent / "apps"
        config_path = apps_dir / app_name / "config.yaml"
        if config_path.exists():
            data = self._load_yaml(config_path)
            self.layers.append(data)
        return self

    def load_user_config(self) -> "ConfigLoader":
        """Загрузить пользовательскую конфигурацию."""
        user_config = Path.home() / ".pve-lxc" / "config.yaml"
        if user_config.exists():
            data = self._load_yaml(user_config)
            self.layers.append(data)
        return self

    def override(self, **kwargs) -> "ConfigLoader":
        """Добавить CLI переопределения."""
        # Фильтруем None значения
        filtered = {k: v for k, v in kwargs.items() if v is not None}
        if filtered:
            self.layers.append(filtered)
        return self

    def merge(self) -> dict[str, Any]:
        """Слияние всех слоёв с приоритетом."""
        result = {}
        for layer in self.layers:
            result = self._deep_merge(result, layer)
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение по ключу с поддержкой точечной нотации."""
        merged = self.merge()
        keys = key.split(".")
        value = merged
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
