"""iRedMail установщик."""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class IRedMailInstaller(AppInstaller):
    name = "iredmail"
    description = "iRedMail Server"
    default_cores = 2
    default_memory = 2048
    default_disk = 15
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.logger.info("Installing prerequisites for iRedMail...")
        self.system.apt_update()
        self.system.apt_install(["wget", "bzip2", "gzip"])
        
        self.logger.info("Downloading iRedMail installer...")
        version = "1.7.2"
        tarball = f"iRedMail-{version}.tar.bz2"
        url = f"https://github.com/iredmail/iRedMail/archive/refs/tags/{version}.tar.gz" # GitHub source is often better
        # Actually iRedMail has its own download server, but GitHub is stable.
        # Let's use the official way if possible.
        
        install_dir = Path("/opt/iredmail")
        self.system.mkdir(install_dir)
        
        self.system.run([
            "wget", f"https://github.com/iredmail/iRedMail/archive/refs/tags/{version}.tar.gz",
            "-O", f"/tmp/iredmail.tar.gz"
        ])
        
        self.system.run(["tar", "-xzf", "/tmp/iredmail.tar.gz", "-C", str(install_dir), "--strip-components=1"])
        
        self.logger.info("iRedMail installer is ready at /opt/iredmail/iRedMail.sh")
        # Мы не запускаем его автоматически в интерактивном режиме, 
        # но подготавливаем всё для запуска пользователем или через конфиг.
        
    def get_result(self) -> InstallResult:
        return InstallResult(
            success=True, 
            message="iRedMail installer downloaded to /opt/iredmail. Please run 'cd /opt/iredmail && bash iRedMail.sh' to complete setup.",
            access_url=None
        )
