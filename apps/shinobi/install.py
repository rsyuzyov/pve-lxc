"""Shinobi установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class ShinobiInstaller(AppInstaller):
    name = "shinobi"
    description = "Shinobi Video Surveillance"
    default_cores = 4
    default_memory = 4096
    default_disk = 40
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["git", "nodejs", "npm", "ffmpeg", "mariadb-server"])
        self.system.run(["git", "clone", "https://gitlab.com/Shinobi-Systems/Shinobi.git", "/opt/shinobi"])
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="Shinobi installed", access_url="http://localhost:8080")
