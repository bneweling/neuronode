#!/bin/bash

# =============================================================================
# KI-Wissenssystem Deployment Manager
# =============================================================================
# Zentrale Steuerung für alle Deployment-Operationen
# =============================================================================

set -e

# Konfiguration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="ki-wissenssystem"
DOCKER_COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE="production/config/.env"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Banner
show_banner() {
    echo -e "${BLUE}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║    🚀 KI-Wissenssystem Deployment Manager                       ║
║                                                                  ║
║    Zentrale Steuerung für Production Deployments                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${PURPLE}[STEP]${NC} $1"; }

# Hilfsfunktionen
check_dependencies() {
    log_info "Überprüfe Dependencies..."
    
    for cmd in docker docker-compose git; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd ist nicht installiert!"
            exit 1
        fi
    done
    
    log_success "Alle Dependencies verfügbar"
}

check_environment() {
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "Environment-Datei nicht gefunden: $ENV_FILE"
        log_info "Kopiere Template nach $ENV_FILE"
        
        mkdir -p "$(dirname "$ENV_FILE")"
        cp production-env.template "$ENV_FILE"
        
        log_warning "Bitte $ENV_FILE konfigurieren und erneut ausführen!"
        exit 1
    fi
    
    log_success "Environment-Konfiguration gefunden"
}

get_version() {
    if git rev-parse --git-dir > /dev/null 2>&1; then
        echo "$(git rev-parse --short HEAD)"
    else
        echo "unknown"
    fi
}

backup_data() {
    log_step "Erstelle Backup vor Deployment..."
    
    BACKUP_DIR="production/backups/pre-deploy-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup nur wenn Container laufen
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps -q neo4j > /dev/null 2>&1; then
        docker exec ki-prod-neo4j neo4j-admin database dump --to-path=/var/lib/neo4j/import neo4j 2>/dev/null || true
        docker cp ki-prod-neo4j:/var/lib/neo4j/import/neo4j.dump "$BACKUP_DIR/" 2>/dev/null || true
    fi
    
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps -q chromadb > /dev/null 2>&1; then
        docker cp ki-prod-chromadb:/chroma/chroma "$BACKUP_DIR/chroma" 2>/dev/null || true
    fi
    
    log_success "Backup erstellt: $BACKUP_DIR"
}

# Deployment-Strategien
deploy_fresh() {
    log_step "Führe Fresh Deployment durch..."
    
    # Setup ausführen
    if [ -f "production-setup.sh" ]; then
        chmod +x production-setup.sh
        ./production-setup.sh
    fi
    
    # Container starten
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    # Warten auf Health Checks
    wait_for_health
    
    log_success "Fresh Deployment abgeschlossen!"
}

deploy_update() {
    log_step "Führe Rolling Update durch..."
    
    # Backup erstellen
    backup_data
    
    # Images neu bauen
    docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache --parallel
    
    # Rolling Update
    for service in backend frontend; do
        log_info "Update $service..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --no-deps $service
        sleep 10  # Grace period
    done
    
    # Health Check
    wait_for_health
    
    log_success "Rolling Update abgeschlossen!"
}

deploy_rollback() {
    log_step "Führe Rollback durch..."
    
    # Stoppe aktuelle Services
    docker-compose -f "$DOCKER_COMPOSE_FILE" stop backend frontend
    
    # Suche letztes funktionierendes Backup
    LAST_BACKUP=$(find production/backups -name "pre-deploy-*" -type d | sort -r | head -n1)
    
    if [ -z "$LAST_BACKUP" ]; then
        log_error "Kein Backup für Rollback gefunden!"
        exit 1
    fi
    
    log_info "Rollback zu: $LAST_BACKUP"
    
    # Restore Database (falls vorhanden)
    if [ -f "$LAST_BACKUP/neo4j.dump" ]; then
        docker cp "$LAST_BACKUP/neo4j.dump" ki-prod-neo4j:/var/lib/neo4j/import/
        docker exec ki-prod-neo4j neo4j-admin database load --from-path=/var/lib/neo4j/import neo4j --overwrite-destination=true
    fi
    
    # Services neu starten
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d backend frontend
    
    wait_for_health
    
    log_success "Rollback abgeschlossen!"
}

wait_for_health() {
    log_info "Warte auf Health Checks..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:8080/health > /dev/null 2>&1 && \
           curl -f http://localhost:3000 > /dev/null 2>&1; then
            log_success "Alle Services sind gesund!"
            return 0
        fi
        
        echo -n "."
        sleep 10
        ((attempt++))
    done
    
    log_error "Health Check fehlgeschlagen!"
    show_status
    exit 1
}

show_status() {
    log_info "System Status:"
    
    echo -e "\n${YELLOW}=== Container Status ===${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    
    echo -e "\n${YELLOW}=== Resource Usage ===${NC}"
    docker stats --no-stream
    
    echo -e "\n${YELLOW}=== Health Checks ===${NC}"
    for service in "Backend:8080/health" "Frontend:3000" "Grafana:3001"; do
        name=$(echo $service | cut -d: -f1)
        endpoint=$(echo $service | cut -d: -f2)
        
        if curl -f "http://localhost:$endpoint" > /dev/null 2>&1; then
            echo -e "✅ $name: ${GREEN}OK${NC}"
        else
            echo -e "❌ $name: ${RED}FEHLER${NC}"
        fi
    done
}

show_logs() {
    local service=${1:-""}
    
    if [ -n "$service" ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f --tail=100 "$service"
    else
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f --tail=50
    fi
}

cleanup() {
    log_step "Cleanup-Operationen..."
    
    # Alte Container und Images entfernen
    docker system prune -f
    
    # Alte Backups entfernen (älter als 30 Tage)
    find production/backups -name "pre-deploy-*" -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true
    
    # Log-Rotation
    find production/logs -name "*.log" -size +100M -exec truncate -s 50M {} \; 2>/dev/null || true
    
    log_success "Cleanup abgeschlossen"
}

show_help() {
    cat << EOF
${BLUE}KI-Wissenssystem Deployment Manager${NC}

VERWENDUNG:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    fresh           Fresh deployment (komplette Neuinstallation)
    update          Rolling update (behält Daten bei)
    rollback        Rollback zum letzten Backup
    status          Zeigt System-Status
    logs [service]  Zeigt Logs (optional: spezifischer Service)
    stop            Stoppt alle Services
    start           Startet alle Services
    restart         Neustart aller Services
    cleanup         Cleanup-Operationen
    backup          Manuelles Backup
    monitor         Öffnet Monitoring-Dashboard

BEISPIELE:
    $0 fresh                    # Komplett neues Deployment
    $0 update                   # Update bestehender Installation
    $0 logs backend             # Backend-Logs anzeigen
    $0 status                   # System-Status prüfen

OPTIONEN:
    -h, --help                  Zeigt diese Hilfe
    -v, --version               Zeigt Version
    --env-file FILE             Verwendet alternative env-Datei

EOF
}

# Hauptlogik
main() {
    show_banner
    
    case "${1:-help}" in
        fresh)
            check_dependencies
            check_environment
            deploy_fresh
            show_status
            ;;
        update)
            check_dependencies
            check_environment
            deploy_update
            show_status
            ;;
        rollback)
            check_dependencies
            deploy_rollback
            show_status
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        stop)
            log_info "Stoppe alle Services..."
            docker-compose -f "$DOCKER_COMPOSE_FILE" down
            log_success "Services gestoppt"
            ;;
        start)
            log_info "Starte alle Services..."
            docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
            wait_for_health
            log_success "Services gestartet"
            ;;
        restart)
            log_info "Starte Services neu..."
            docker-compose -f "$DOCKER_COMPOSE_FILE" restart
            wait_for_health
            log_success "Services neu gestartet"
            ;;
        cleanup)
            cleanup
            ;;
        backup)
            backup_data
            ;;
        monitor)
            log_info "Öffne Monitoring-Dashboard..."
            echo "Grafana: http://localhost:3001 (admin/admin)"
            echo "Prometheus: http://localhost:9090"
            ;;
        version|--version|-v)
            echo "KI-Wissenssystem Deployment Manager v1.0"
            echo "Git Version: $(get_version)"
            ;;
        help|--help|-h|*)
            show_help
            ;;
    esac
}

# Trap für cleanup bei Ctrl+C
trap 'log_warning "Deployment unterbrochen"; exit 1' INT TERM

# Script ausführen
main "$@" 