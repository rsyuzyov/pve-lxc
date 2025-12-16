"""Команда destroy - удаление LXC контейнера."""

import typer
from typing import Optional

import sys
sys.path.insert(0, str(__file__).rsplit("/", 4)[0])
from lib.logger import Logger
from lib.validation import validate_ctid, ValidationError
from cli.core.pve import PVE
from cli.core.container import destroy_container
from cli.core.host_manager import HostManager
from cli.core.yaml_config import load_yaml_config, merge_config

app = typer.Typer()


def get_executor_from_context(ctx: typer.Context):
    """Получить executor из контекста."""
    host = ctx.obj.get("host") if ctx.obj else None
    manager = HostManager()
    return manager.get_executor(host)


@app.command()
def destroy(
    ctx: typer.Context,
    ctid: Optional[int] = typer.Argument(None, help="CTID контейнера"),
    force: bool = typer.Option(False, "--force", "-f", help="Удалить без подтверждения"),
    json_output: bool = typer.Option(False, "--json", help="Вывод в JSON формате"),
    config: Optional[str] = typer.Option(None, "--config", "-C", help="Путь к YAML файлу с параметрами"),
):
    """Удалить LXC контейнер."""
    logger = Logger(json_output=json_output)
    
    # Загружаем yaml и мержим с CLI
    try:
        yaml_cfg = load_yaml_config(config)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise typer.Exit(1)
    
    cfg = merge_config(yaml_cfg, ctid=ctid, force=force)
    ctid = cfg.get("ctid")
    force = cfg.get("force", False)
    
    if ctid is None:
        logger.error("CTID is required (argument or in config)")
        raise typer.Exit(1)
    
    try:
        validate_ctid(ctid)
    except ValidationError as e:
        logger.error(str(e))
        raise typer.Exit(1)
    
    logger.set_context(command="destroy", ctid=ctid)
    
    # Получаем executor из контекста (--host)
    executor = get_executor_from_context(ctx)
    
    # Проверяем существование контейнера
    pve = PVE(logger, executor=executor)
    container = pve.get_container(ctid)
    
    if not container:
        logger.error(f"Container {ctid} not found")
        raise typer.Exit(1)
    
    # Запрос подтверждения для запущенного контейнера
    if container.status == "running" and not force:
        confirm = typer.confirm(f"Container {ctid} is running. Stop and destroy?")
        if not confirm:
            logger.info("Aborted")
            raise typer.Exit(0)
        force = True
    
    success = destroy_container(logger, ctid, force=force, executor=executor)
    
    if success:
        logger.result(True, {"ctid": ctid, "message": f"Container {ctid} destroyed"})
    else:
        logger.result(False, {"message": f"Failed to destroy container {ctid}"})
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
