#!/usr/bin/env python3
"""Кроссплатформенный установщик pve-lxc."""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# Цвета для вывода
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'
    
    @classmethod
    def disable(cls):
        cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = cls.NC = ''

# Windows не поддерживает ANSI по умолчанию
if platform.system() == 'Windows':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        Colors.disable()

def print_info(msg): print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")
def print_error(msg): print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")
def print_warn(msg): print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")
def print_step(msg): print(f"{Colors.GREEN}[STEP]{Colors.NC} {msg}")

def get_platform_config():
    """Возвращает конфигурацию для текущей платформы."""
    system = platform.system()
    home = Path.home()
    
    if system == 'Windows':
        return {
            'install_dir': home / 'AppData' / 'Local' / 'pve-lxc',
            'bin_dir': home / 'AppData' / 'Local' / 'Microsoft' / 'WindowsApps',
            'script_ext': '.bat',
            'python_cmd': 'python',
            'venv_python': 'Scripts/python.exe',
            'venv_pip': 'Scripts/pip.exe',
        }
    elif system == 'Darwin':  # macOS
        return {
            'install_dir': home / '.pve-lxc',
            'bin_dir': Path('/usr/local/bin'),
            'script_ext': '',
            'python_cmd': 'python3',
            'venv_python': 'bin/python',
            'venv_pip': 'bin/pip',
        }
    else:  # Linux
        return {
            'install_dir': home / '.pve-lxc',
            'bin_dir': Path('/usr/local/bin'),
            'script_ext': '',
            'python_cmd': 'python3',
            'venv_python': 'bin/python',
            'venv_pip': 'bin/pip',
        }


def check_python_version():
    """Проверяет версию Python."""
    if sys.version_info < (3, 8):
        print_error(f"Требуется Python 3.8+, текущая версия: {sys.version}")
        sys.exit(1)
    print_info(f"Python {sys.version_info.major}.{sys.version_info.minor}")

def check_permissions(config):
    """Проверяет права доступа."""
    system = platform.system()
    
    if system != 'Windows':
        bin_dir = config['bin_dir']
        if bin_dir.exists() and not os.access(bin_dir, os.W_OK):
            if os.geteuid() != 0:
                print_error(f"Нет прав записи в {bin_dir}. Запусти с sudo.")
                sys.exit(1)

def copy_project_files(script_dir: Path, install_dir: Path):
    """Копирует файлы проекта."""
    print_step(f"Копирование файлов в {install_dir}")
    
    dirs_to_copy = ['lib', 'cli', 'apps', 'bootstrap']
    files_to_copy = ['requirements.txt']
    
    install_dir.mkdir(parents=True, exist_ok=True)
    
    for dir_name in dirs_to_copy:
        src = script_dir / dir_name
        dst = install_dir / dir_name
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
    
    for file_name in files_to_copy:
        src = script_dir / file_name
        dst = install_dir / file_name
        if src.exists():
            shutil.copy2(src, dst)

def create_venv(config):
    """Создаёт виртуальное окружение."""
    venv_dir = config['install_dir'] / 'venv'
    print_step(f"Создание venv: {venv_dir}")
    
    subprocess.run([sys.executable, '-m', 'venv', str(venv_dir)], check=True)
    
    pip_path = venv_dir / config['venv_pip']
    req_path = config['install_dir'] / 'requirements.txt'
    
    print_step("Установка зависимостей")
    subprocess.run([str(pip_path), 'install', '--upgrade', 'pip'], check=True)
    subprocess.run([str(pip_path), 'install', '-r', str(req_path)], check=True)

def create_launcher(config):
    """Создаёт скрипт запуска."""
    system = platform.system()
    venv_python = config['install_dir'] / 'venv' / config['venv_python']
    launcher = config['bin_dir'] / f"pve-lxc{config['script_ext']}"
    
    print_step(f"Создание launcher: {launcher}")
    
    config['bin_dir'].mkdir(parents=True, exist_ok=True)
    
    if system == 'Windows':
        content = f'@echo off\n"{venv_python}" -m cli.main %*\n'
    else:
        content = f'#!/bin/bash\nexec "{venv_python}" -m cli.main "$@"\n'
    
    launcher.write_text(content)
    
    if system != 'Windows':
        launcher.chmod(0o755)

def main():
    print_info(f"Платформа: {platform.system()} {platform.machine()}")
    
    check_python_version()
    config = get_platform_config()
    check_permissions(config)
    
    script_dir = Path(__file__).parent.resolve()
    
    copy_project_files(script_dir, config['install_dir'])
    create_venv(config)
    create_launcher(config)
    
    print_info("Установка завершена")
    print_info("Используй: pve-lxc --help")
    
    if platform.system() == 'Windows':
        print_warn("Возможно потребуется перезапустить терминал")

if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as e:
        print_error(f"Ошибка выполнения команды: {e}")
        sys.exit(1)
    except PermissionError as e:
        print_error(f"Ошибка доступа: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Неожиданная ошибка: {e}")
        sys.exit(1)
