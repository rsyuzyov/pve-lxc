"""Zabbix Proxy установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class ZabbixProxyInstaller(AppInstaller):
    name = "zabbix_proxy"
    description = "Zabbix Proxy"
    default_cores = 2
    default_memory = 2048
    default_disk = 20
    parameters = [
        {
            "name": "server",
            "description": "Zabbix Server address",
            "required": True
        },
        {
            "name": "hostname",
            "description": "Proxy hostname",
            "required": True
        },
        {
            "name": "mode",
            "description": "Proxy mode (active/passive)",
            "required": False,
            "default": "active"
        }
    ]
    
    def validate(self) -> bool:
        if not self.config.get("server"):
            self._validation_error = "Zabbix Server address is required"
            return False
        if not self.config.get("hostname"):
            self._validation_error = "Proxy hostname is required"
            return False
        return True
    
    def install(self) -> None:
        # Добавляем репозиторий Zabbix
        self.system.run("wget https://repo.zabbix.com/zabbix/7.0/debian/pool/main/z/zabbix-release/zabbix-release_latest_7.0+debian12_all.deb")
        self.system.run("dpkg -i zabbix-release_latest_7.0+debian12_all.deb")
        self.system.apt_update()
        
        self.system.apt_install(["zabbix-proxy-sqlite3"])
        self.system.systemctl("enable", "zabbix-proxy")
    
    def configure(self) -> None:
        server = self.config.get("server")
        hostname = self.config.get("hostname")
        mode = self.config.get("mode", "active")
        
        proxy_mode = "0" if mode == "active" else "1"
        
        config_content = f"""Server={server}
Hostname={hostname}
ProxyMode={proxy_mode}
DBName=/var/lib/zabbix/zabbix_proxy.db
"""
        self.system.write_file("/etc/zabbix/zabbix_proxy.conf", config_content)
        self.system.systemctl("start", "zabbix-proxy")
    
    def get_result(self) -> InstallResult:
        return InstallResult(
            success=True,
            message="Zabbix Proxy installed"
        )
