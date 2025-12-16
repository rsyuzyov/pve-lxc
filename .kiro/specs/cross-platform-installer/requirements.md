# Requirements Document

## Introduction

Замена bash-скрипта install.sh на кросс-платформенный Python-скрипт установки, работающий на Linux, Windows и macOS. Скрипт должен устанавливать pve-lxc CLI с созданием виртуального окружения и необходимых зависимостей.

## Glossary

- **INSTALL_DIR**: Директория установки приложения (~/.pve-lxc)
- **VENV_DIR**: Директория виртуального окружения Python внутри INSTALL_DIR
- **CLI_COMMAND**: Команда для запуска приложения (pve-lxc)

## Requirements

### Requirement 1

**User Story:** As a user, I want to run a single Python script to install pve-lxc, so that installation works on any platform with Python.

#### Acceptance Criteria

1. WHEN the user runs `python install.py` THEN the system SHALL create the installation directory at ~/.pve-lxc
2. WHEN the installation directory is created THEN the system SHALL copy project files (lib, cli, apps, bootstrap, requirements.txt) to it
3. WHEN project files are copied THEN the system SHALL create a Python virtual environment in ~/.pve-lxc/venv
4. WHEN the virtual environment is created THEN the system SHALL install dependencies from requirements.txt

### Requirement 2

**User Story:** As a user on Linux or macOS, I want the installer to create a command-line entry point, so that I can run pve-lxc from anywhere.

#### Acceptance Criteria

1. WHEN installing on Linux or macOS THEN the system SHALL create an executable wrapper script
2. WHEN the wrapper script is created THEN the system SHALL place it in ~/.local/bin/pve-lxc or /usr/local/bin/pve-lxc depending on permissions
3. WHEN the wrapper script is executed THEN the system SHALL invoke the virtual environment Python with cli.main module

### Requirement 3

**User Story:** As a user on Windows, I want the installer to create a batch file entry point, so that I can run pve-lxc from command prompt.

#### Acceptance Criteria

1. WHEN installing on Windows THEN the system SHALL create a pve-lxc.bat batch file
2. WHEN the batch file is created THEN the system SHALL place it in a directory that is in PATH or suggest adding to PATH
3. WHEN the batch file is executed THEN the system SHALL invoke the virtual environment Python with cli.main module

### Requirement 4

**User Story:** As a user, I want to see colored progress messages during installation, so that I understand what is happening.

#### Acceptance Criteria

1. WHEN installation steps are executed THEN the system SHALL print colored status messages (info, error, warning, step)
2. WHEN running on Windows THEN the system SHALL enable ANSI color support or fall back to plain text
3. WHEN an error occurs THEN the system SHALL print an error message and exit with non-zero code

### Requirement 5

**User Story:** As a user, I want the installer to check prerequisites, so that I know if something is missing before installation fails.

#### Acceptance Criteria

1. WHEN the installer starts THEN the system SHALL verify Python version is 3.8 or higher
2. WHEN Python version is insufficient THEN the system SHALL print an error and exit
3. WHEN the installer starts THEN the system SHALL verify pip is available

