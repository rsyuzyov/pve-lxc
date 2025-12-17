"""Команда free-ip - поиск свободных IP адресов."""

import typer
from typing import Optional

import sys
sys.path.insert(0, str(__file__).rsplit("/", 4)[0])
from lib.logger import Logger
from cli.core.network import Network
from cli.core.yaml_config import load_yaml_config, merge_config

from rich.panel import Panel
from rich.console import Console

SAMPLES = """\
[dim]# Поиск в диапазоне с полным IP[/]
pve-lxc free-ip 192.168.1.21-50

[dim]# Короткий формат (использует gateway из конфига)[/]
pve-lxc free-ip 21-50

[dim]# Вывод в JSON[/]
pve-lxc free-ip 192.168.1.21-50 --json\
"""

app = typer.Typer()


@app.command(epilog="")
def ip(
    ctx: typer.Context,
    ip_range: Optional[str] = typer.Argument(None, help="Диапазон IP (21-50 или 192.168.1.21-50)"),
    json_output: bool = typer.Option(False, "--json", help="Вывод в JSON формате"),
    config: Optional[str] = typer.Option(None, "--config", "-C", help="Путь к YAML файлу с параметрами"),
    help_flag: bool = typer.Option(False, "--help", "-h", is_eager=True, help="Показать справку"),
):
    """Найти свободные IP адреса в диапазоне (ping-сканирование)."""
    if help_flag:
        typer.echo(ctx.get_help())
        console = Console()
        console.print()
        console.print(Panel(SAMPLES, title="Samples", title_align="left", border_style="dim"))
        raise typer.Exit()
    logger = Logger(json_output=json_output)
    
    # Загружаем yaml и мержим с CLI
    try:
        yaml_cfg = load_yaml_config(config)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise typer.Exit(1)
    
    cfg = merge_config(yaml_cfg, ip_range=ip_range)
    ip_range = cfg.get("ip_range")
    
    if not ip_range:
        # Без параметров — показываем help
        typer.echo(ctx.get_help())
        console = Console()
        console.print()
        console.print(Panel(SAMPLES, title="Samples", title_align="left", border_style="dim"))
        raise typer.Exit()
    
    logger.set_context(command="ip", range=ip_range)
    
    network = Network(logger)
    
    try:
        free_ips = network.list_free_ips(ip_range)
    except Exception as e:
        logger.error(str(e))
        raise typer.Exit(1)
    
    if json_output:
        logger.result(True, {"free_ips": free_ips, "count": len(free_ips)})
    else:
        if free_ips:
            logger.info(f"Found {len(free_ips)} free IPs:")
            for ip_addr in free_ips:
                print(f"  {ip_addr}")
        else:
            logger.warn("No free IPs found in range")


if __name__ == "__main__":
    app()
