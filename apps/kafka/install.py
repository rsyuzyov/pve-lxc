"""Kafka установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class KafkaInstaller(AppInstaller):
    name = "kafka"
    description = "Apache Kafka"
    default_cores = 2
    default_memory = 4096
    default_disk = 20
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["openjdk-17-jdk", "curl"])
        self.system.run(["curl", "-sL", "https://downloads.apache.org/kafka/3.7.0/kafka_2.13-3.7.0.tgz", "-o", "/tmp/kafka.tgz"])
        self.system.run(["tar", "-xzf", "/tmp/kafka.tgz", "-C", "/opt"])
        self.system.run(["ln", "-s", "/opt/kafka_2.13-3.7.0", "/opt/kafka"])
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="Kafka installed", access_url=None)
