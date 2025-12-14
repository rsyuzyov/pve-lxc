"""Prometheus установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class PrometheusInstaller(AppInstaller):
    name = "prometheus"
    description = "Prometheus Monitoring"
    default_cores = 2
    default_memory = 2048
    default_disk = 20
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["prometheus"])
        self.system.systemctl("enable", "prometheus")
        self.system.systemctl("start", "prometheus")
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="Prometheus installed", access_url="http://localhost:9090")
