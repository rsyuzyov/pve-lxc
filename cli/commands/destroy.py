"""Команда destroy - удаление LXC контейнера."""

import typer

import sys
sys.path.insert(0, str(__file__).rsplit("/", 4)[0])
from lib.logger import Logger
from lib.validation import validate_ctid, ValidationError
from cli.core.pve import PVE
from cli.core.container import destroy_container

app = typer.Typer()


@app.command()
def destroy(
    ctid: int = typer.Argument(..., help="CTID контейнера"),
    force: bool = typer.Option(False, "--force", "-f", help="Удалить без подтверждения"),
    json_output: bool = typer.Option(False, "--json", help="Вывод в JSON формате"),
):
    """Удалить LXC контейнер."""
    logger = Logger(json_output=json_output)
    
    try:
        validate_ctid(ctid)
    except ValidationError as e:
        logger.error(str(e))
        raise typer.Exit(1)
    
    logger.set_context(command="destroy", ctid=ctid)
    
    # Проверяем существование контейнера
    pve = PVE(logger)
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
    
    success = destroy_container(logger, ctid, force=force)
    
    if success:
        logger.result(True, {"ctid": ctid, "message": f"Container {ctid} destroyed"})
    else:
        logger.result(False, {"message": f"Failed to destroy container {ctid}"})
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
