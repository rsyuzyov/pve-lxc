"""Команда deploy - развертывание приложений в контейнерах."""

import typer
from typing import Optional
from pathlib import Path

import sys
sys.path.insert(0, str(__file__).rsplit("/", 4)[0])
from lib.logger import Logger
from lib.system import System, CommandResult
from lib.config import ConfigLoader
from lib.validation import validate_ctid, validate_name, ValidationError
from cli.core.pve import PVE
from cli.core.container import create_container, bootstrap_container
from cli.core.host_manager import HostManager
from cli.core.yaml_config import load_yaml_config, merge_config
from apps.registry import AppRegistry


def get_executor_from_context(ctx: typer.Context):
    """Получить executor из контекста."""
    host = ctx.obj.get("host") if ctx.obj else None
    manager = HostManager()
    return manager.get_executor(host)


class RemoteSystem:
    """System для выполнения команд в контейнере через pct exec."""
    
    def __init__(self, logger: Logger, pve, ctid: int):
        self.logger = logger
        self.pve = pve
        self.ctid = ctid
    
    def run(self, cmd: list[str], check: bool = True, capture: bool = True) -> CommandResult:
        """Выполнить команду в контейнере."""
        self.logger.debug(f"Running: {' '.join(cmd)}")
        result = self.pve.exec(self.ctid, cmd)
        if check and not result.success:
            self.logger.error(f"Command failed: {' '.join(cmd)}", stderr=result.stderr)
        return result
    
    def apt_update(self) -> CommandResult:
        """Обновить списки пакетов."""
        self.logger.info("Updating package lists")
        return self.run(["apt-get", "update", "-qq"])
    
    def apt_install(self, packages: list[str]) -> CommandResult:
        """Установить пакеты."""
        self.logger.info(f"Installing packages: {', '.join(packages)}")
        cmd = ["apt-get", "install", "-y", "-qq"] + packages
        return self.run(cmd)
    
    def systemctl(self, action: str, service: str) -> CommandResult:
        """Управление systemd сервисом."""
        self.logger.info(f"Systemctl {action} {service}")
        return self.run(["systemctl", action, service])


app = typer.Typer()


@app.command()
def deploy(
    ctx: typer.Context,
    app_name: Optional[str] = typer.Option(None, "--app", "-a", help="Имя приложения для установки"),
    container: Optional[int] = typer.Option(None, "--container", "-c", help="CTID существующего контейнера"),
    create: bool = typer.Option(False, "--create", help="Создать новый контейнер"),
    ctid: Optional[int] = typer.Option(None, "--ctid", help="CTID для нового контейнера (при --create)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Имя нового контейнера (при --create)"),
    cores: Optional[int] = typer.Option(None, "--cores", help="Количество ядер CPU"),
    memory: Optional[int] = typer.Option(None, "--memory", help="Память в МБ"),
    disk: Optional[int] = typer.Option(None, "--disk", help="Размер диска в ГБ"),
    ip: Optional[str] = typer.Option(None, "--ip", help="IP адрес"),
    gateway: Optional[str] = typer.Option(None, "--gateway", help="Шлюз"),
    json_output: bool = typer.Option(False, "--json", help="Вывод в JSON формате"),
    config: Optional[str] = typer.Option(None, "--config", "-C", help="Путь к YAML файлу с параметрами"),
):
    """Развернуть приложение в LXC контейнере."""
    logger = Logger(json_output=json_output)
    
    # Загружаем yaml и мержим с CLI
    try:
        yaml_cfg = load_yaml_config(config)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise typer.Exit(1)
    
    cfg = merge_config(yaml_cfg, app=app_name, container=container, create=create,
                       ctid=ctid, name=name, cores=cores, memory=memory, 
                       disk=disk, ip=ip, gateway=gateway)
    
    app_name = cfg.get("app")
    container = cfg.get("container")
    create = cfg.get("create", False)
    ctid = cfg.get("ctid")
    name = cfg.get("name")
    cores = cfg.get("cores")
    memory = cfg.get("memory")
    disk = cfg.get("disk")
    ip = cfg.get("ip")
    gateway = cfg.get("gateway")
    
    if not app_name:
        logger.error("App name is required (--app or in config)")
        raise typer.Exit(1)
    
    logger.set_context(command="deploy", app=app_name)
    
    # Получаем executor из контекста (--host)
    executor = get_executor_from_context(ctx)
    
    # Проверяем что приложение существует
    installer_class = AppRegistry.get(app_name)
    if not installer_class:
        logger.error(f"Application '{app_name}' not found")
        available = ", ".join(AppRegistry.list_all())
        logger.info(f"Available apps: {available}")
        raise typer.Exit(1)
    
    # Валидация параметров
    try:
        if container:
            validate_ctid(container)
        if name:
            validate_name(name)
    except ValidationError as e:
        logger.error(str(e))
        raise typer.Exit(1)

    # Определяем CTID
    target_ctid = container  # существующий контейнер
    new_ctid = ctid  # желаемый CTID для нового контейнера
    
    if create:
        if not name:
            name = app_name
        
        # Получаем дефолты из приложения
        app_cores = cores or getattr(installer_class, 'default_cores', 2)
        app_memory = memory or getattr(installer_class, 'default_memory', 2048)
        app_disk = disk or getattr(installer_class, 'default_disk', 10)
        
        result = create_container(
            logger=logger,
            name=name,
            cores=app_cores,
            memory=app_memory,
            disk=app_disk,
            ip=ip,
            gateway=gateway,
            ctid=new_ctid,
            executor=executor
        )
        
        if not result.success:
            logger.error(f"Failed to create container: {result.message}")
            raise typer.Exit(1)
        
        target_ctid = result.ctid
        logger.success(f"Container {target_ctid} created")
        
        # Bootstrap контейнера
        bootstrap_container(logger, target_ctid, executor=executor)
    
    if not target_ctid:
        logger.error("Specify --container or use --create")
        raise typer.Exit(1)
    
    # Загружаем конфигурацию
    config = (
        ConfigLoader()
        .load_app_config(app_name)
        .load_user_config()
        .override(cores=cores, memory=memory, disk=disk)
        .merge()
    )
    
    # Создаём установщик и запускаем
    pve = PVE(logger, executor=executor)
    
    # Ждём готовности контейнера
    import time
    for _ in range(30):
        result = pve.exec(target_ctid, ["true"])
        if result.success:
            break
        time.sleep(1)
    
    # Создаём RemoteSystem для выполнения команд в контейнере
    system = RemoteSystem(logger, pve, target_ctid)
    
    # Запускаем установку
    installer = installer_class(logger, system, config)
    result = installer.run()
    
    if result.success:
        logger.result(True, {
            "ctid": target_ctid,
            "app": app_name,
            "access_url": result.access_url,
            "credentials": result.credentials
        })
    else:
        logger.result(False, {
            "message": result.message,
            "log_path": str(result.log_path) if result.log_path else None
        })
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
