"""Команда create - создание LXC контейнера."""

import typer
from typing import Optional

import sys
sys.path.insert(0, str(__file__).rsplit("/", 4)[0])
from lib.logger import Logger
from lib.validation import validate_name, validate_ip, validate_resources, ValidationError
from cli.core.container import create_container

app = typer.Typer()


@app.command()
def create(
    name: str = typer.Option(..., "--name", "-n", help="Имя контейнера"),
    cores: Optional[int] = typer.Option(None, "--cores", "-c", help="Количество ядер CPU"),
    memory: Optional[int] = typer.Option(None, "--memory", "-m", help="Память в МБ"),
    disk: Optional[int] = typer.Option(None, "--disk", "-d", help="Размер диска в ГБ"),
    ip: Optional[str] = typer.Option(None, "--ip", help="IP адрес или диапазон (21-50 или 192.168.1.100/24)"),
    gateway: Optional[str] = typer.Option(None, "--gateway", "-g", help="Gateway"),
    gpu: bool = typer.Option(False, "--gpu", help="Включить GPU passthrough"),
    json_output: bool = typer.Option(False, "--json", help="Вывод в JSON формате"),
):
    """Создать LXC контейнер."""
    logger = Logger(json_output=json_output)
    
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
    
    result = create_container(
        logger=logger,
        name=name,
        cores=cores,
        memory=memory,
        disk=disk,
        ip=ip,
        gateway=gateway,
        gpu=gpu
    )
    
    if result.success:
        logger.result(True, {"ctid": result.ctid, "ip": result.ip})
    else:
        logger.result(False, {"message": result.message})
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
