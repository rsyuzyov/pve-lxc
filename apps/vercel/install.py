"""Vercel CLI установщик."""

from pathlib import Path

import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])

from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry


@AppRegistry.register
class VercelInstaller(AppInstaller):
    name = "vercel"
    description = "Vercel CLI - Deploy and manage Vercel projects"
    default_cores = 2
    default_memory = 2048
    default_disk = 10
    parameters = [
        {"name": "token", "type": "string", "required": False, "description": "Vercel API token"},
        {"name": "scope", "type": "string", "required": False, "description": "Team scope"},
    ]
    
    NODE_VERSION = "20"
    
    def validate(self) -> bool:
        return True
    
    def pre_install(self) -> None:
        """Установка Node.js если не установлен."""
        result = self.system.run(["which", "node"], check=False)
        if result.returncode != 0:
            self.log("Node.js not found, installing...")
            self._install_nodejs()
    
    def _install_nodejs(self) -> None:
        """Установка Node.js через NodeSource."""
        self.system.apt_update()
        self.system.apt_install(["ca-certificates", "curl", "gnupg"])
        
        # NodeSource setup
        self.system.run([
            "bash", "-c",
            f"curl -fsSL https://deb.nodesource.com/setup_{self.NODE_VERSION}.x | bash -"
        ])
        self.system.apt_install(["nodejs"])
    
    def install(self) -> None:
        """Установка Vercel CLI."""
        self.log("Installing Vercel CLI...")
        self.system.run(["npm", "install", "-g", "vercel"])
    
    def post_install(self) -> None:
        """Настройка токена если указан."""
        token = self.config.get("token")
        if token:
            self.log("Configuring Vercel token...")
            self._configure_token(token)
    
    def _configure_token(self, token: str) -> None:
        """Сохранение токена в конфиг."""
        config_dir = Path.home() / ".config" / "vercel"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        auth_file = config_dir / "auth.json"
        scope = self.config.get("scope", "")
        
        auth_content = f'{{"token": "{token}"}}'
        auth_file.write_text(auth_content)
        auth_file.chmod(0o600)
        
        if scope:
            config_file = config_dir / "config.json"
            config_file.write_text(f'{{"currentTeam": "{scope}"}}')
    
    def get_result(self) -> InstallResult:
        token = self.config.get("token")
        message = "Vercel CLI installed successfully"
        if not token:
            message += ". Run 'vercel login' to authenticate"
        
        return InstallResult(
            success=True,
            message=message,
            credentials={"token": token} if token else None
        )
