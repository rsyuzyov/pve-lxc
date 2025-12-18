"""Mastra AI установщик."""
import sys
from pathlib import Path

# Добавляем корень проекта в путь для импорта
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from apps.base import AppInstaller, InstallResult
from apps.registry import AppRegistry

@AppRegistry.register
class MastraInstaller(AppInstaller):
    name = "mastra"
    description = "Mastra AI Framework"
    default_cores = 2
    default_memory = 4096
    default_disk = 20
    
    def validate(self) -> bool:
        return True
    
    def install(self) -> None:
        # 1. Установка зависимостей
        self.system.apt_update()
        self.system.apt_install([
            "curl",
            "git",
            "ca-certificates",
            "gnupg",
            "build-essential"
        ])
        
        # 2. Установка Node.js 20 LTS
        self.system.run(["curl", "-fsSL", "https://deb.nodesource.com/setup_20.x", "-o", "/tmp/nodesource_setup.sh"])
        self.system.run(["bash", "/tmp/nodesource_setup.sh"])
        self.system.apt_install(["nodejs"])
        
        # 3. Подготовка директории проекта
        self.system.mkdir(Path("/opt/mastra-app"))
        
        # 4. Инициализация проекта Mastra
        # Мы используем --yes для неинтерактивной установки
        self.system.run(["npm", "init", "-y"], cwd="/opt/mastra-app")
        self.system.run(["npm", "install", "mastra", "typescript", "tsx", "@types/node"], cwd="/opt/mastra-app")
        self.system.run(["npx", "tsc", "--init"], cwd="/opt/mastra-app")

    def configure(self) -> None:
        # Создаем базовый пример агента
        agent_code = """
import { Mastra } from 'mastra';

const mastra = new Mastra({
  agents: {
    baseAgent: {
      name: 'Base Agent',
      instructions: 'You are a helpful assistant.',
      model: {
        provider: 'OPENAI',
        name: 'gpt-4o',
        apiKey: process.env.OPENAI_API_KEY || 'your-api-key',
      },
    },
  },
});

console.log('Mastra initialized');
"""
        self.system.write_file(Path("/opt/mastra-app/index.ts"), agent_code)
        
        # Создаем скрипт запуска в package.json
        self.system.run(["npm", "pkg", "set", "scripts.start=tsx index.ts"], cwd="/opt/mastra-app")

    def get_result(self) -> InstallResult:
        return InstallResult(
            success=True,
            message="Mastra AI environment installed in /opt/mastra-app",
            access_url=None,
            credentials={"info": "Add OPENAI_API_KEY to your environment to use agents"}
        )
