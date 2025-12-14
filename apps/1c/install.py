"""1C:Enterprise установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class OneCInstaller(AppInstaller):
    name = "1c"
    description = "1C:Enterprise Server"
    default_cores = 4
    default_memory = 8192
    default_disk = 40
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["libfreetype6", "libgsf-1-114", "libglib2.0-0", "libodbc1", "libmagickwand-6.q16-6"])
        self.log("1C requires manual installation of deb packages from 1C portal")
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="1C base dependencies installed. Install 1C packages manually.", access_url=None)
