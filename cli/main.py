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
from cli.commands.ip import ip
from cli.commands.list import list_containers
from cli.commands.apps import apps_command
from cli.commands.deploy import deploy

app = typer.Typer(
    name="pve-lxc",
    help="Управление LXC контейнерами в Proxmox VE",
    add_completion=False
)


# Регистрация команд
app.command("create")(create)
app.command("destroy")(destroy)
app.command("bootstrap")(bootstrap)
app.command("ip")(ip)
app.command("list")(list_containers)
app.command("apps")(apps_command)
app.command("deploy")(deploy)


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Подробный вывод"),
    json_output: bool = typer.Option(False, "--json", help="Вывод в JSON формате"),
):
    """pve-lxc - CLI для управления LXC контейнерами в Proxmox VE."""
    pass


def run():
    """Запуск CLI."""
    app()


if __name__ == "__main__":
    run()
