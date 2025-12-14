"""GitLab CE установщик."""

import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])

from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry


@AppRegistry.register
class GitlabInstaller(AppInstaller):
    """Установщик GitLab CE."""
    
    name = "gitlab"
    description = "GitLab CE - DevOps платформа"
    default_cores = 4
    default_memory = 8192
    default_disk = 40
    parameters = [
        {"name": "external_url", "type": "string", "required": True, "description": "URL для доступа к GitLab"},
        {"name": "smtp_enabled", "type": "bool", "default": False, "description": "Включить отправку email"}
    ]
    
    def validate(self) -> bool:
        external_url = self.config.get("install", {}).get("external_url")
        if not external_url:
            self._validation_error = "external_url is required"
            return False
        return True
    
    def pre_install(self) -> None:
        self.log("Installing dependencies")
        self.system.apt_update()
        self.system.apt_install(["curl", "openssh-server", "ca-certificates", "tzdata", "perl"])
    
    def install(self) -> None:
        self.log("Adding GitLab repository")
        self.system.run([
            "curl", "-fsSL", 
            "https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.deb.sh",
            "-o", "/tmp/gitlab-repo.sh"
        ])
        self.system.run(["bash", "/tmp/gitlab-repo.sh"])
        
        external_url = self.config.get("install", {}).get("external_url", "http://gitlab.local")
        self.log(f"Installing GitLab CE with EXTERNAL_URL={external_url}")
        self.system.run(
            ["apt-get", "install", "-y", "gitlab-ce"],
            check=True
        )
    
    def configure(self) -> None:
        external_url = self.config.get("install", {}).get("external_url", "http://gitlab.local")
        self.log(f"Configuring GitLab with external_url={external_url}")
        
        # Обновляем gitlab.rb
        config_content = f"external_url '{external_url}'\n"
        self.system.write_file("/etc/gitlab/gitlab.rb", config_content)
        
        self.log("Running gitlab-ctl reconfigure")
        self.system.run(["gitlab-ctl", "reconfigure"])
    
    def get_result(self) -> InstallResult:
        external_url = self.config.get("install", {}).get("external_url", "http://gitlab.local")
        return InstallResult(
            success=True,
            message="GitLab CE installed successfully",
            access_url=external_url,
            credentials={"user": "root", "password": "See /etc/gitlab/initial_root_password"}
        )
