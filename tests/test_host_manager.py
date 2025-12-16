"""Property-based tests для HostManager."""

import sys
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings

sys.path.insert(0, ".")
from cli.core.host_manager import HostManager
from cli.core.ssh_config import SSHConfigParser
from lib.exceptions import HostNotFoundError


# Стратегии для генерации валидных данных
valid_name = st.from_regex(r"[a-z][a-z0-9\-]{0,15}", fullmatch=True)


# **Feature: remote-pve-hosts, Property 4: Default Host Persistence**
@settings(max_examples=50)
@given(
    names=st.lists(valid_name, min_size=1, max_size=5, unique=True)
)
def test_default_host_persistence(names):
    """Установка default host сохраняется и читается обратно."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssh_config_path = Path(tmpdir) / "ssh_config"
        pve_config_path = Path(tmpdir) / "config.yaml"
        
        ssh_config = SSHConfigParser(ssh_config_path)
        manager = HostManager(ssh_config=ssh_config, config_path=pve_config_path)
        
        # Добавляем хосты
        for i, name in enumerate(names):
            manager.add(name=name, hostname=f"192.168.1.{i+1}")
        
        # Устанавливаем последний как default
        last_name = names[-1]
        manager.set_default(last_name)
        
        # Читаем обратно
        assert manager.get_default() == last_name


@settings(max_examples=30)
@given(
    names=st.lists(valid_name, min_size=2, max_size=5, unique=True)
)
def test_default_host_changes(names):
    """Изменение default host обновляет значение."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssh_config_path = Path(tmpdir) / "ssh_config"
        pve_config_path = Path(tmpdir) / "config.yaml"
        
        ssh_config = SSHConfigParser(ssh_config_path)
        manager = HostManager(ssh_config=ssh_config, config_path=pve_config_path)
        
        # Добавляем хосты
        for i, name in enumerate(names):
            manager.add(name=name, hostname=f"192.168.1.{i+1}")
        
        # Устанавливаем каждый по очереди
        for name in names:
            manager.set_default(name)
            assert manager.get_default() == name


def test_set_default_nonexistent_raises_error():
    """Установка несуществующего хоста как default вызывает ошибку."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssh_config_path = Path(tmpdir) / "ssh_config"
        pve_config_path = Path(tmpdir) / "config.yaml"
        
        ssh_config = SSHConfigParser(ssh_config_path)
        manager = HostManager(ssh_config=ssh_config, config_path=pve_config_path)
        
        try:
            manager.set_default("nonexistent")
            assert False, "Should raise HostNotFoundError"
        except HostNotFoundError as e:
            assert "not found" in str(e)


def test_get_executor_returns_local_when_no_default():
    """get_executor возвращает LocalExecutor когда нет default."""
    from cli.core.executor import LocalExecutor
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ssh_config_path = Path(tmpdir) / "ssh_config"
        pve_config_path = Path(tmpdir) / "config.yaml"
        
        ssh_config = SSHConfigParser(ssh_config_path)
        manager = HostManager(ssh_config=ssh_config, config_path=pve_config_path)
        
        executor = manager.get_executor()
        assert isinstance(executor, LocalExecutor)


def test_get_executor_returns_ssh_for_named_host():
    """get_executor возвращает SSHExecutor для именованного хоста."""
    from cli.core.executor import SSHExecutor
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ssh_config_path = Path(tmpdir) / "ssh_config"
        pve_config_path = Path(tmpdir) / "config.yaml"
        
        ssh_config = SSHConfigParser(ssh_config_path)
        manager = HostManager(ssh_config=ssh_config, config_path=pve_config_path)
        
        manager.add(name="test", hostname="192.168.1.1", user="admin", port=2222)
        
        executor = manager.get_executor("test")
        assert isinstance(executor, SSHExecutor)
        assert executor.host == "192.168.1.1"
        assert executor.user == "admin"
        assert executor.port == 2222


def test_get_executor_raises_for_unknown_host():
    """get_executor вызывает ошибку для неизвестного хоста."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssh_config_path = Path(tmpdir) / "ssh_config"
        pve_config_path = Path(tmpdir) / "config.yaml"
        
        ssh_config = SSHConfigParser(ssh_config_path)
        manager = HostManager(ssh_config=ssh_config, config_path=pve_config_path)
        
        try:
            manager.get_executor("unknown")
            assert False, "Should raise HostNotFoundError"
        except HostNotFoundError as e:
            assert "unknown" in str(e)


def test_remove_default_host_clears_default():
    """Удаление default хоста сбрасывает default."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssh_config_path = Path(tmpdir) / "ssh_config"
        pve_config_path = Path(tmpdir) / "config.yaml"
        
        ssh_config = SSHConfigParser(ssh_config_path)
        manager = HostManager(ssh_config=ssh_config, config_path=pve_config_path)
        
        manager.add(name="test", hostname="192.168.1.1")
        manager.set_default("test")
        assert manager.get_default() == "test"
        
        manager.remove("test")
        assert manager.get_default() is None
