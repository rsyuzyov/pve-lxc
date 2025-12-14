"""Команда deploy - развертывание приложений в контейнерах."""

import typer
from typing import Optional
from pathlib import Path

import sys
sys.path.insert(0, str(__file__).rsplit("/", 4)[0])
from lib.logger import Logger
from lib.system import System
from lib.config import ConfigLoader
from lib.validation import validate_ctid, validate_name, ValidationError
from cli.core.pve import PVE
from cli.core.container import create_container
from apps.registry import AppRegistry

app = typer.Typer()


@app.command()
def deploy(
    app_name: str = typer.Option(..., "--app", "-a", help="Имя приложения для установки"),
    container: Optional[int] = typer.Option(None, "--container", "-c", help="CTID существующего контейнера"),
    create: bool = typer.Option(False, "--create", help="Создать новый контейнер"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Имя нового контейнера (при --create)"),
    cores: Optional[int] = typer.Option(None, "--cores", help="Количество ядер CPU"),
    memory: Optional[int] = typer.Option(None, "--memory", help="Память в МБ"),
    disk: Optional[int] = typer.Option(None, "--disk", help="Размер диска в ГБ"),
    ip: Optional[str] = typer.Option(None, "--ip", help="IP адрес"),
    json_output: bool = typer.Option(False, "--json", help="Вывод в JSON формате"),
):
    """Развернуть приложение в LXC контейнере."""
    logger = Logger(json_output=json_output)
    logger.set_context(command="deploy", app=app_name)
    
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
    ctid = container
    
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
            ip=ip
        )
        
        if not result.success:
            logger.error(f"Failed to create container: {result.message}")
            raise typer.Exit(1)
        
        ctid = result.ctid
        logger.success(f"Container {ctid} created")
    
    if not ctid:
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
    pve = PVE(logger)
    system = System(logger)
    
    # Копируем lib в контейнер
    lib_path = Path(__file__).parent.parent.parent / "lib"
    pve.exec(ctid, ["mkdir", "-p", "/opt/pve-lxc/lib"])
    for py_file in lib_path.glob("*.py"):
        pve.push(ctid, py_file, Path(f"/opt/pve-lxc/lib/{py_file.name}"))
    
    # Запускаем установку
    installer = installer_class(logger, system, config)
    result = installer.run()
    
    if result.success:
        logger.result(True, {
            "ctid": ctid,
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
