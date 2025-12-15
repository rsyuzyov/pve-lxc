"""Supabase установщик."""

import secrets
import string
from pathlib import Path

import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])

from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry


@AppRegistry.register
class SupabaseInstaller(AppInstaller):
    name = "supabase"
    description = "Supabase - Open Source Firebase Alternative"
    default_cores = 4
    default_memory = 4096
    default_disk = 30
    parameters = [
        {"name": "domain", "type": "string", "required": True, "description": "Домен для Supabase"},
        {"name": "jwt_secret", "type": "string", "required": False, "description": "JWT секрет"},
        {"name": "postgres_password", "type": "string", "required": False, "description": "Пароль PostgreSQL"},
        {"name": "dashboard_password", "type": "string", "required": False, "description": "Пароль Studio"},
    ]
    
    SUPABASE_DIR = Path("/opt/supabase")
    
    def _generate_secret(self, length: int = 32) -> str:
        """Генерация случайного секрета."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def _generate_jwt_secret(self) -> str:
        """Генерация JWT секрета (минимум 32 символа)."""
        return self._generate_secret(64)
    
    def validate(self) -> bool:
        domain = self.config.get("domain")
        if not domain:
            self._validation_error = "Parameter 'domain' is required"
            return False
        return True
    
    def pre_install(self) -> None:
        """Установка Docker если не установлен."""
        result = self.system.run(["which", "docker"], check=False)
        if result.returncode != 0:
            self.log("Docker not found, installing...")
            self._install_docker()
    
    def _install_docker(self) -> None:
        """Установка Docker."""
        self.system.apt_update()
        self.system.apt_install(["ca-certificates", "curl", "gnupg"])
        self.system.run(["install", "-m", "0755", "-d", "/etc/apt/keyrings"])
        self.system.run([
            "curl", "-fsSL", "https://download.docker.com/linux/debian/gpg",
            "-o", "/etc/apt/keyrings/docker.asc"
        ])
        self.system.run(["bash", "-c",
            'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] '
            'https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" '
            '> /etc/apt/sources.list.d/docker.list'
        ])
        self.system.apt_update()
        self.system.apt_install(["docker-ce", "docker-ce-cli", "containerd.io", "docker-compose-plugin"])
        self.system.systemctl("enable", "docker")
        self.system.systemctl("start", "docker")

    def install(self) -> None:
        """Клонирование и настройка Supabase."""
        self.log("Cloning Supabase repository...")
        
        self.SUPABASE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Клонируем официальный docker репозиторий
        self.system.run([
            "git", "clone", "--depth", "1",
            "https://github.com/supabase/supabase.git",
            str(self.SUPABASE_DIR / "repo")
        ])
        
        # Копируем docker конфиги
        docker_dir = self.SUPABASE_DIR / "repo" / "docker"
        self.system.run(["cp", "-r", str(docker_dir / "."), str(self.SUPABASE_DIR)])
        
        self._configure_env()
    
    def _configure_env(self) -> None:
        """Настройка .env файла."""
        self.log("Configuring environment...")
        
        domain = self.config.get("domain")
        jwt_secret = self.config.get("jwt_secret") or self._generate_jwt_secret()
        postgres_password = self.config.get("postgres_password") or self._generate_secret(24)
        dashboard_password = self.config.get("dashboard_password") or self._generate_secret(16)
        anon_key = self._generate_secret(32)
        service_key = self._generate_secret(32)
        
        # Сохраняем credentials
        self._credentials = {
            "jwt_secret": jwt_secret,
            "postgres_password": postgres_password,
            "dashboard_password": dashboard_password,
            "anon_key": anon_key,
            "service_key": service_key,
        }
        
        env_example = self.SUPABASE_DIR / ".env.example"
        env_file = self.SUPABASE_DIR / ".env"
        
        if env_example.exists():
            content = env_example.read_text()
        else:
            content = self._get_default_env()
        
        # Заменяем значения
        replacements = {
            "POSTGRES_PASSWORD=": f"POSTGRES_PASSWORD={postgres_password}",
            "JWT_SECRET=": f"JWT_SECRET={jwt_secret}",
            "ANON_KEY=": f"ANON_KEY={anon_key}",
            "SERVICE_ROLE_KEY=": f"SERVICE_ROLE_KEY={service_key}",
            "DASHBOARD_PASSWORD=": f"DASHBOARD_PASSWORD={dashboard_password}",
            "SITE_URL=": f"SITE_URL=https://{domain}",
            "API_EXTERNAL_URL=": f"API_EXTERNAL_URL=https://{domain}",
            "SUPABASE_PUBLIC_URL=": f"SUPABASE_PUBLIC_URL=https://{domain}",
        }
        
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            replaced = False
            for key, value in replacements.items():
                if line.startswith(key):
                    new_lines.append(value)
                    replaced = True
                    break
            if not replaced:
                new_lines.append(line)
        
        env_file.write_text('\n'.join(new_lines))
        
        # SMTP настройки если указаны
        smtp_host = self.config.get("smtp_host")
        if smtp_host:
            self._configure_smtp()
    
    def _configure_smtp(self) -> None:
        """Настройка SMTP."""
        env_file = self.SUPABASE_DIR / ".env"
        content = env_file.read_text()
        
        smtp_config = f"""
SMTP_HOST={self.config.get('smtp_host', '')}
SMTP_PORT={self.config.get('smtp_port', 587)}
SMTP_USER={self.config.get('smtp_user', '')}
SMTP_PASS={self.config.get('smtp_pass', '')}
"""
        env_file.write_text(content + smtp_config)
    
    def _get_default_env(self) -> str:
        """Базовый .env если example не найден."""
        return """############
# Secrets
############
POSTGRES_PASSWORD=
JWT_SECRET=
ANON_KEY=
SERVICE_ROLE_KEY=
DASHBOARD_PASSWORD=

############
# URLs
############
SITE_URL=http://localhost:3000
API_EXTERNAL_URL=http://localhost:8000
SUPABASE_PUBLIC_URL=http://localhost:8000

############
# Database
############
POSTGRES_HOST=db
POSTGRES_DB=postgres
POSTGRES_PORT=5432

############
# Studio
############
STUDIO_PORT=3000
"""
    
    def post_install(self) -> None:
        """Запуск Supabase."""
        self.log("Starting Supabase containers...")
        self.system.run(
            ["docker", "compose", "up", "-d"],
            cwd=str(self.SUPABASE_DIR)
        )
    
    def get_result(self) -> InstallResult:
        domain = self.config.get("domain")
        return InstallResult(
            success=True,
            message="Supabase installed successfully",
            access_url=f"https://{domain}",
            credentials=self._credentials
        )
