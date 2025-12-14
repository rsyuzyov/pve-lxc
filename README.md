# pve-lxc v2

CLI для управления LXC контейнерами в Proxmox VE.

## Установка

```bash
sudo ./install.sh
```

## Команды

```bash
# Создать контейнер
pve-lxc create --name gitlab --cores 4 --memory 8192 --ip 21-50

# Базовая настройка
pve-lxc bootstrap 101

# Развернуть приложение
pve-lxc deploy --app gitlab --container 101
pve-lxc deploy --app gitlab --create --name gitlab

# Список контейнеров
pve-lxc list

# Список приложений
pve-lxc apps
pve-lxc apps --help gitlab

# Найти свободные IP
pve-lxc ip 21-50

# Удалить контейнер
pve-lxc destroy 101 --force
```

## Приложения

| Приложение | Описание |
|------------|----------|
| 1c | 1C:Enterprise Server |
| apache | Apache HTTP Server |
| docker | Docker Engine |
| foreman | Foreman Infrastructure |
| forgejo | Forgejo Git Server |
| gitlab | GitLab CE |
| gitlab-runner | GitLab Runner |
| jenkins | Jenkins CI/CD |
| kafka | Apache Kafka |
| kubernetes | Kubernetes (k3s) |
| mariadb | MariaDB Database |
| mongodb | MongoDB Database |
| motioneye | MotionEye Surveillance |
| n8n | n8n Workflow Automation |
| nats | NATS Message Broker |
| nginx | Nginx Web Server |
| postgres | PostgreSQL Database |
| prometheus | Prometheus Monitoring |
| rabbitmq | RabbitMQ Message Broker |
| shinobi | Shinobi Surveillance |
| syncthing | Syncthing File Sync |
| zoneminder | ZoneMinder Surveillance |

## Конфигурация

Пользовательская конфигурация: `~/.pve-lxc/config.yaml`

```yaml
container:
  cores: 4
  memory: 4096
  storage: local-lvm

bootstrap:
  locale: ru_RU.UTF-8
  timezone: Europe/Moscow
```
