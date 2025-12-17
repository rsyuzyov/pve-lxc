"""Zabbix Server установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class ZabbixInstaller(AppInstaller):
    name = "zabbix"
    description = "Zabbix Server"
    default_cores = 2
    default_memory = 4096
    default_disk = 30
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        # Добавляем репозиторий Zabbix
        self.system.run("wget https://repo.zabbix.com/zabbix/7.0/debian/pool/main/z/zabbix-release/zabbix-release_latest_7.0+debian12_all.deb")
        self.system.run("dpkg -i zabbix-release_latest_7.0+debian12_all.deb")
        self.system.apt_update()
        
        # Устанавливаем Zabbix Server, frontend, agent
        self.system.apt_install([
            "zabbix-server-pgsql",
            "zabbix-frontend-php",
            "zabbix-nginx-conf",
            "zabbix-sql-scripts",
            "zabbix-agent",
            "postgresql"
        ])
        
        self.system.systemctl("enable", "zabbix-server")
        self.system.systemctl("enable", "zabbix-agent")
        self.system.systemctl("enable", "nginx")
        self.system.systemctl("enable", "php8.2-fpm")
    
    def post_install(self) -> None:
        # Создаём базу данных
        self.system.run("sudo -u postgres createuser --pwprompt zabbix || true")
        self.system.run("sudo -u postgres createdb -O zabbix zabbix || true")
        self.system.run("zcat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | sudo -u zabbix psql zabbix || true")
    
    def configure(self) -> None:
        self.system.systemctl("start", "zabbix-server")
        self.system.systemctl("start", "zabbix-agent")
        self.system.systemctl("start", "nginx")
        self.system.systemctl("start", "php8.2-fpm")
    
    def get_result(self) -> InstallResult:
        return InstallResult(
            success=True,
            message="Zabbix Server installed",
            access_url="http://localhost/zabbix",
            credentials={"user": "Admin", "password": "zabbix"}
        )
