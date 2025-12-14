"""GitLab Runner установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class GitlabRunnerInstaller(AppInstaller):
    name = "gitlab-runner"
    description = "GitLab Runner"
    default_cores = 2
    default_memory = 2048
    default_disk = 20
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["curl"])
        self.system.run(["curl", "-L", "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh", "-o", "/tmp/runner.sh"])
        self.system.run(["bash", "/tmp/runner.sh"])
        self.system.apt_install(["gitlab-runner"])
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="GitLab Runner installed. Run: gitlab-runner register", access_url=None)
