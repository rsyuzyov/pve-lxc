"""Foreman установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class ForemanInstaller(AppInstaller):
    name = "foreman"
    description = "Foreman Infrastructure Management"
    default_cores = 4
    default_memory = 8192
    default_disk = 40
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["ca-certificates", "curl"])
        self.log("Foreman requires manual installation. See docs.")
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="Foreman base installed", access_url="http://localhost:3000")
