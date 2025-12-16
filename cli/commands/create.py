"""Команда create - создание LXC контейнера."""

import typer
from typing import Optional

import sys
sys.path.insert(0, str(__file__).rsplit("/", 4)[0])
from lib.logger import Logger
from lib.validation import validate_name, validate_ip, validate_resources, ValidationError
from cli.core.container import create_container
from cli.core.host_manager import HostManager
from cli.core.yaml_config import load_yaml_config, merge_config

app = typer.Typer()


def get_executor_from_context(ctx: typer.Context):
    """Получить executor из контекста."""
    host = ctx.obj.get("host") if ctx.obj else None
    manager = HostManager()
    return manager.get_executor(host)


@app.command()
def create(
    ctx: typer.Context,
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Имя контейнера"),
    cores: Optional[int] = typer.Option(None, "--cores", "-c", help="Количество ядер CPU"),
    memory: Optional[int] = typer.Option(None, "--memory", "-m", help="Память в МБ"),
    disk: Optional[int] = typer.Option(None, "--disk", "-d", help="Размер диска в ГБ"),
    ip: Optional[str] = typer.Option(None, "--ip", help="IP адрес или диапазон (21-50 или 192.168.1.100/24)"),
    gateway: Optional[str] = typer.Option(None, "--gateway", "-g", help="Gateway"),
    gpu: bool = typer.Option(False, "--gpu", help="Включить GPU passthrough"),
    json_output: bool = typer.Option(False, "--json", help="Вывод в JSON формате"),
    config: Optional[str] = typer.Option(None, "--config", "-C", help="Путь к YAML файлу с параметрами"),
    help_flag: bool = typer.Option(False, "--help", "-h", is_eager=True, help="Показать справку"),
):
    """Создать LXC контейнер."""
    # Показываем help если нет параметров
    if not any([name, config]):
        typer.echo(ctx.get_help())
        raise typer.Exit(0)
    
    logger = Logger(json_output=json_output)
    
    # Загружаем yaml и мержим с CLI
    try:
        yaml_cfg = load_yaml_config(config)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise typer.Exit(1)
    
    cfg = merge_config(yaml_cfg, name=name, cores=cores, memory=memory, 
                       disk=disk, ip=ip, gateway=gateway, gpu=gpu)
    
    # Извлекаем параметры
    name = cfg.get("name")
    cores = cfg.get("cores")
    memory = cfg.get("memory")
    disk = cfg.get("disk")
    ip = cfg.get("ip")
    gateway = cfg.get("gateway")
    gpu = cfg.get("gpu", False)
    
    if not name:
        logger.error("Name is required (--name or in config)")
        raise typer.Exit(1)
    
    try:
        # Валидация
        validate_name(name)
        if ip:
            validate_ip(ip)
        if cores or memory or disk:
            validate_resources(cores=cores, memory=memory, disk=disk)
    except ValidationError as e:
        logger.error(str(e))
        raise typer.Exit(1)
    
    logger.set_context(command="create", name=name)
    
    # Получаем executor из контекста (--host)
    executor = get_executor_from_context(ctx)
    
    result = create_container(
        logger=logger,
        name=name,
        cores=cores,
        memory=memory,
        disk=disk,
        ip=ip,
        gateway=gateway,
        gpu=gpu,
        executor=executor
    )
    
    if result.success:
        logger.result(True, {"ctid": result.ctid, "ip": result.ip})
    else:
        logger.result(False, {"message": result.message})
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
