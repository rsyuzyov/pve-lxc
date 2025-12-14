"""PostgreSQL установщик."""

import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])

from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry


@AppRegistry.register
class PostgresInstaller(AppInstaller):
    name = "postgres"
    description = "PostgreSQL Database"
    default_cores = 2
    default_memory = 2048
    default_disk = 20
    parameters = [{"name": "version", "type": "string", "default": "16", "description": "Версия PostgreSQL"}]
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["postgresql", "postgresql-contrib"])
        self.system.systemctl("enable", "postgresql")
        self.system.systemctl("start", "postgresql")
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="PostgreSQL installed", access_url=None)
