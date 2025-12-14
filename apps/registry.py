"""Реестр приложений."""

from typing import Optional, Type


class AppRegistry:
    """Реестр установщиков приложений."""
    
    _apps: dict[str, Type] = {}
    
    @classmethod
    def register(cls, installer_class: Type) -> Type:
        """Декоратор для регистрации установщика."""
        name = getattr(installer_class, 'name', installer_class.__name__.lower().replace('installer', ''))
        cls._apps[name] = installer_class
        return installer_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type]:
        """Получить класс установщика по имени."""
        return cls._apps.get(name)
    
    @classmethod
    def list_all(cls) -> list[str]:
        """Список всех зарегистрированных приложений."""
        return sorted(cls._apps.keys())
    
    @classmethod
    def get_help(cls, name: str) -> Optional[str]:
        """Справка по параметрам приложения."""
        installer = cls.get(name)
        if not installer:
            return None
        
        lines = [f"Application: {name}"]
        
        if hasattr(installer, 'description'):
            lines.append(f"Description: {installer.description}")
        
        lines.append("")
        lines.append("Default resources:")
        lines.append(f"  Cores: {getattr(installer, 'default_cores', 2)}")
        lines.append(f"  Memory: {getattr(installer, 'default_memory', 2048)} MB")
        lines.append(f"  Disk: {getattr(installer, 'default_disk', 10)} GB")
        
        # Параметры из config.yaml
        if hasattr(installer, 'parameters'):
            lines.append("")
            lines.append("Parameters:")
            for param in installer.parameters:
                req = " (required)" if param.get('required') else ""
                default = f" [default: {param.get('default')}]" if 'default' in param else ""
                lines.append(f"  --{param['name']}: {param.get('description', '')}{req}{default}")
        
        return "\n".join(lines)
