"""Команда apps - список и справка по приложениям."""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table

import sys
sys.path.insert(0, str(__file__).rsplit("/", 4)[0])
from lib.logger import Logger

app = typer.Typer()


def get_app_registry():
    """Получить реестр приложений (ленивая загрузка)."""
    try:
        from apps.registry import AppRegistry
        return AppRegistry
    except ImportError:
        return None


@app.command("apps")
def apps_command(
    help_app: Optional[str] = typer.Option(None, "--help", "-h", help="Показать справку по приложению"),
    json_output: bool = typer.Option(False, "--json", help="Вывод в JSON формате"),
):
    """Показать список доступных приложений."""
    logger = Logger(json_output=json_output)
    logger.set_context(command="apps")
    
    registry = get_app_registry()
    
    if registry is None:
        logger.error("App registry not available")
        raise typer.Exit(1)
    
    if help_app:
        # Справка по конкретному приложению
        help_text = registry.get_help(help_app)
        if help_text:
            if json_output:
                logger.result(True, {"app": help_app, "help": help_text})
            else:
                print(help_text)
        else:
            logger.error(f"App '{help_app}' not found")
            raise typer.Exit(1)
    else:
        # Список всех приложений
        apps_list = registry.list_all()
        
        if json_output:
            logger.result(True, {"apps": apps_list, "count": len(apps_list)})
        else:
            console = Console()
            table = Table(title="Available Applications")
            
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="green")
            
            for app_name in apps_list:
                installer = registry.get(app_name)
                desc = getattr(installer, 'description', '') if installer else ''
                table.add_row(app_name, desc)
            
            console.print(table)


if __name__ == "__main__":
    app()
