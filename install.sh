#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_step() { echo -e "${GREEN}[STEP]${NC} $1"; }

INSTALL_DIR="$HOME/.pve-lxc"
VENV_DIR="$INSTALL_DIR/venv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYMLINK="/usr/local/bin/pve-lxc"

if [ "$EUID" -ne 0 ]; then
    print_error "Требуются права root"
    exit 1
fi

print_step "Создание директории $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

print_step "Копирование файлов проекта"
cp -r "$SCRIPT_DIR/lib" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/cli" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/apps" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/bootstrap" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"

print_step "Создание виртуального окружения Python"
python3 -m venv "$VENV_DIR"

print_step "Установка зависимостей"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

print_step "Создание симлинка $SYMLINK"
cat > "$SYMLINK" << EOF
#!/bin/bash
exec "$VENV_DIR/bin/python" -m cli.main "\$@"
EOF
chmod +x "$SYMLINK"

print_info "Установка завершена"
print_info "Используйте: pve-lxc --help"
