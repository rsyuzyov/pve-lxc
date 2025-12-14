"""Команда list - список контейнеров."""

import typer
from rich.console import Console
from rich.table import Table

import sys
sys.path.insert(0, str(__file__).rsplit("/", 4)[0])
from lib.logger import Logger
from cli.core.pve import PVE

app = typer.Typer()


@app.command("list")
def list_containers(
    json_output: bool = typer.Option(False, "--json", help="Вывод в JSON формате"),
):
    """Показать список LXC контейнеров."""
    logger = Logger(json_output=json_output)
    logger.set_context(command="list")
    
    pve = PVE(logger)
    containers = pve.list_containers()
    
    if json_output:
        data = [
            {
                "ctid": c.ctid,
                "name": c.name,
                "status": c.status,
                "ip": c.ip,
                "cores": c.cores,
                "memory": c.memory
            }
            for c in containers
        ]
        logger.result(True, {"containers": data, "count": len(data)})
    else:
        console = Console()
        table = Table(title="LXC Containers")
        
        table.add_column("CTID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("IP", style="blue")
        table.add_column("Cores")
        table.add_column("Memory")
        
        for c in containers:
            status_style = "green" if c.status == "running" else "red"
            table.add_row(
                str(c.ctid),
                c.name,
                f"[{status_style}]{c.status}[/{status_style}]",
                c.ip or "-",
                str(c.cores),
                f"{c.memory}MB"
            )
        
        console.print(table)


if __name__ == "__main__":
    app()
