"""Proxmox Mail Gateway установщик."""
import sys
from pathlib import Path

sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class PMGInstaller(AppInstaller):
    name = "pmg"
    description = "Proxmox Mail Gateway"
    default_cores = 2
    default_memory = 2048
    default_disk = 10
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.logger.info("Adding Proxmox Mail Gateway repository...")
        
        # Определение дистрибутива (упрощенно до bookworm для примера, 
        # в реальной системе стоит проверять /etc/os-release)
        codename = "bookworm" 
        
        # Добавление GPG ключа
        gpg_path = Path("/etc/apt/trusted.gpg.d/proxmox-release-bookworm.gpg")
        if not self.system.file_exists(gpg_path):
            self.system.run([
                "wget", "https://enterprise.proxmox.com/debian/proxmox-release-bookworm.gpg", 
                "-O", str(gpg_path)
            ])
        
        # Добавление репозитория
        repo_content = f"deb http://download.proxmox.com/debian/pmg {codename} pmg-no-subscription\n"
        self.system.write_file(Path("/etc/apt/sources.list.d/pmg-community.list"), repo_content)
        
        self.system.apt_update()
        
        # Установка PMG
        # Примечание: установка может быть интерактивной, 
        # но обычно в Debian можно использовать DEBIAN_FRONTEND=noninteractive
        self.system.run(["apt-get", "install", "-y", "-qq", "proxmox-mail-gateway"], check=True)
    
    def get_result(self) -> InstallResult:
        return InstallResult(
            success=True, 
            message="Proxmox Mail Gateway installed. Access via https://<ip>:8006",
            access_url="https://localhost:8006"
        )
