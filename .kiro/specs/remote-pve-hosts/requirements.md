# Requirements Document

## Introduction

Расширение pve-lxc для поддержки удалённого управления несколькими хостами Proxmox VE через SSH. Позволяет запускать CLI из Docker-контейнера или отдельного LXC, подключаясь к PVE хостам по сети. Использует стандартный SSH config для хранения параметров подключения.

## Glossary

- **PVE Host**: Сервер с установленным Proxmox VE, на котором выполняются команды pct/pvesm/pveam
- **SSH Config**: Стандартный файл конфигурации SSH (~/.ssh/config) с алиасами хостов
- **Host Alias**: Имя хоста в SSH config, используемое для подключения
- **Default Host**: PVE хост, используемый по умолчанию при отсутствии явного указания

## Requirements

### Requirement 1

**User Story:** As a DevOps engineer, I want to manage multiple PVE hosts from a single CLI instance, so that I can deploy containers to different servers without switching environments.

#### Acceptance Criteria

1. WHEN a user specifies a host via `--host` flag THEN the CLI SHALL execute commands on that PVE host via SSH
2. WHEN a user does not specify a host AND a default host is configured in pve-lxc config THEN the CLI SHALL use the default host
3. WHEN a user specifies a host that is not reachable THEN the CLI SHALL display an error message with connection details

### Requirement 2

**User Story:** As a system administrator, I want to use standard SSH config for host management, so that I can leverage existing SSH infrastructure and tools.

#### Acceptance Criteria

1. WHEN connecting to a host THEN the CLI SHALL use SSH config (~/.ssh/config) for connection parameters
2. WHEN a user runs `pve-lxc host list` THEN the CLI SHALL display configured hosts from SSH config that are marked as PVE hosts
3. WHEN a user runs `pve-lxc host test <name>` THEN the CLI SHALL verify SSH connectivity and PVE tools availability
4. WHEN a user runs `pve-lxc host set-default <name>` THEN the CLI SHALL store the default host in pve-lxc config

### Requirement 3

**User Story:** As a system administrator, I want to easily add PVE hosts to my configuration, so that I can quickly set up new servers for management.

#### Acceptance Criteria

1. WHEN a user runs `pve-lxc host add <name> --hostname <ip> [--user root] [--port 22] [--key ~/.ssh/id_rsa]` THEN the CLI SHALL add a Host entry to SSH config
2. WHEN a user runs `pve-lxc host remove <name>` THEN the CLI SHALL remove the Host entry from SSH config
3. WHEN adding a host with a name that already exists THEN the CLI SHALL display an error and suggest using a different name

### Requirement 4

**User Story:** As a user running pve-lxc in Docker, I want the application to work without local PVE tools, so that I can manage PVE hosts from any environment.

#### Acceptance Criteria

1. WHEN running with a configured host THEN the CLI SHALL execute PVE commands (pct, pvesm, pveam, pvesh) via SSH
2. WHEN running with a configured host THEN the CLI SHALL transfer files to containers via SSH and remote pct push
3. WHEN no host is configured AND local PVE tools are not available THEN the CLI SHALL display an error with setup instructions

### Requirement 5

**User Story:** As a DevOps engineer, I want to see the status of my PVE hosts, so that I can quickly identify connectivity issues.

#### Acceptance Criteria

1. WHEN a user runs `pve-lxc host list` THEN the CLI SHALL show host name, address, and connection status (online/offline)
2. WHEN a user runs `pve-lxc host list --verbose` THEN the CLI SHALL additionally show PVE version and node name
