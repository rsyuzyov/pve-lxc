"""Команда ip - поиск свободных IP адресов."""

import typer

import sys
sys.path.insert(0, str(__file__).rsplit("/", 4)[0])
from lib.logger import Logger
from cli.core.network import Network

app = typer.Typer()


@app.command()
def ip(
    ip_range: str = typer.Argument(..., help="Диапазон IP (21-50 или 192.168.1.21-50)"),
    json_output: bool = typer.Option(False, "--json", help="Вывод в JSON формате"),
):
    """Найти свободные IP адреса в диапазоне."""
    logger = Logger(json_output=json_output)
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
