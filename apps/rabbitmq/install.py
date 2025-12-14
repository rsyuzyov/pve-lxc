"""RabbitMQ установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class RabbitmqInstaller(AppInstaller):
    name = "rabbitmq"
    description = "RabbitMQ Message Broker"
    default_cores = 2
    default_memory = 2048
    default_disk = 10
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["rabbitmq-server"])
        self.system.systemctl("enable", "rabbitmq-server")
        self.system.systemctl("start", "rabbitmq-server")
        self.system.run(["rabbitmq-plugins", "enable", "rabbitmq_management"])
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="RabbitMQ installed", access_url="http://localhost:15672", credentials={"user": "guest", "password": "guest"})
