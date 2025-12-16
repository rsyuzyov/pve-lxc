"""Пользовательские исключения для pve-lxc."""


class PVELXCError(Exception):
    """Базовое исключение для pve-lxc."""
    pass


class HostNotFoundError(PVELXCError):
    """Хост не найден в SSH config."""
    
    def __init__(self, host: str, available: list[str] = None):
        self.host = host
        self.available = available or []
        
        msg = f"Host '{host}' not found"
        if self.available:
            msg += f". Available hosts: {', '.join(self.available)}"
        
        super().__init__(msg)


class ConnectionError(PVELXCError):
    """Ошибка подключения к хосту."""
    
    def __init__(self, host: str, reason: str = None):
        self.host = host
        self.reason = reason
        
        msg = f"Failed to connect to '{host}'"
        if reason:
            msg += f": {reason}"
        
        super().__init__(msg)


class PVENotFoundError(PVELXCError):
    """PVE tools не найдены на хосте."""
    
    def __init__(self, host: str):
        self.host = host
        super().__init__(
            f"PVE tools not found on '{host}'. "
            "Make sure Proxmox VE is installed."
        )


class AuthenticationError(PVELXCError):
    """Ошибка аутентификации SSH."""
    
    def __init__(self, host: str, user: str):
        self.host = host
        self.user = user
        super().__init__(
            f"Authentication failed for {user}@{host}. "
            "Check SSH key or password."
        )
