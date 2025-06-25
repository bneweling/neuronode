#!/bin/bash

# =============================================================================
# KI-Wissenssystem Production Setup Script
# =============================================================================
# Automatisiertes Setup für produktiven Einsatz
# Autor: KI-Wissenssystem Team
# Version: 1.0
# =============================================================================

set -e  # Exit on any error

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
LOGFILE="production-setup.log"
exec 1> >(tee -a "$LOGFILE")
exec 2> >(tee -a "$LOGFILE" >&2)

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║    🚀 KI-Wissenssystem Production Setup                         ║
║                                                                  ║
║    Automatisierte Einrichtung für produktiven Einsatz           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Funktionen
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Überprüfe System-Anforderungen..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 ist nicht installiert!"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js ist nicht installiert!"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker ist nicht installiert!"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose ist nicht installiert!"
        exit 1
    fi
    
    log_success "Alle System-Anforderungen erfüllt"
}

setup_environment() {
    log_info "Richte Produktions-Umgebung ein..."
    
    # Create production directories
    mkdir -p production/{logs,data,backups,ssl,config}
    mkdir -p production/data/{uploads,exports,temp}
    
    # Copy configuration templates
    if [ ! -f "production/config/.env" ]; then
        cp ki-wissenssystem/env.example production/config/.env
        log_info "Environment-Template nach production/config/.env kopiert"
        log_warning "Bitte .env-Datei mit produktiven Werten konfigurieren!"
    fi
    
    log_success "Produktions-Verzeichnisse erstellt"
}

setup_backend() {
    log_info "Richte Backend für Produktion ein..."
    
    cd ki-wissenssystem
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Python Virtual Environment erstellt"
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Add production dependencies
    pip install gunicorn supervisor
    
    cd ..
    log_success "Backend-Dependencies installiert"
}

setup_frontend() {
    log_info "Richte Frontend für Produktion ein..."
    
    cd ki-wissenssystem-webapp
    
    # Install dependencies
    npm ci --production=false
    
    # Build for production
    npm run build
    
    cd ..
    log_success "Frontend für Produktion gebaut"
}

setup_docker() {
    log_info "Bereite Docker-Umgebung vor..."
    
    # Build images
    cd ki-wissenssystem
    docker-compose build --no-cache
    
    cd ..
    log_success "Docker-Images erstellt"
}

setup_nginx() {
    log_info "Konfiguriere Nginx für Produktion..."
    
    # Create nginx configuration for production
    cat > production/config/nginx-production.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server localhost:8080;
    }
    
    upstream frontend {
        server localhost:3000;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=web:10m rate=30r/s;
    
    server {
        listen 80;
        server_name _;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        
        # Frontend
        location / {
            limit_req zone=web burst=50 nodelay;
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # API
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF
    
    log_success "Nginx-Konfiguration erstellt"
}

setup_systemd() {
    log_info "Erstelle Systemd-Services..."
    
    # Backend service
    cat > production/config/ki-backend.service << EOF
[Unit]
Description=KI-Wissenssystem Backend API
After=network.target
Requires=docker.service

[Service]
Type=forking
User=$USER
WorkingDirectory=$(pwd)/ki-wissenssystem
ExecStart=$(pwd)/production/scripts/start-backend.sh
ExecStop=$(pwd)/production/scripts/stop-backend.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Frontend service
    cat > production/config/ki-frontend.service << EOF
[Unit]
Description=KI-Wissenssystem Frontend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)/ki-wissenssystem-webapp
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
Environment=NODE_ENV=production
Environment=PORT=3000

[Install]
WantedBy=multi-user.target
EOF
    
    log_success "Systemd-Services erstellt"
}

setup_monitoring() {
    log_info "Richte Monitoring ein..."
    
    # Create health check script
    cat > production/scripts/health-check.sh << 'EOF'
#!/bin/bash

# Health Check Script
check_backend() {
    curl -f http://localhost:8080/health > /dev/null 2>&1
    return $?
}

check_frontend() {
    curl -f http://localhost:3000 > /dev/null 2>&1
    return $?
}

check_docker() {
    docker-compose -f ki-wissenssystem/docker-compose.yml ps | grep -q "Up"
    return $?
}

echo "=== Health Check $(date) ==="
if check_backend; then
    echo "✅ Backend: OK"
else
    echo "❌ Backend: FEHLER"
fi

if check_frontend; then
    echo "✅ Frontend: OK"
else
    echo "❌ Frontend: FEHLER"
fi

if check_docker; then
    echo "✅ Docker Services: OK"
else
    echo "❌ Docker Services: FEHLER"
fi
echo "================================"
EOF
    
    chmod +x production/scripts/health-check.sh
    log_success "Health-Check-Script erstellt"
}

create_scripts() {
    log_info "Erstelle Produktions-Skripte..."
    
    mkdir -p production/scripts
    
    # Start script
    cat > production/scripts/start-production.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starte KI-Wissenssystem Production..."

# Start Docker services
cd ki-wissenssystem
docker-compose up -d
cd ..

# Start frontend
cd ki-wissenssystem-webapp
npm start &
echo $! > ../production/ki-frontend.pid
cd ..

echo "✅ KI-Wissenssystem Production gestartet!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8080"
EOF

    # Stop script
    cat > production/scripts/stop-production.sh << 'EOF'
#!/bin/bash

echo "🛑 Stoppe KI-Wissenssystem Production..."

# Stop frontend
if [ -f production/ki-frontend.pid ]; then
    kill $(cat production/ki-frontend.pid) 2>/dev/null || true
    rm -f production/ki-frontend.pid
fi

# Stop Docker services
cd ki-wissenssystem
docker-compose down
cd ..

echo "✅ KI-Wissenssystem Production gestoppt!"
EOF

    # Backup script
    cat > production/scripts/backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="production/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Erstelle Backup in $BACKUP_DIR..."

# Backup database
docker exec ki-wissenssystem-neo4j neo4j-admin database dump --to-path=/var/lib/neo4j/import neo4j
docker cp ki-wissenssystem-neo4j:/var/lib/neo4j/import/neo4j.dump "$BACKUP_DIR/"

# Backup vector database
docker cp ki-wissenssystem-chromadb:/chroma/chroma "$BACKUP_DIR/chroma-data"

# Backup configuration
cp -r production/config "$BACKUP_DIR/"

# Backup logs
cp -r production/logs "$BACKUP_DIR/" 2>/dev/null || true

echo "✅ Backup erstellt: $BACKUP_DIR"
EOF

    # Make scripts executable
    chmod +x production/scripts/*.sh
    
    log_success "Produktions-Skripte erstellt"
}

main() {
    log_info "Starte Production Setup..."
    
    check_requirements
    setup_environment
    setup_backend
    setup_frontend
    setup_docker
    setup_nginx
    setup_systemd
    setup_monitoring
    create_scripts
    
    log_success "🎉 Production Setup abgeschlossen!"
    
    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════════╗"
    echo -e "║                                                                  ║"
    echo -e "║  ✅ KI-Wissenssystem ist bereit für den produktiven Einsatz!    ║"
    echo -e "║                                                                  ║"
    echo -e "║  Nächste Schritte:                                              ║"
    echo -e "║  1. Konfiguriere production/config/.env                         ║"
    echo -e "║  2. Starte mit: ./production/scripts/start-production.sh        ║"
    echo -e "║  3. Überwache mit: ./production/scripts/health-check.sh         ║"
    echo -e "║                                                                  ║"
    echo -e "╚══════════════════════════════════════════════════════════════════╝${NC}"
}

# Führe Setup aus
main "$@" 