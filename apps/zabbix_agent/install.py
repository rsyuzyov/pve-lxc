"""Zabbix Agent установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class ZabbixAgentInstaller(AppInstaller):
    name = "zabbix_agent"
    description = "Zabbix Agent"
    default_cores = 1
    default_memory = 512
    default_disk = 5
    parameters = [
        {
            "name": "server",
            "description": "Zabbix Server address",
            "required": True
        },
        {
            "name": "hostname",
            "description": "Agent hostname",
            "required": False,
            "default": "auto"
        }
    ]
    
    def validate(self) -> bool:
        if not self.config.get("server"):
            self._validation_error = "Zabbix Server address is required"
            return False
        return True
    
    def install(self) -> None:
        # Добавляем репозиторий Zabbix
        self.system.run("wget https://repo.zabbix.com/zabbix/7.0/debian/pool/main/z/zabbix-release/zabbix-release_latest_7.0+debian12_all.deb")
        self.system.run("dpkg -i zabbix-release_latest_7.0+debian12_all.deb")
        self.system.apt_update()
        
        self.system.apt_install(["zabbix-agent2"])
        self.system.systemctl("enable", "zabbix-agent2")
    
    def configure(self) -> None:
        server = self.config.get("server")
        hostname = self.config.get("hostname", "auto")
        
        config_content = f"""Server={server}
ServerActive={server}
Hostname={hostname if hostname != "auto" else "$(hostname)"}
"""
        self.system.write_file("/etc/zabbix/zabbix_agent2.conf", config_content)
        self.system.systemctl("restart", "zabbix-agent2")
    
    def get_result(self) -> InstallResult:
        return InstallResult(
            success=True,
            message="Zabbix Agent installed"
        )
