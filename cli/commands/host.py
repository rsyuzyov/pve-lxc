"""Команды управления PVE хостами."""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.core.host_manager import HostManager
from cli.core.ssh_config import SSHConfigError
from lib.exceptions import HostNotFoundError

console = Console()
host_app = typer.Typer(
    name="host",
    help="Управление PVE хостами"
)


def get_host_manager() -> HostManager:
    """Получить экземпляр HostManager."""
    return HostManager()


@host_app.command("add")
def host_add(
    name: str = typer.Argument(..., help="Имя хоста (алиас для SSH)"),
    hostname: str = typer.Option(..., "--hostname", "-h", help="IP адрес или hostname"),
    user: str = typer.Option("root", "--user", "-u", help="SSH пользователь"),
    port: int = typer.Option(22, "--port", "-p", help="SSH порт"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Путь к SSH ключу"),
):
    """Добавить PVE хост."""
    manager = get_host_manager()
    
    try:
        manager.add(name=name, hostname=hostname, user=user, port=port, key=key)
        console.print(f"[green]✓[/green] Хост '{name}' добавлен")
    except SSHConfigError as e:
        console.print(f"[red]✗[/red] Ошибка: {e}")
        raise typer.Exit(1)


@host_app.command("remove")
def host_remove(
    name: str = typer.Argument(..., help="Имя хоста для удаления"),
):
    """Удалить PVE хост."""
    manager = get_host_manager()
    
    if manager.remove(name):
        console.print(f"[green]✓[/green] Хост '{name}' удалён")
    else:
        console.print(f"[red]✗[/red] Хост '{name}' не найден")
        raise typer.Exit(1)


@host_app.command("list")
def host_list(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Показать PVE версию"),
):
    """Список PVE хостов."""
    manager = get_host_manager()
    hosts = manager.list()
    default_host = manager.get_default()
    
    if not hosts:
        console.print("Нет настроенных хостов")
        console.print("\nДобавьте хост командой:")
        console.print("  pve-lxc host add <name> --hostname <ip>")
        return
    
    table = Table(title="PVE Хосты")
    table.add_column("Имя", style="cyan")
    table.add_column("Адрес")
    table.add_column("Пользователь")
    table.add_column("Порт")
    table.add_column("По умолчанию", justify="center")
    
    if verbose:
        table.add_column("Статус")
        table.add_column("PVE версия")
    
    for host in hosts:
        name = host.get("name", "")
        is_default = "✓" if name == default_host else ""
        
        row = [
            name,
            host.get("hostname", ""),
            host.get("user", "root"),
            host.get("port", "22"),
            is_default,
        ]
        
        if verbose:
            test_result = manager.test(name)
            status = "[green]online[/green]" if test_result["connected"] else "[red]offline[/red]"
            pve_version = test_result.get("pve_version", "-") or "-"
            row.extend([status, pve_version])
        
        table.add_row(*row)
    
    console.print(table)


@host_app.command("test")
def host_test(
    name: str = typer.Argument(..., help="Имя хоста для проверки"),
):
    """Проверить подключение к PVE хосту."""
    manager = get_host_manager()
    
    console.print(f"Проверка подключения к '{name}'...")
    
    result = manager.test(name)
    
    if result["connected"]:
        console.print(f"[green]✓[/green] Подключение успешно")
        console.print(f"  PVE версия: {result['pve_version']}")
    else:
        console.print(f"[red]✗[/red] Ошибка подключения")
        if result.get("error"):
            console.print(f"  Причина: {result['error']}")
        raise typer.Exit(1)


@host_app.command("set-default")
def host_set_default(
    name: str = typer.Argument(..., help="Имя хоста по умолчанию"),
):
    """Установить хост по умолчанию."""
    manager = get_host_manager()
    
    try:
        manager.set_default(name)
        console.print(f"[green]✓[/green] Хост '{name}' установлен по умолчанию")
    except HostNotFoundError as e:
        console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)
