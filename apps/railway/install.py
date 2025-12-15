"""Railway CLI установщик."""

from pathlib import Path

import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])

from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry


@AppRegistry.register
class RailwayInstaller(AppInstaller):
    name = "railway"
    description = "Railway CLI - Deploy and manage Railway projects"
    default_cores = 2
    default_memory = 2048
    default_disk = 10
    parameters = [
        {"name": "token", "type": "string", "required": False, "description": "Railway API token"},
    ]
    
    def validate(self) -> bool:
        return True
    
    def pre_install(self) -> None:
        """Установка зависимостей."""
        self.system.apt_update()
        self.system.apt_install(["curl", "ca-certificates"])
    
    def install(self) -> None:
        """Установка Railway CLI через официальный скрипт."""
        self.log("Installing Railway CLI...")
        self.system.run([
            "bash", "-c",
            "curl -fsSL https://railway.app/install.sh | sh"
        ])
    
    def post_install(self) -> None:
        """Настройка токена если указан."""
        token = self.config.get("token")
        if token:
            self.log("Configuring Railway token...")
            self._configure_token(token)
    
    def _configure_token(self, token: str) -> None:
        """Сохранение токена в переменную окружения."""
        config_dir = Path.home() / ".railway"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Railway использует переменную RAILWAY_TOKEN
        bashrc = Path.home() / ".bashrc"
        export_line = f'export RAILWAY_TOKEN="{token}"'
        
        if bashrc.exists():
            content = bashrc.read_text()
            if "RAILWAY_TOKEN" not in content:
                bashrc.write_text(content + f"\n{export_line}\n")
        else:
            bashrc.write_text(f"{export_line}\n")
    
    def get_result(self) -> InstallResult:
        token = self.config.get("token")
        message = "Railway CLI installed successfully"
        if not token:
            message += ". Run 'railway login' to authenticate"
        
        return InstallResult(
            success=True,
            message=message,
            credentials={"token": token} if token else None
        )
