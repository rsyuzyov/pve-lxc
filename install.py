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


def create_symlink(project_dir: Path):
    """Создаёт симлинк в /usr/local/bin."""
    src = project_dir / 'pve-lxc'
    dst = Path('/usr/local/bin/pve-lxc')
    
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    
    print_step(f"Создание симлинка: {dst} -> {src}")
    dst.symlink_to(src)


def detect_shell() -> str:
    """Определяет текущий shell."""
    shell = os.environ.get('SHELL', '/bin/bash')
    return Path(shell).name


def get_shell_rc(shell: str) -> Path:
    """Возвращает путь к rc-файлу shell."""
    home = Path.home()
    rc_files = {
        'bash': home / '.bashrc',
        'zsh': home / '.zshrc',
        'fish': home / '.config' / 'fish' / 'config.fish',
    }
    return rc_files.get(shell, home / '.bashrc')


def fix_completion_script(script: str, cmd_name: str = 'pve-lxc') -> str:
    """Исправляет completion скрипт для работы с pve-lxc."""
    # Typer генерирует completion для "python -m cli.main"
    # Нужно заменить на pve-lxc
    
    # Заменяем переменную окружения для completion
    script = script.replace('_PYTHON _M CLI.MAIN_COMPLETE', '_PVE_LXC_COMPLETE')
    
    # Заменяем вызов команды внутри функции ($1 -> pve-lxc)
    script = script.replace('$1', cmd_name)
    
    # Заменяем имя функции
    script = script.replace('_python_mclimain_completion', f'_{cmd_name}_completion')
    
    # Заменяем команду в строке complete (после замены имени функции)
    script = script.replace(f'complete -o default -F _{cmd_name}_completion python -m cli.main',
                           f'complete -o default -F _{cmd_name}_completion {cmd_name}')
    
    return script


def enable_bash_completion():
    """Включает bash-completion в /etc/bash.bashrc если закомментирован."""
    bashrc = Path('/etc/bash.bashrc')
    
    if not bashrc.exists() or not os.access(bashrc, os.W_OK):
        return
    
    content = bashrc.read_text()
    
    # Проверяем, закомментирован ли bash-completion
    if '#if ! shopt -oq posix; then' in content:
        print_step("Включение bash-completion в /etc/bash.bashrc")
        
        replacements = [
            ('#if ! shopt -oq posix; then', 'if ! shopt -oq posix; then'),
            ('#  if [ -f /usr/share/bash-completion/bash_completion ]; then',
             '  if [ -f /usr/share/bash-completion/bash_completion ]; then'),
            ('#    . /usr/share/bash-completion/bash_completion',
             '    . /usr/share/bash-completion/bash_completion'),
            ('#  elif [ -f /etc/bash_completion ]; then',
             '  elif [ -f /etc/bash_completion ]; then'),
            ('#    . /etc/bash_completion',
             '    . /etc/bash_completion'),
            ('#  fi', '  fi'),
            ('#fi', 'fi'),
        ]
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        bashrc.write_text(content)
        print_info("bash-completion включён")


def install_completion(project_dir: Path):
    """Устанавливает автодополнение в системную директорию."""
    print_step("Настройка автодополнения")
    
    # Включаем bash-completion если нужно
    enable_bash_completion()
    
    # Используем готовый completion скрипт
    completion_src = project_dir / 'cli' / 'completion.bash'
    
    if not completion_src.exists():
        print_error(f"Файл {completion_src} не найден")
        return
    
    # Системная директория для bash completion
    system_completion_dir = Path('/etc/bash_completion.d')
    
    if system_completion_dir.exists() and os.access(system_completion_dir, os.W_OK):
        # Устанавливаем симлинк системно (для всех пользователей)
        completion_file = system_completion_dir / 'pve-lxc'
        if completion_file.exists() or completion_file.is_symlink():
            completion_file.unlink()
        completion_file.symlink_to(completion_src)
        print_info(f"Симлинк: {completion_file} -> {completion_src}")
    else:
        # Fallback: симлинк для текущего пользователя
        completion_dir = Path.home() / '.local' / 'share' / 'bash-completion' / 'completions'
        completion_dir.mkdir(parents=True, exist_ok=True)
        completion_file = completion_dir / 'pve-lxc'
        if completion_file.exists() or completion_file.is_symlink():
            completion_file.unlink()
        completion_file.symlink_to(completion_src)
        print_info(f"Симлинк: {completion_file} -> {completion_src}")


def fix_zsh_completion_script(script: str, cmd_name: str = 'pve-lxc') -> str:
    """Исправляет zsh completion скрипт."""
    script = script.replace('_PYTHON _M CLI.MAIN_COMPLETE', f'_PVE_LXC_COMPLETE')
    script = script.replace('python -m cli.main', cmd_name)
    return script


def install_zsh_completion(project_dir: Path):
    """Устанавливает zsh completion если zsh используется."""
    python_path = project_dir / '.venv' / 'bin' / 'python'
    
    result = subprocess.run(
        [str(python_path), '-m', 'cli.main', '--show-completion', 'zsh'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return
    
    completion_script = result.stdout.strip()
    if not completion_script:
        return
    
    # Исправляем скрипт
    completion_script = fix_zsh_completion_script(completion_script)
    
    # Системная директория для zsh
    zsh_dirs = [
        Path('/usr/local/share/zsh/site-functions'),
        Path('/usr/share/zsh/site-functions'),
    ]
    
    for zsh_dir in zsh_dirs:
        if zsh_dir.exists() and os.access(zsh_dir, os.W_OK):
            completion_file = zsh_dir / '_pve-lxc'
            completion_file.write_text(completion_script)
            print_info(f"Zsh completion: {completion_file}")
            return
    
    # Fallback для пользователя
    user_zsh_dir = Path.home() / '.zsh' / 'completions'
    user_zsh_dir.mkdir(parents=True, exist_ok=True)
    completion_file = user_zsh_dir / '_pve-lxc'
    completion_file.write_text(completion_script)


def main():
    check_python_version()
    
    project_dir = Path(__file__).parent.resolve()
    create_venv(project_dir)
    create_symlink(project_dir)
    install_completion(project_dir)
    
    print_info("Установка завершена")
    print_info("Запуск: pve-lxc --help")


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as e:
        print_error(f"Ошибка выполнения команды: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Неожиданная ошибка: {e}")
        sys.exit(1)
