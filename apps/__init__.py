# pve-lxc v2 - Application installers

# Импорт всех установщиков для регистрации в AppRegistry
from apps.postgres.install import PostgresInstaller
from apps.mariadb.install import MariadbInstaller
from apps.mongodb.install import MongodbInstaller
from apps.nginx.install import NginxInstaller
from apps.apache.install import ApacheInstaller
from apps.docker.install import DockerInstaller
from apps.gitlab.install import GitlabInstaller
from apps.gitlab_runner.install import GitlabRunnerInstaller
from apps.jenkins.install import JenkinsInstaller
from apps.forgejo.install import ForgejoInstaller
from apps.rabbitmq.install import RabbitmqInstaller
from apps.kafka.install import KafkaInstaller
from apps.nats.install import NatsInstaller
from apps.prometheus.install import PrometheusInstaller
from apps.kubernetes.install import KubernetesInstaller
from apps.n8n.install import N8nInstaller
from apps.syncthing.install import SyncthingInstaller
from apps.motioneye.install import MotioneyeInstaller
from apps.shinobi.install import ShinobiInstaller
from apps.zoneminder.install import ZoneminderInstaller
from apps.foreman.install import ForemanInstaller
from apps.fleet.install import FleetInstaller
from apps.mastra.install import MastraInstaller
from apps.samba.install import SambaInstaller
from apps.samba_ad_dc.install import SambaADDCInstaller
from apps.pmg.install import PMGInstaller
from apps.iredmail.install import IRedMailInstaller
from apps.stalwart.install import StalwartInstaller
from apps import registry  # noqa: F401
# 1c не импортируем - имя папки начинается с цифры
