"""Stalwart Mail Server установщик."""
import sys
from pathlib import Path

sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class StalwartInstaller(AppInstaller):
    name = "stalwart"
    description = "Stalwart Mail Server"
    default_cores = 1
    default_memory = 1024
    default_disk = 5
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.logger.info("Installing Stalwart Mail Server...")
        self.system.apt_update()
        self.system.apt_install(["curl"])
        
        # Запуск официального скрипта установки
        # Мы используем -s для silent режима если возможно, 
        # но скрипт stalwart обычно довольно автономен.
        self.system.run(["bash", "-c", "curl -sSL https://www.stalw.art/install.sh | sh"], check=True)
        
    def get_result(self) -> InstallResult:
        return InstallResult(
            success=True, 
            message="Stalwart Mail Server installed. Access via port 8080 (Admin UI).",
            access_url="http://localhost:8080"
        )
