"""MongoDB установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class MongodbInstaller(AppInstaller):
    name = "mongodb"
    description = "MongoDB Database"
    default_cores = 2
    default_memory = 2048
    default_disk = 20
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["gnupg", "curl"])
        self.system.run(["curl", "-fsSL", "https://www.mongodb.org/static/pgp/server-7.0.asc", "-o", "/tmp/mongodb.asc"])
        self.system.run(["gpg", "--dearmor", "-o", "/usr/share/keyrings/mongodb.gpg", "/tmp/mongodb.asc"])
        self.system.run(["bash", "-c", 'echo "deb [signed-by=/usr/share/keyrings/mongodb.gpg] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" > /etc/apt/sources.list.d/mongodb.list'])
        self.system.apt_update()
        self.system.apt_install(["mongodb-org"])
        self.system.systemctl("enable", "mongod")
        self.system.systemctl("start", "mongod")
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="MongoDB installed", access_url=None)
