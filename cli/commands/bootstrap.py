"""Команда bootstrap - базовая настройка контейнера."""

import typer

import sys
sys.path.insert(0, str(__file__).rsplit("/", 4)[0])
from lib.logger import Logger
from lib.validation import validate_ctid, ValidationError
from cli.core.container import bootstrap_container
from cli.core.host_manager import HostManager

app = typer.Typer()


def get_executor_from_context(ctx: typer.Context):
    """Получить executor из контекста."""
    host = ctx.obj.get("host") if ctx.obj else None
    manager = HostManager()
    return manager.get_executor(host)


@app.command()
def bootstrap(
    ctx: typer.Context,
    ctid: int = typer.Argument(..., help="CTID контейнера"),
    json_output: bool = typer.Option(False, "--json", help="Вывод в JSON формате"),
):
    """Выполнить базовую настройку контейнера."""
    logger = Logger(json_output=json_output)
    
    try:
        validate_ctid(ctid)
    except ValidationError as e:
        logger.error(str(e))
        raise typer.Exit(1)
    
    logger.set_context(command="bootstrap", ctid=ctid)
    
    # Получаем executor из контекста (--host)
    executor = get_executor_from_context(ctx)
    
    success = bootstrap_container(logger, ctid, executor=executor)
    
    if success:
        logger.result(True, {"ctid": ctid})
    else:
        logger.result(False, {"message": "Bootstrap failed"})
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
