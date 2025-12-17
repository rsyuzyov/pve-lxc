"""Точка входа CLI приложения pve-lxc."""

import typer
from typing import Optional

import sys
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.commands.create import create
from cli.commands.destroy import destroy
from cli.commands.bootstrap import bootstrap
from cli.commands.ip import ip as free_ip
from cli.commands.list import list_containers
from cli.commands.apps import apps_command
from cli.commands.deploy import deploy
from cli.commands.host import host_app

from rich.panel import Panel
from rich.console import Console, Group
from rich.text import Text

SAMPLES_TEXT = """\
[dim]# Создание контейнера на локальном хосте[/]
pve-lxc create -n mycontainer

[dim]# Создание на удалённом хосте[/]
pve-lxc --host pve.local create -n mycontainer

[dim]# Создание с бутстрапом[/]
pve-lxc create -n mycontainer --bootstrap

[dim]# Создание с бутстрапом и установкой приложения[/]
pve-lxc create -n mycontainer --bootstrap --app docker

[dim]# Создание с автоматическим выбором свободного IP[/]
pve-lxc create -n mycontainer --ip 192.168.1.21-50

[dim]# Найти свободные IP в диапазоне[/]
pve-lxc free-ip 192.168.1.21-50

[dim]# Установить приложение в существующий контейнер[/]
pve-lxc deploy -c mycontainer -a docker

[dim]# Добавить хост в SSH config[/]
pve-lxc host add mycontainer\
"""

app = typer.Typer(
    name="pve-lxc",
    help="Управление LXC контейнерами в Proxmox VE",
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Подробный вывод"),
    json_output: bool = typer.Option(False, "--json", help="Вывод в JSON формате"),
    host: Optional[str] = typer.Option(None, "--host", "-H", help="PVE хост для подключения"),
):
    """pve-lxc - CLI для управления LXC контейнерами в Proxmox VE."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["json_output"] = json_output
    ctx.obj["host"] = host
    
    if ctx.invoked_subcommand is None:
        # Показываем стандартный help
        typer.echo(ctx.get_help())
        # Добавляем панель Samples
        console = Console()
        console.print()
        console.print(Panel(SAMPLES_TEXT, title="Samples", title_align="left", border_style="dim"))


# Регистрация команд
app.command("create")(create)
app.command("destroy")(destroy)
app.command("bootstrap")(bootstrap)
app.command("free-ip")(free_ip)
app.command("list")(list_containers)
app.command("apps")(apps_command)
app.command("deploy")(deploy)
app.add_typer(host_app, name="host")


def run():
    """Запуск CLI."""
    app()


if __name__ == "__main__":
    run()
