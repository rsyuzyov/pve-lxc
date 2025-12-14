"""ZoneMinder установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class ZoneminderInstaller(AppInstaller):
    name = "zoneminder"
    description = "ZoneMinder Video Surveillance"
    default_cores = 4
    default_memory = 4096
    default_disk = 40
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["zoneminder"])
        self.system.systemctl("enable", "zoneminder")
        self.system.systemctl("start", "zoneminder")
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="ZoneMinder installed", access_url="http://localhost/zm")
