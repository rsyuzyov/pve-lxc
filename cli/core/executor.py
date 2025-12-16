"""Абстракция выполнения команд: локально или через SSH."""

from abc import ABC, abstractmethod
from pathlib import Path
import shutil
import subprocess

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from lib.system import CommandResult


class CommandExecutor(ABC):
    """Абстракция выполнения команд."""
    
    @abstractmethod
    def run(self, cmd: list[str], check: bool = True) -> CommandResult:
        """Выполнить команду."""
        pass
    
    @abstractmethod
    def push_file(self, local_path: Path, remote_path: Path) -> bool:
        """Скопировать файл на целевую систему."""
        pass
    
    @abstractmethod
    def read_file(self, remote_path: Path) -> str:
        """Прочитать файл с целевой системы."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Освободить ресурсы."""
        pass


class LocalExecutor(CommandExecutor):
    """Локальное выполнение через subprocess."""
    
    def run(self, cmd: list[str], check: bool = True) -> CommandResult:
        """Выполнить команду локально."""
        result = subprocess.run(cmd, capture_output=True, text=True)
        return CommandResult(
            returncode=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or ""
        )
    
    def push_file(self, local_path: Path, remote_path: Path) -> bool:
        """Скопировать файл локально."""
        try:
            remote_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(local_path, remote_path)
            return True
        except Exception:
            return False
    
    def read_file(self, remote_path: Path) -> str:
        """Прочитать локальный файл."""
        return remote_path.read_text()
    
    def close(self) -> None:
        """Ничего не делаем для локального executor."""
        pass


class SSHExecutor(CommandExecutor):
    """Удалённое выполнение через SSH."""
    
    def __init__(
        self, 
        host: str, 
        user: str = "root", 
        port: int = 22, 
        key_path: Path = None
    ):
        self.host = host
        self.user = user
        self.port = port
        self.key_path = key_path
        self._client = None
    
    def _ensure_connected(self) -> None:
        """Установить SSH соединение если не установлено."""
        if self._client is not None:
            return
        
        import paramiko
        from lib.exceptions import ConnectionError, AuthenticationError
        
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        connect_kwargs = {
            "hostname": self.host,
            "port": self.port,
            "username": self.user,
        }
        
        if self.key_path:
            connect_kwargs["key_filename"] = str(self.key_path)
        
        try:
            self._client.connect(**connect_kwargs)
        except paramiko.AuthenticationException:
            self._client = None
            raise AuthenticationError(self.host, self.user)
        except Exception as e:
            self._client = None
            raise ConnectionError(self.host, str(e))
    
    def run(self, cmd: list[str], check: bool = True) -> CommandResult:
        """Выполнить команду через SSH."""
        import shlex
        
        self._ensure_connected()
        
        cmd_str = " ".join(shlex.quote(c) for c in cmd)
        stdin, stdout, stderr = self._client.exec_command(cmd_str)
        
        return CommandResult(
            returncode=stdout.channel.recv_exit_status(),
            stdout=stdout.read().decode(),
            stderr=stderr.read().decode()
        )
    
    def push_file(self, local_path: Path, remote_path: Path) -> bool:
        """Скопировать файл на удалённый хост через SFTP."""
        try:
            self._ensure_connected()
            
            sftp = self._client.open_sftp()
            
            # Создаём родительские директории
            remote_dir = str(remote_path.parent)
            self._mkdir_p(sftp, remote_dir)
            
            sftp.put(str(local_path), str(remote_path))
            sftp.close()
            return True
        except Exception:
            return False
    
    def _mkdir_p(self, sftp, remote_dir: str) -> None:
        """Рекурсивно создать директории на удалённом хосте."""
        if remote_dir == "/" or remote_dir == "":
            return
        
        try:
            sftp.stat(remote_dir)
        except FileNotFoundError:
            self._mkdir_p(sftp, str(Path(remote_dir).parent))
            sftp.mkdir(remote_dir)
    
    def read_file(self, remote_path: Path) -> str:
        """Прочитать файл с удалённого хоста через SFTP."""
        self._ensure_connected()
        
        sftp = self._client.open_sftp()
        with sftp.open(str(remote_path)) as f:
            content = f.read().decode()
        sftp.close()
        return content
    
    def close(self) -> None:
        """Закрыть SSH соединение."""
        if self._client:
            self._client.close()
            self._client = None
