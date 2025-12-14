"""MotionEye установщик."""
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class MotioneyeInstaller(AppInstaller):
    name = "motioneye"
    description = "MotionEye Video Surveillance"
    default_cores = 2
    default_memory = 2048
    default_disk = 20
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        self.system.apt_update()
        self.system.apt_install(["motion", "python3-pip", "python3-dev", "libcurl4-openssl-dev", "libssl-dev", "libjpeg-dev"])
        self.system.run(["pip3", "install", "motioneye", "--break-system-packages"])
    
    def get_result(self) -> InstallResult:
        return InstallResult(success=True, message="MotionEye installed", access_url="http://localhost:8765", credentials={"user": "admin", "password": ""})
