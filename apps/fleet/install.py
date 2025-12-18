"""Fleet DM установщик."""
import sys
from pathlib import Path

# Добавляем корень проекта в путь для импорта
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class FleetInstaller(AppInstaller):
    name = "fleet"
    description = "Fleet Device Management"
    default_cores = 2
    default_memory = 4096
    default_disk = 20
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        # 1. Установка зависимостей
        self.system.apt_update()
        self.system.apt_install([
            "mariadb-server",
            "redis-server",
            "wget",
            "unzip"
        ])
        
        # 2. Скачивание Fleet
        # Версия v4.65.0
        version = "4.65.0"
        url = f"https://github.com/fleetdm/fleet/releases/download/v{version}/fleet.zip"
        self.system.run(["wget", "-O", "/tmp/fleet.zip", url])
        self.system.run(["unzip", "-o", "/tmp/fleet.zip", "-d", "/tmp/fleet_dist"])
        self.system.run(["cp", "/tmp/fleet_dist/fleet", "/usr/local/bin/fleet"])
        self.system.run(["cp", "/tmp/fleet_dist/fleetctl", "/usr/local/bin/fleetctl"])
        self.system.run(["chmod", "+x", "/usr/local/bin/fleet", "/usr/local/bin/fleetctl"])
        
        # 3. Настройка MariaDB
        self.system.run(["mariadb", "-e", "CREATE DATABASE IF NOT EXISTS fleet;"])
        self.system.run(["mariadb", "-e", "GRANT ALL PRIVILEGES ON fleet.* TO 'fleet'@'localhost' IDENTIFIED BY 'fleet123';"])
        self.system.run(["mariadb", "-e", "FLUSH PRIVILEGES;"])
        
        # 4. Подготовка БД Fleet
        self.system.run([
            "fleet", "prepare", "db",
            "--mysql_address=localhost:3306",
            "--mysql_database=fleet",
            "--mysql_username=fleet",
            "--mysql_password=fleet123"
        ])
        
    def configure(self) -> None:
        # 5. Создание systemd сервиса
        service_content = """[Unit]
Description=Fleet Device Management
After=network.target mariadb.service redis-server.service

[Service]
ExecStart=/usr/local/bin/fleet serve \\
    --mysql_address=localhost:3306 \\
    --mysql_database=fleet \\
    --mysql_username=fleet \\
    --mysql_password=fleet123 \\
    --redis_address=localhost:6379 \\
    --server_address=0.0.0.0:8080
Restart=always
User=root

[Install]
WantedBy=multi-user.target
"""
        self.system.write_file(Path("/etc/systemd/system/fleet.service"), service_content)
        self.system.run(["systemctl", "daemon-reload"])
        self.system.systemctl("enable", "fleet")
        self.system.systemctl("start", "fleet")
        
    def get_result(self) -> InstallResult:
        return InstallResult(
            success=True,
            message="Fleet DM installed successfully",
            access_url="http://localhost:8080",
            credentials={"mysql_user": "fleet", "mysql_password": "fleet123"}
        )
