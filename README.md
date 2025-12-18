# pve-lxc v2

CLI для управления LXC контейнерами в Proxmox VE.

## Установка
Скачать проект в /opt/

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

### Инфраструктура и Контейнеризация
| Приложение | Описание |
|------------|----------|
| docker | Docker Engine |
| kubernetes | Kubernetes (k3s) |
| fleet | Fleet Device Management |
| foreman | Foreman Infrastructure |
| samba_ad_dc | Samba Active Directory DC |

### Веб-серверы и Прокси
| Приложение | Описание |
|------------|----------|
| apache | Apache HTTP Server |
| nginx | Nginx Web Server |

### Базы данных
| Приложение | Описание |
|------------|----------|
| mariadb | MariaDB Database |
| mongodb | MongoDB Database |
| postgres | PostgreSQL Database |
| supabase | Supabase (Firebase Alternative) |

### CI/CD и Git
| Приложение | Описание |
|------------|----------|
| forgejo | Forgejo Git Server |
| gitlab | GitLab CE |
| gitlab-runner | GitLab Runner |
| jenkins | Jenkins CI/CD |

### Очереди и Сообщения
| Приложение | Описание |
|------------|----------|
| kafka | Apache Kafka |
| nats | NATS Message Broker |
| rabbitmq | RabbitMQ Message Broker |

### Мониторинг
| Приложение | Описание |
|------------|----------|
| prometheus | Prometheus Monitoring |
| zabbix | Zabbix Server |
| zabbix_agent | Zabbix Agent |
| zabbix_proxy | Zabbix Proxy |

### Автоматизация и Разработка
| Приложение | Описание |
|------------|----------|
| n8n | n8n Workflow Automation |
| mastra | Mastra AI Framework |
| railway | Railway CLI |
| vercel | Vercel CLI |

### Видеонаблюдение
| Приложение | Описание |
|------------|----------|
| motioneye | MotionEye Surveillance |
| shinobi | Shinobi Surveillance |
| zoneminder | ZoneMinder Surveillance |

### Другое
| Приложение | Описание |
|------------|----------|
| 1c | 1C:Enterprise Server |
| syncthing | Syncthing File Sync |

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
