"""Jenkins установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class JenkinsInstaller(AppInstaller):
    name = "jenkins"
    description = "Jenkins CI/CD Server"
    default_cores = 2
    default_memory = 4096
    default_disk = 20
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["openjdk-17-jdk", "curl", "gnupg"])
        self.system.run(["curl", "-fsSL", "https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key", "-o", "/usr/share/keyrings/jenkins.asc"])
        self.system.run(["bash", "-c", 'echo "deb [signed-by=/usr/share/keyrings/jenkins.asc] https://pkg.jenkins.io/debian-stable binary/" > /etc/apt/sources.list.d/jenkins.list'])
        self.system.apt_update()
        self.system.apt_install(["jenkins"])
        self.system.systemctl("enable", "jenkins")
        self.system.systemctl("start", "jenkins")
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="Jenkins installed", access_url="http://localhost:8080", credentials={"password": "See /var/lib/jenkins/secrets/initialAdminPassword"})
