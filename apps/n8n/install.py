"""n8n установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class N8nInstaller(AppInstaller):
    name = "n8n"
    description = "n8n Workflow Automation"
    default_cores = 2
    default_memory = 2048
    default_disk = 10
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["nodejs", "npm"])
        self.system.run(["npm", "install", "-g", "n8n"])
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="n8n installed", access_url="http://localhost:5678")
