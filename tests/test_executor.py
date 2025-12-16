"""Property-based tests для CommandExecutor."""

import sys
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings

sys.path.insert(0, ".")
from cli.core.executor import LocalExecutor


# **Feature: remote-pve-hosts, Property 2: Executor Command Equivalence (partial - local)**
@settings(max_examples=100)
@given(
    exit_code=st.integers(min_value=0, max_value=255)
)
def test_local_executor_returns_correct_exit_code(exit_code):
    """LocalExecutor возвращает корректный exit code."""
    executor = LocalExecutor()
    result = executor.run(["bash", "-c", f"exit {exit_code}"])
    assert result.returncode == exit_code
    assert result.success == (exit_code == 0)


@settings(max_examples=100)
@given(
    output=st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S'),
        whitelist_characters=' '
    ))
)
def test_local_executor_captures_stdout(output):
    """LocalExecutor корректно захватывает stdout."""
    executor = LocalExecutor()
    # Используем printf для точного вывода без newline
    result = executor.run(["printf", "%s", output])
    assert result.success
    assert result.stdout == output


@settings(max_examples=100)
@given(
    error=st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=('L', 'N'),
        whitelist_characters=' _-'
    ))
)
def test_local_executor_captures_stderr(error):
    """LocalExecutor корректно захватывает stderr."""
    import base64
    executor = LocalExecutor()
    # Используем base64 для безопасной передачи любого текста
    encoded = base64.b64encode(error.encode()).decode()
    result = executor.run(["bash", "-c", f"echo -n {encoded} | base64 -d >&2"])
    assert result.stderr == error


# **Feature: remote-pve-hosts, Property 5: File Transfer Integrity (local)**
@settings(max_examples=50)
@given(
    content=st.text(min_size=0, max_size=1000)
)
def test_local_executor_file_roundtrip(content):
    """Запись и чтение файла через LocalExecutor сохраняет содержимое."""
    executor = LocalExecutor()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = Path(tmpdir) / "source.txt"
        dst_path = Path(tmpdir) / "dest.txt"
        
        # Записываем исходный файл (binary mode для сохранения \r)
        src_path.write_bytes(content.encode('utf-8'))
        
        # Копируем через executor
        assert executor.push_file(src_path, dst_path)
        
        # Читаем через executor (binary mode)
        read_content = dst_path.read_bytes().decode('utf-8')
        
        assert read_content == content


def test_local_executor_push_creates_parent_dirs():
    """push_file создаёт родительские директории."""
    executor = LocalExecutor()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = Path(tmpdir) / "source.txt"
        dst_path = Path(tmpdir) / "nested" / "deep" / "dest.txt"
        
        src_path.write_text("test content")
        
        assert executor.push_file(src_path, dst_path)
        assert dst_path.exists()
        assert dst_path.read_text() == "test content"


def test_local_executor_close_is_noop():
    """close() не вызывает ошибок."""
    executor = LocalExecutor()
    executor.close()  # Не должно падать


# **Feature: remote-pve-hosts, Property 5: File Transfer Integrity (SSH)**
# Этот тест требует SSH доступа к localhost
import pytest
import os

@pytest.mark.skipif(
    not os.path.exists(os.path.expanduser("~/.ssh/id_rsa")),
    reason="SSH key not found, skipping SSH tests"
)
class TestSSHExecutor:
    """Тесты SSHExecutor (требуют SSH к localhost)."""
    
    @settings(max_examples=20, deadline=None)
    @given(
        content=st.text(min_size=0, max_size=500, alphabet=st.characters(
            whitelist_categories=('L', 'N', 'P'),
            whitelist_characters=' \n\t'
        ))
    )
    def test_ssh_executor_file_roundtrip(self, content):
        """Запись и чтение файла через SSHExecutor сохраняет содержимое."""
        from cli.core.executor import SSHExecutor
        
        executor = SSHExecutor(host="localhost", user=os.environ.get("USER", "root"))
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                src_path = Path(tmpdir) / "source.txt"
                dst_path = Path(tmpdir) / "dest_ssh.txt"
                
                # Записываем исходный файл
                src_path.write_bytes(content.encode('utf-8'))
                
                # Копируем через SSH executor
                assert executor.push_file(src_path, dst_path)
                
                # Читаем через SSH executor
                read_content = executor.read_file(dst_path)
                
                assert read_content == content
        finally:
            executor.close()
    
    def test_ssh_executor_run_command(self):
        """SSHExecutor выполняет команды через SSH."""
        from cli.core.executor import SSHExecutor
        
        executor = SSHExecutor(host="localhost", user=os.environ.get("USER", "root"))
        
        try:
            result = executor.run(["echo", "hello"])
            assert result.success
            assert result.stdout.strip() == "hello"
        finally:
            executor.close()
    
    def test_ssh_executor_exit_code(self):
        """SSHExecutor возвращает корректный exit code."""
        from cli.core.executor import SSHExecutor
        
        executor = SSHExecutor(host="localhost", user=os.environ.get("USER", "root"))
        
        try:
            result = executor.run(["bash", "-c", "exit 42"])
            assert result.returncode == 42
            assert not result.success
        finally:
            executor.close()
