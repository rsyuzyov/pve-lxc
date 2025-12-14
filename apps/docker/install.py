"""Docker установщик."""

import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])

from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry


@AppRegistry.register
class DockerInstaller(AppInstaller):
    name = "docker"
    description = "Docker Engine"
    default_cores = 2
    default_memory = 2048
    default_disk = 20
    parameters = [{"name": "compose", "type": "bool", "default": True, "description": "Установить Docker Compose"}]
    
    def validate(self) -> bool:
        return True
    
    def pre_install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["ca-certificates", "curl", "gnupg"])
    
    def install(self) -> None:
        self.log("Adding Docker repository")
        self.system.run(["install", "-m", "0755", "-d", "/etc/apt/keyrings"])
        self.system.run([
            "curl", "-fsSL", "https://download.docker.com/linux/debian/gpg",
            "-o", "/etc/apt/keyrings/docker.asc"
        ])
        
        # Add repo
        self.system.run(["bash", "-c", 
            'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] '
            'https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" '
            '> /etc/apt/sources.list.d/docker.list'
        ])
        
        self.system.apt_update()
        self.system.apt_install(["docker-ce", "docker-ce-cli", "containerd.io", "docker-compose-plugin"])
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="Docker installed", access_url=None)
