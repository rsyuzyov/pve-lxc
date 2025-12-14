"""Syncthing установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class SyncthingInstaller(AppInstaller):
    name = "syncthing"
    description = "Syncthing File Sync"
    default_cores = 1
    default_memory = 512
    default_disk = 20
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["syncthing"])
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="Syncthing installed", access_url="http://localhost:8384")
