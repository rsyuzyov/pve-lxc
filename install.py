#!/usr/bin/env python3
"""Установщик pve-lxc — создаёт venv и ставит зависимости."""

import os
import sys
import subprocess
from pathlib import Path

# Цвета для вывода
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def print_info(msg): print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")
def print_error(msg): print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")
def print_step(msg): print(f"{Colors.GREEN}[STEP]{Colors.NC} {msg}")


def check_python_version():
    """Проверяет версию Python."""
    if sys.version_info < (3, 8):
        print_error(f"Требуется Python 3.8+, текущая версия: {sys.version}")
        sys.exit(1)
    print_info(f"Python {sys.version_info.major}.{sys.version_info.minor}")


def create_venv(project_dir: Path):
    """Создаёт виртуальное окружение и ставит зависимости."""
    venv_dir = project_dir / '.venv'
    
    if not venv_dir.exists():
        print_step(f"Создание venv: {venv_dir}")
        subprocess.run([sys.executable, '-m', 'venv', str(venv_dir)], check=True)
    else:
        print_info(f"venv уже существует: {venv_dir}")
    
    pip_path = venv_dir / 'bin' / 'pip'
    req_path = project_dir / 'requirements.txt'
    
    print_step("Установка зависимостей")
    subprocess.run([str(pip_path), 'install', '--upgrade', 'pip'], check=True)
    subprocess.run([str(pip_path), 'install', '-r', str(req_path)], check=True)


def main():
    check_python_version()
    
    project_dir = Path(__file__).parent.resolve()
    create_venv(project_dir)
    
    print_info("Установка завершена")
    print_info("Запуск: ./pve-lxc --help")


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as e:
        print_error(f"Ошибка выполнения команды: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Неожиданная ошибка: {e}")
        sys.exit(1)
