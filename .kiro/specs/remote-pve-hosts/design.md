# Design Document: Remote PVE Hosts

## Overview

Расширение архитектуры pve-lxc для поддержки удалённого выполнения команд на PVE хостах через SSH. Ключевая идея — абстрагировать выполнение команд от транспорта, чтобы один и тот же код работал как локально, так и удалённо.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      CLI Layer                          │
│  (create, deploy, list, bootstrap, host commands)       │
│                        │                                │
│                   --host flag                           │
└────────────────────────┼────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                    PVE Class                            │
│              (business logic)                           │
│                        │                                │
│              CommandExecutor                            │
└────────────────────────┼────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
┌─────────▼─────────┐       ┌───────────▼───────────┐
│  LocalExecutor    │       │   SSHExecutor         │
│  (subprocess)     │       │   (paramiko/fabric)   │
└───────────────────┘       └───────────────────────┘
```

## Components and Interfaces

### 1. CommandExecutor (Abstract Base)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    
    @property
    def success(self) -> bool:
        return self.returncode == 0

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
```

### 2. LocalExecutor

```python
class LocalExecutor(CommandExecutor):
    """Локальное выполнение через subprocess."""
    
    def run(self, cmd: list[str], check: bool = True) -> CommandResult:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return CommandResult(
            returncode=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or ""
        )
    
    def push_file(self, local_path: Path, remote_path: Path) -> bool:
        shutil.copy(local_path, remote_path)
        return True
    
    def read_file(self, remote_path: Path) -> str:
        return remote_path.read_text()
```

### 3. SSHExecutor

```python
import paramiko

class SSHExecutor(CommandExecutor):
    """Удалённое выполнение через SSH."""
    
    def __init__(self, host: str, user: str = "root", 
                 port: int = 22, key_path: Path = None):
        self.host = host
        self.user = user
        self.port = port
        self.key_path = key_path
        self._client: paramiko.SSHClient = None
    
    def connect(self) -> None:
        """Установить SSH соединение."""
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(
            hostname=self.host,
            port=self.port,
            username=self.user,
            key_filename=str(self.key_path) if self.key_path else None
        )
    
    def run(self, cmd: list[str], check: bool = True) -> CommandResult:
        if not self._client:
            self.connect()
        
        cmd_str = " ".join(shlex.quote(c) for c in cmd)
        stdin, stdout, stderr = self._client.exec_command(cmd_str)
        
        return CommandResult(
            returncode=stdout.channel.recv_exit_status(),
            stdout=stdout.read().decode(),
            stderr=stderr.read().decode()
        )
    
    def push_file(self, local_path: Path, remote_path: Path) -> bool:
        if not self._client:
            self.connect()
        
        sftp = self._client.open_sftp()
        sftp.put(str(local_path), str(remote_path))
        sftp.close()
        return True
    
    def read_file(self, remote_path: Path) -> str:
        if not self._client:
            self.connect()
        
        sftp = self._client.open_sftp()
        with sftp.open(str(remote_path)) as f:
            content = f.read().decode()
        sftp.close()
        return content
    
    def close(self) -> None:
        if self._client:
            self._client.close()
```

### 4. SSHConfigParser

```python
class SSHConfigParser:
    """Парсер и редактор SSH config."""
    
    def __init__(self, config_path: Path = None):
        self.config_path = config_path or Path.home() / ".ssh" / "config"
    
    def list_hosts(self) -> list[dict]:
        """Получить список хостов из SSH config."""
        pass
    
    def get_host(self, name: str) -> dict | None:
        """Получить параметры хоста."""
        pass
    
    def add_host(self, name: str, hostname: str, 
                 user: str = "root", port: int = 22,
                 identity_file: str = None) -> None:
        """Добавить хост в SSH config."""
        pass
    
    def remove_host(self, name: str) -> bool:
        """Удалить хост из SSH config."""
        pass
```

### 5. HostManager

