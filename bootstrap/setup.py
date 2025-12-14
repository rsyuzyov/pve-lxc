"""Базовая настройка контейнера."""

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from lib.logger import Logger
from lib.system import System
from lib.config import ConfigLoader


def setup_locale(system: System, locale: str = "en_US.UTF-8") -> bool:
    """Настроить локаль."""
    system.run(["locale-gen", locale])
    system.run(["update-locale", f"LANG={locale}"])
    return True


def setup_timezone(system: System, timezone: str = "UTC") -> bool:
    """Настроить часовой пояс."""
    system.run(["ln", "-sf", f"/usr/share/zoneinfo/{timezone}", "/etc/localtime"])
    system.run(["dpkg-reconfigure", "-f", "noninteractive", "tzdata"])
    return True


def install_base_packages(system: System, packages: list[str] = None) -> bool:
    """Установить базовые пакеты."""
    if packages is None:
        packages = ["curl", "wget", "git", "vim", "htop"]
    
    system.apt_update()
    system.apt_install(packages)
    return True


def run_bootstrap(logger: Logger = None) -> bool:
    """Выполнить полную базовую настройку."""
    if logger is None:
        logger = Logger()
    
    system = System(logger)
    config = ConfigLoader().load_user_config().merge()
    bootstrap_config = config.get("bootstrap", {})
    
    locale = bootstrap_config.get("locale", "en_US.UTF-8")
    timezone = bootstrap_config.get("timezone", "UTC")
    packages = bootstrap_config.get("packages", ["curl", "wget", "git", "vim", "htop"])
    
    logger.step("Setting up locale", current=1, total=3)
    setup_locale(system, locale)
    
    logger.step("Setting up timezone", current=2, total=3)
    setup_timezone(system, timezone)
    
    logger.step("Installing base packages", current=3, total=3)
    install_base_packages(system, packages)
    
    logger.success("Bootstrap completed")
    return True


if __name__ == "__main__":
    run_bootstrap()
