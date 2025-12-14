"""NATS установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class NatsInstaller(AppInstaller):
    name = "nats"
    description = "NATS Message Broker"
    default_cores = 1
    default_memory = 512
    default_disk = 8
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["curl"])
        self.system.run(["curl", "-sL", "https://github.com/nats-io/nats-server/releases/download/v2.10.0/nats-server-v2.10.0-linux-amd64.tar.gz", "-o", "/tmp/nats.tar.gz"])
        self.system.run(["tar", "-xzf", "/tmp/nats.tar.gz", "-C", "/tmp"])
        self.system.run(["mv", "/tmp/nats-server-v2.10.0-linux-amd64/nats-server", "/usr/local/bin/"])
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="NATS installed", access_url=None)
