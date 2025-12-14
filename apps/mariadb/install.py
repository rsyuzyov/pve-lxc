"""MariaDB установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class MariadbInstaller(AppInstaller):
    name = "mariadb"
    description = "MariaDB Database"
    default_cores = 2
    default_memory = 2048
    default_disk = 20
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["mariadb-server"])
        self.system.systemctl("enable", "mariadb")
        self.system.systemctl("start", "mariadb")
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="MariaDB installed", access_url=None)
