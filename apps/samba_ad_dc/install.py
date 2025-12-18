"""Samba AD DC установщик."""
import sys
import os
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class SambaADDCInstaller(AppInstaller):
    name = "samba_ad_dc"
    description = "Samba Active Directory Domain Controller"
    default_cores = 2
    default_memory = 2048
    default_disk = 10
    
    parameters = [
        {"name": "realm", "type": "string", "default": "AD.EXAMPLE.COM", "description": "Kerberos Realm (в верхнем регистре)"},
        {"name": "domain", "type": "string", "default": "AD", "description": "NetBIOS Domain Name"},
        {"name": "password", "type": "string", "default": "Pa$$w0rd123", "description": "Administrator Password"}
    ]
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.log("Updating apt and installing Samba packages...")
        self.system.apt_update()
        
        # Установка без интерактивных запросов
        os.environ["DEBIAN_FRONTEND"] = "noninteractive"
        packages = [
            "samba", "smbclient", "krb5-config", "winbind", "libpam-winbind", 
            "libnss-winbind", "krb5-user", "adcli"
        ]
        self.system.apt_install(packages)
        
        self.log("Stopping and masking conflicting services...")
        for service in ["smbd", "nmbd", "winbind"]:
            self.system.run_command(f"systemctl stop {service} || true")
            self.system.run_command(f"systemctl disable {service} || true")
            self.system.run_command(f"systemctl mask {service} || true")

        self.log("Backing up existing smb.conf...")
        self.system.run_command("mv /etc/samba/smb.conf /etc/samba/smb.conf.bak || true")
        
        realm = self.config.get("realm", "AD.EXAMPLE.COM").upper()
        domain = self.config.get("domain", "AD").upper()
        password = self.config.get("password", "Pa$$w0rd123")
        
        self.log(f"Provisioning domain {realm}...")
        provision_cmd = (
            f"samba-tool domain provision "
            f"--use-rfc2307 "
            f"--realm={realm} "
            f"--domain={domain} "
            f"--server-role=dc "
            f"--dns-backend=SAMBA_INTERNAL "
            f"--adminpass='{password}'"
        )
        self.system.run_command(provision_cmd)
        
        self.log("Configuring Kerberos...")
        self.system.run_command("cp /var/lib/samba/private/krb5.conf /etc/krb5.conf")
        
        self.log("Starting Samba AD DC service...")
        self.system.run_command("systemctl unmask samba-ad-dc || true")
        self.system.systemctl("enable", "samba-ad-dc")
        self.system.systemctl("start", "samba-ad-dc")
    
    def get_result(self) -> InstallResult:
        realm = self.config.get("realm", "AD.EXAMPLE.COM").upper()
        return InstallResult(
            success=True, 
            message="Samba AD DC installed and provisioned successfully",
            credentials={
                "admin_user": "Administrator",
                "realm": realm,
                "domain": self.config.get("domain", "AD").upper()
            }
        )
