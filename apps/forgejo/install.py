"""Forgejo установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class ForgejoInstaller(AppInstaller):
    name = "forgejo"
    description = "Forgejo Git Server"
    default_cores = 2
    default_memory = 1024
    default_disk = 20
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["git", "curl"])
        self.system.run(["curl", "-sL", "https://codeberg.org/forgejo/forgejo/releases/download/v7.0.0/forgejo-7.0.0-linux-amd64", "-o", "/usr/local/bin/forgejo"])
        self.system.run(["chmod", "+x", "/usr/local/bin/forgejo"])
        self.system.run(["useradd", "-r", "-m", "-d", "/var/lib/forgejo", "-s", "/bin/bash", "forgejo"])
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="Forgejo installed", access_url="http://localhost:3000")
