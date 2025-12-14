"""Property-based tests для Apps framework."""

import sys
from hypothesis import given, strategies as st, settings

sys.path.insert(0, ".")
from apps.registry import AppRegistry
from apps.base import AppInstaller, InstallResult
from lib.logger import Logger
from lib.system import System


# Создаём тестовый установщик
class MockInstaller(AppInstaller):
    name = "test"
    description = "Test application"
    default_cores = 2
    default_memory = 2048
    default_disk = 10
    parameters = [
        {"name": "param1", "type": "string", "required": True, "description": "Test param"},
        {"name": "param2", "type": "int", "default": 42, "description": "Optional param"}
    ]
    
    def __init__(self, logger, system, config, should_fail_validation=False):
        super().__init__(logger, system, config)
        self.should_fail_validation = should_fail_validation
        self.call_order = []
    
    def validate(self) -> bool:
        self.call_order.append("validate")
        if self.should_fail_validation:
            self._validation_error = "Test validation error"
            return False
        return True
    
    def pre_install(self) -> None:
        self.call_order.append("pre_install")
    
    def install(self) -> None:
        self.call_order.append("install")
    
    def post_install(self) -> None:
        self.call_order.append("post_install")
    
    def configure(self) -> None:
        self.call_order.append("configure")
    
    def get_result(self) -> InstallResult:
        self.call_order.append("get_result")
        return InstallResult(
            success=True,
            message="Test installed",
            access_url="http://localhost:8080"
        )


# Регистрируем тестовый установщик
AppRegistry.register(MockInstaller)


# **Feature: pve-lxc-v2, Property 10: Список приложений полный**
def test_apps_list_complete():
    """Список приложений должен содержать все зарегистрированные."""
    apps = AppRegistry.list_all()
    assert "test" in apps
    
    # Проверяем что все приложения из списка можно получить
    for app_name in apps:
        installer = AppRegistry.get(app_name)
        assert installer is not None


# **Feature: pve-lxc-v2, Property 11: Справка приложения содержит параметры**
def test_app_help_contains_parameters():
    """Справка должна содержать все параметры из config."""
    help_text = AppRegistry.get_help("test")
    
    assert help_text is not None
    assert "param1" in help_text
    assert "param2" in help_text
    assert "Test param" in help_text
    assert "default: 42" in help_text


# **Feature: pve-lxc-v2, Property 8: Порядок вызовов AppInstaller**
def test_app_installer_call_order():
    """Методы должны вызываться в порядке: validate → pre_install → install → post_install → configure."""
    logger = Logger(json_output=True)
    system = System(logger)
    
    installer = MockInstaller(logger, system, {}, should_fail_validation=False)
    result = installer.run()
    
    assert result.success
    expected_order = ["validate", "pre_install", "install", "post_install", "configure", "get_result"]
    assert installer.call_order == expected_order


# **Feature: pve-lxc-v2, Property 9: Прерывание при ошибке валидации**
def test_app_installer_stops_on_validation_error():
    """При ошибке валидации остальные методы не должны вызываться."""
    logger = Logger(json_output=True)
    system = System(logger)
    
    installer = MockInstaller(logger, system, {}, should_fail_validation=True)
    result = installer.run()
    
    assert not result.success
    assert installer.call_order == ["validate"]
    assert "pre_install" not in installer.call_order
    assert "install" not in installer.call_order


# **Feature: pve-lxc-v2, Property 14: InstallResult при успехе содержит access_url**
def test_install_result_success_has_access_url():
    """При успешной установке access_url не должен быть None."""
    logger = Logger(json_output=True)
    system = System(logger)
    
    installer = MockInstaller(logger, system, {})
    result = installer.run()
    
    assert result.success
    assert result.access_url is not None


# **Feature: pve-lxc-v2, Property 15: InstallResult при ошибке содержит log_path**
def test_install_result_failure_has_log_path():
    """При неуспешной установке log_path должен быть указан."""
    logger = Logger(json_output=True)
    system = System(logger)
    
    installer = MockInstaller(lrun-in-lxcogger, system, {}, should_fail_validation=True)
    result = installer.run()
    
    assert not result.success
    assert result.log_path is not None
