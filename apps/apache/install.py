"""Apache установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class ApacheInstaller(AppInstaller):
    name = "apache"
    description = "Apache HTTP Server"
    default_cores = 1
    default_memory = 512
    default_disk = 8
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["apache2"])
        self.system.systemctl("enable", "apache2")
        self.system.systemctl("start", "apache2")
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="Apache installed", access_url="http://localhost")
