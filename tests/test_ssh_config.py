"""Property-based tests для SSHConfigParser."""

import sys
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume

sys.path.insert(0, ".")
from cli.core.ssh_config import SSHConfigParser, SSHConfigError


# Стратегии для генерации валидных данных
valid_hostname = st.from_regex(r"[a-z][a-z0-9\-]{0,20}", fullmatch=True)
valid_name = st.from_regex(r"[a-z][a-z0-9\-]{0,15}", fullmatch=True)
valid_user = st.from_regex(r"[a-z][a-z0-9_]{0,10}", fullmatch=True)
valid_port = st.integers(min_value=1, max_value=65535)


# **Feature: remote-pve-hosts, Property 1: SSH Config Round Trip**
@settings(max_examples=100)
@given(
    name=valid_name,
    hostname=valid_hostname,
    user=valid_user,
    port=valid_port
)
def test_ssh_config_round_trip(name, hostname, user, port):
    """Добавление хоста и чтение обратно возвращает эквивалентные значения."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config"
        parser = SSHConfigParser(config_path)
        
        # Добавляем хост
        parser.add_host(name=name, hostname=hostname, user=user, port=port)
        
        # Читаем обратно
        host = parser.get_host(name)
        
        assert host is not None
        assert host["name"] == name
        assert host["hostname"] == hostname
        assert host["user"] == user
        assert host["port"] == str(port)


# **Feature: remote-pve-hosts, Property 3: Host List Consistency**
@settings(max_examples=50)
@given(
    names=st.lists(valid_name, min_size=1, max_size=10, unique=True)
)
def test_host_list_after_adds(names):
    """После добавления N хостов, list_hosts возвращает N хостов."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config"
        parser = SSHConfigParser(config_path)
        
        # Добавляем все хосты
        for i, name in enumerate(names):
            parser.add_host(
                name=name, 
                hostname=f"192.168.1.{i+1}", 
                user="root", 
                port=22
            )
        
        # Проверяем список
        hosts = parser.list_hosts()
        host_names = {h["name"] for h in hosts}
        
        assert host_names == set(names)


@settings(max_examples=50)
@given(
    names=st.lists(valid_name, min_size=2, max_size=10, unique=True),
    remove_indices=st.data()
)
def test_host_list_after_removes(names, remove_indices):
    """После удаления хостов, они не появляются в списке."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config"
        parser = SSHConfigParser(config_path)
        
        # Добавляем все хосты
        for i, name in enumerate(names):
            parser.add_host(
                name=name, 
                hostname=f"192.168.1.{i+1}", 
                user="root", 
                port=22
            )
        
        # Выбираем случайные хосты для удаления
        num_to_remove = remove_indices.draw(st.integers(min_value=1, max_value=len(names)-1))
        to_remove = set(names[:num_to_remove])
        
        # Удаляем
        for name in to_remove:
            parser.remove_host(name)
        
        # Проверяем список
        hosts = parser.list_hosts()
        host_names = {h["name"] for h in hosts}
        
        expected = set(names) - to_remove
        assert host_names == expected


def test_add_duplicate_host_raises_error():
    """Добавление хоста с существующим именем вызывает ошибку."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config"
        parser = SSHConfigParser(config_path)
        
        parser.add_host(name="test", hostname="192.168.1.1", user="root", port=22)
        
        try:
            parser.add_host(name="test", hostname="192.168.1.2", user="root", port=22)
            assert False, "Should raise SSHConfigError"
        except SSHConfigError as e:
            assert "already exists" in str(e)


def test_remove_nonexistent_host_returns_false():
    """Удаление несуществующего хоста возвращает False."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config"
        parser = SSHConfigParser(config_path)
        
        result = parser.remove_host("nonexistent")
        assert result is False


def test_get_nonexistent_host_returns_none():
    """Получение несуществующего хоста возвращает None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config"
        parser = SSHConfigParser(config_path)
        
        result = parser.get_host("nonexistent")
        assert result is None


def test_identity_file_is_saved():
    """IdentityFile сохраняется в конфиге."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config"
        parser = SSHConfigParser(config_path)
        
        parser.add_host(
            name="test", 
            hostname="192.168.1.1", 
            user="root", 
            port=22,
            identity_file="~/.ssh/my_key"
        )
        
        host = parser.get_host("test")
        assert host["identityfile"] == "~/.ssh/my_key"
