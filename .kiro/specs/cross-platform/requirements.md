# Requirements Document

## Introduction

Добавление кросс-платформенной поддержки для CLI-приложения pve-lxc, чтобы оно корректно работало на Windows, Linux и macOS. Основная работа приложения — управление Proxmox VE через SSH, поэтому локальные платформо-зависимые операции минимальны и сводятся к работе с файлами и правами доступа.

## Glossary

- **OS_TYPE**: Глобальная переменная, содержащая тип текущей операционной системы
- **OSType**: Enum с возможными значениями типа ОС (WINDOWS, LINUX, MACOS)
- **chmod**: Unix-операция установки прав доступа к файлу, не поддерживается на Windows

## Requirements

### Requirement 1

**User Story:** As a developer, I want to detect the operating system at startup, so that I can use platform-specific logic throughout the application.

#### Acceptance Criteria

1. WHEN the application starts THEN the system SHALL detect the current OS and store it in OS_TYPE variable
2. WHEN OS_TYPE is accessed THEN the system SHALL return one of the OSType enum values: WINDOWS, LINUX, or MACOS
3. WHEN running on an unknown platform THEN the system SHALL default to LINUX type

### Requirement 2

**User Story:** As a user on Windows, I want the application to skip Unix-specific file permission operations, so that the application runs without errors.

#### Acceptance Criteria

1. WHEN setting file permissions on Windows THEN the system SHALL skip the chmod operation
2. WHEN setting file permissions on Linux or macOS THEN the system SHALL execute the chmod operation normally
3. WHEN writing SSH config on Windows THEN the system SHALL create the file without setting Unix permissions

### Requirement 3

**User Story:** As a developer, I want consistent path handling across platforms, so that file operations work correctly on all operating systems.

#### Acceptance Criteria

1. WHEN constructing file paths THEN the system SHALL use pathlib.Path instead of string manipulation with hardcoded separators
2. WHEN accessing user home directory THEN the system SHALL use Path.home() which works on all platforms
