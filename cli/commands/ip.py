"""Команда ip - поиск свободных IP адресов."""

import typer
from typing import Optional

import sys
sys.path.insert(0, str(__file__).rsplit("/", 4)[0])
from lib.logger import Logger
from cli.core.network import Network
from cli.core.yaml_config import load_yaml_config, merge_config

app = typer.Typer()


@app.command()
def ip(
    ip_range: Optional[str] = typer.Argument(None, help="Диапазон IP (21-50 или 192.168.1.21-50)"),
    json_output: bool = typer.Option(False, "--json", help="Вывод в JSON формате"),
    config: Optional[str] = typer.Option(None, "--config", "-C", help="Путь к YAML файлу с параметрами"),
):
    """Найти свободные IP адреса в диапазоне."""
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
        logger.error("IP range is required (argument or in config)")
        raise typer.Exit(1)
    
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
