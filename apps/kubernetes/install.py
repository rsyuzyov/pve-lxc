"""Kubernetes (k3s) установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class KubernetesInstaller(AppInstaller):
    name = "kubernetes"
    description = "Kubernetes (k3s)"
    default_cores = 4
    default_memory = 4096
    default_disk = 40
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["curl"])
        self.system.run(["curl", "-sfL", "https://get.k3s.io", "-o", "/tmp/k3s.sh"])
        self.system.run(["bash", "/tmp/k3s.sh"])
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="k3s installed", access_url=None)