```python
class HostManager:
    """Управление PVE хостами."""
    
    def __init__(self, ssh_config: SSHConfigParser, 
                 app_config: ConfigLoader):
        self.ssh_config = ssh_config
        self.app_config = app_config
    
    def add(self, name: str, hostname: str, **kwargs) -> None:
        """Добавить хост."""
        self.ssh_config.add_host(name, hostname, **kwargs)
    
    def remove(self, name: str) -> None:
        """Удалить хост."""
        self.ssh_config.remove_host(name)
    
    def list(self) -> list[dict]:
        """Список хостов."""
        return self.ssh_config.list_hosts()
    
    def test(self, name: str) -> dict:
        """Проверить подключение и PVE."""
        executor = self.get_executor(name)
        result = executor.run(["pveversion"])
        return {
            "connected": result.success,
            "pve_version": result.stdout.strip() if result.success else None
        }
    
    def get_executor(self, name: str = None) -> CommandExecutor:
        """Получить executor для хоста."""
        if not name:
            name = self.app_config.get("default_host")
        
        if not name:
            return LocalExecutor()
        
        host_config = self.ssh_config.get_host(name)
        if not host_config:
            raise ValueError(f"Host '{name}' not found in SSH config")
        
        return SSHExecutor(
            host=host_config["hostname"],
            user=host_config.get("user", "root"),
            port=host_config.get("port", 22),
            key_path=host_config.get("identityfile")
        )
    
    def set_default(self, name: str) -> None:
        """Установить хост по умолчанию."""
        # Сохраняем в ~/.pve-lxc/config.yaml
        pass
```

### 6. Модификация PVE класса

```python
class PVE:
    """Работа с Proxmox VE."""

    def __init__(self, logger: Logger, executor: CommandExecutor = None):
        self.logger = logger
        self.executor = executor or LocalExecutor()

    def _run(self, cmd: list[str], check: bool = True) -> CommandResult:
        """Выполнить команду через executor."""
        self.logger.debug(f"PVE: {' '.join(cmd)}")
        return self.executor.run(cmd, check)
    
    # Остальные методы без изменений — они используют _run()
```

## Data Models

### Host Configuration (в SSH config)

```
Host pve1
    HostName 192.168.1.10
    User root
    Port 22
    IdentityFile ~/.ssh/id_rsa

Host pve2
    HostName 192.168.1.11
    User root
```

### App Configuration (в ~/.pve-lxc/config.yaml)

```yaml
default_host: pve1

container:
  cores: 2
  memory: 2048
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: SSH Config Round Trip
*For any* valid host configuration (name, hostname, user, port, identity_file), adding it to SSH config and then reading it back SHALL produce equivalent values.
**Validates: Requirements 3.1**

### Property 2: Executor Command Equivalence
*For any* PVE command and its arguments, executing via LocalExecutor on a PVE host SHALL produce the same result as executing via SSHExecutor connected to that same host.
**Validates: Requirements 4.1**

### Property 3: Host List Consistency
*For any* sequence of host add and remove operations, the host list SHALL contain exactly the hosts that were added and not subsequently removed.
**Validates: Requirements 2.2, 3.1, 3.2**

### Property 4: Default Host Persistence
*For any* host name set as default, subsequent reads of the default host configuration SHALL return that same host name until changed.
**Validates: Requirements 2.4**

### Property 5: File Transfer Integrity
*For any* file content, pushing a file via SSHExecutor and reading it back SHALL produce identical content.
**Validates: Requirements 4.2**

## Error Handling

| Scenario | Error | Action |
|----------|-------|--------|
| SSH connection failed | `ConnectionError` | Показать хост, порт, причину |
| Host not in SSH config | `HostNotFoundError` | Показать список доступных хостов |
| PVE tools not found on host | `PVENotFoundError` | Предложить проверить установку PVE |
| SSH config parse error | `ConfigError` | Показать строку с ошибкой |
| Permission denied | `AuthenticationError` | Предложить проверить ключ/пароль |

## Testing Strategy

### Property-Based Testing

Используем **Hypothesis** для Python:

1. **SSH Config Round Trip** — генерируем случайные валидные конфигурации хостов, записываем в SSH config, читаем обратно, проверяем эквивалентность
2. **Host List Consistency** — генерируем последовательности add/remove операций, проверяем финальное состояние
3. **Default Host Persistence** — генерируем последовательности set_default, проверяем что последнее значение сохраняется

### Unit Tests

1. SSHConfigParser — парсинг различных форматов SSH config
2. SSHExecutor — mock-тесты подключения и выполнения команд
3. HostManager — интеграция компонентов
4. CLI commands — проверка аргументов и вывода

### Integration Tests

1. Реальное подключение к тестовому PVE хосту (если доступен)
2. End-to-end тест: add host → test → create container → destroy
