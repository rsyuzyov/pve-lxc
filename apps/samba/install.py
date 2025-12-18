"""Samba File Server установщик."""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class SambaInstaller(AppInstaller):
    name = "samba"
    description = "Samba File Server with ACL and AD integration support"
    default_cores = 1
    default_memory = 1024
    default_disk = 10
    
    parameters = [
        {"name": "ad_integration", "type": "boolean", "default": False, "description": "Интеграция с Active Directory"},
        {"name": "realm", "type": "string", "default": "", "description": "Kerberos Realm (например, AD.EXAMPLE.COM)"},
        {"name": "domain", "type": "string", "default": "", "description": "NetBIOS Domain Name (например, AD)"},
        {"name": "admin_user", "type": "string", "default": "Administrator", "description": "AD Administrator user"},
        {"name": "admin_password", "type": "string", "default": "", "description": "AD Administrator password"},
        {"name": "share_name", "type": "string", "default": "data", "description": "Имя сетевой шары"},
        {"name": "share_path", "type": "string", "default": "/srv/samba/data", "description": "Путь к сетевой шаре"}
    ]
    
    def validate(self) -> bool:
        if self.config.get("ad_integration"):
            if not self.config.get("realm") or not self.config.get("domain"):
                self._validation_error = "Realm and Domain are required for AD integration"
                return False
            if not self.config.get("admin_password"):
                self._validation_error = "Admin password is required for AD integration"
                return False
        return True
    
    def install(self) -> None:
        self.log("Updating apt and installing Samba packages...")
        self.system.apt_update()
        
        os.environ["DEBIAN_FRONTEND"] = "noninteractive"
        packages = ["samba", "smbclient", "acl", "attr"]
        
        if self.config.get("ad_integration"):
            packages.extend(["winbind", "libpam-winbind", "libnss-winbind", "krb5-user", "adcli"])
            
        self.system.apt_install(packages)
        
        share_path = self.config.get("share_path", "/srv/samba/data")
        self.log(f"Creating share directory: {share_path}")
        self.system.run_command(f"mkdir -p {share_path}")
        self.system.run_command(f"chmod 777 {share_path}")
        
        self.log("Configuring Samba (smb.conf)...")
        self._configure_smb_conf()
        
        if self.config.get("ad_integration"):
            self._join_ad()
            self._configure_nss_pam()
            
        self.log("Restarting Samba services...")
        self.system.systemctl("enable", "smbd")
        self.system.systemctl("restart", "smbd")
        self.system.systemctl("enable", "nmbd")
        self.system.systemctl("restart", "nmbd")
        
        if self.config.get("ad_integration"):
            self.system.systemctl("enable", "winbind")
            self.system.systemctl("restart", "winbind")

    def _configure_smb_conf(self) -> None:
        realm = self.config.get("realm", "").upper()
        domain = self.config.get("domain", "").upper()
        share_name = self.config.get("share_name", "data")
        share_path = self.config.get("share_path", "/srv/samba/data")
        
        smb_conf = [
            "[global]",
            f"   workgroup = {domain or 'WORKGROUP'}",
            "   server string = %h server (Samba, Ubuntu)",
            "   log file = /var/log/samba/log.%m",
            "   max log size = 1000",
            "   logging = file",
            "   panic action = /usr/share/samba/panic-action %d",
            "   server role = standalone server",
            "   obey pam restrictions = yes",
            "   unix password sync = yes",
            "   passwd program = /usr/bin/passwd %u",
            "   passwd chat = *Enter\\snew\\s*\\spassword:* %n\\n *Retype\\snew\\s*\\spassword:* %n\\n *password\\supdated\\ssuccessfully* .",
            "   pam password change = yes",
            "   map to guest = bad user",
            "   usershare allow guests = yes",
            "",
            "   # ACL support",
            "   vfs objects = acl_xattr",
            "   map acl inherit = yes",
            "   store dos attributes = yes",
            ""
        ]
        
        if self.config.get("ad_integration"):
            smb_conf[7] = "   server role = member server"
            smb_conf.extend([
                f"   realm = {realm}",
                "   security = ADS",
                "   winbind refresh tickets = Yes",
                "   vfs objects = acl_xattr", # explicitly repeat if needed, or keep in global
                "",
                "   # Winbind ID mapping",
                "   idmap config * : backend = tdb",
                "   idmap config * : range = 3000-7999",
                f"   idmap config {domain} : backend = rid",
                f"   idmap config {domain} : range = 10000-999999",
                "",
                "   template shell = /bin/bash",
                "   template homedir = /home/%D/%U",
                ""
            ])
            
        smb_conf.extend([
            f"[{share_name}]",
            f"   path = {share_path}",
            "   read only = no",
            "   guest ok = yes",
            "   browseable = yes",
            "   create mask = 0664",
            "   directory mask = 0775"
        ])
        
        conf_content = "\n".join(smb_conf)
        # Using a temporary file to write smb.conf via run_command with heredoc to avoid complex escaping
        temp_file = "/tmp/smb.conf.new"
        self.system.run_command(f"cat <<EOF > {temp_file}\n{conf_content}\nEOF")
        self.system.run_command(f"cp {temp_file} /etc/samba/smb.conf")

    def _join_ad(self) -> None:
        self.log("Joining Active Directory domain...")
        realm = self.config.get("realm", "").upper()
        user = self.config.get("admin_user", "Administrator")
        password = self.config.get("admin_password")
        
        # Configure Kerberos (basic)
        krb5_conf = [
            "[libdefaults]",
            f"    default_realm = {realm}",
            "    dns_lookup_realm = false",
            "    dns_lookup_kdc = true",
            ""
        ]
        self.system.run_command(f"cat <<EOF > /etc/krb5.conf\n{chr(10).join(krb5_conf)}\nEOF")
        
        # Join
        join_cmd = f"echo '{password}' | net ads join -U {user}"
        self.system.run_command(join_cmd)

    def _configure_nss_pam(self) -> None:
        self.log("Configuring NSS and PAM for Winbind...")
        # NSS
        self.system.run_command("sed -i 's/passwd:         files/passwd:         files winbind/' /etc/nsswitch.conf")
        self.system.run_command("sed -i 's/group:          files/group:          files winbind/' /etc/nsswitch.conf")
        # PAM
        self.system.run_command("pam-auth-update --enable winbind")

    def get_result(self) -> InstallResult:
        share_name = self.config.get("share_name", "data")
        return InstallResult(
            success=True,
            message=f"Samba File Server installed. Share [{share_name}] is ready.",
            credentials={
                "ad_integration": self.config.get("ad_integration"),
                "share": share_name
            }
        )
