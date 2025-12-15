#!/bin/bash
# Тестовое развертывание всех приложений в контейнере 901

set -e

CTID=901
LOG_FILE="/tmp/deploy_test_$(date +%Y%m%d_%H%M%S).log"
VENV_PYTHON="$(dirname "$0")/../.venv/bin/python"
CLI="$(dirname "$0")/../cli/main.py"

# Получаем IP и шлюз хоста
HOST_IP=$(hostname -I | awk '{print $1}')
TEST_IP=$(echo "$HOST_IP" | sed 's/\.[0-9]*$/.234/')
GATEWAY=$(ip route | grep default | awk '{print $3}')

# Список приложений
APPS=(apache docker foreman forgejo gitlab gitlab-runner jenkins kafka kubernetes mariadb mongodb motioneye n8n nats nginx postgres prometheus rabbitmq shinobi syncthing zoneminder)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

cleanup() {
    if pct status $CTID &>/dev/null; then
        log "Удаление контейнера $CTID"
        pct stop $CTID 2>/dev/null || true
        pct destroy $CTID --purge 2>/dev/null || true
    fi
}

test_app() {
    local app=$1
    local test_type=$2
    local extra_args=$3
    
    log "=== Тест $app ($test_type) ==="
    
    cleanup
    
    if $VENV_PYTHON "$CLI" deploy --app "$app" --create --ctid $CTID --name "test-$app" $extra_args 2>&1 | tee -a "$LOG_FILE"; then
        log "✓ $app ($test_type) - OK"
        return 0
    else
        log "✗ $app ($test_type) - FAILED"
        return 1
    fi
}

main() {
    log "Начало тестирования. Лог: $LOG_FILE"
    log "TEST_IP=$TEST_IP, GATEWAY=$GATEWAY"
    
    local failed=()
    
    for app in "${APPS[@]}"; do
        # Тест 1: минимальные параметры (DHCP)
        if ! test_app "$app" "dhcp" ""; then
            failed+=("$app:dhcp")
        fi
        
        cleanup
        
        # Тест 2: статический IP
        if ! test_app "$app" "static-ip" "--ip $TEST_IP --gateway $GATEWAY"; then
            failed+=("$app:static-ip")
        fi
        
        cleanup
    done
    
    log "=== ИТОГИ ==="
    if [ ${#failed[@]} -eq 0 ]; then
        log "Все тесты пройдены успешно"
    else
        log "Провалено тестов: ${#failed[@]}"
        for f in "${failed[@]}"; do
            log "  - $f"
        done
    fi
    
    log "Лог сохранён: $LOG_FILE"
}

main "$@"
