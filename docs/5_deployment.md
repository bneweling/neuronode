# 🚀 Deployment und Operations Guide

**Version:** 2.0 (K6 Knowledge Consolidation)  
**Datum:** Januar 2025  
**Zielgruppe:** DevOps, System-Administratoren, Entwickler  
**Status:** Produktions-ready mit bewährten Konfigurationen

---

## 🎯 Deployment-Übersicht

Das Neuronode kann in verschiedenen Umgebungen deployed werden: Development (lokale Entwicklung), Staging (Pre-Production Tests) und Production (Enterprise-Einsatz). Alle Deployment-Methoden sind getestet und dokumentiert.

### Verfügbare Deployment-Methoden

| Method | Use Case | Komplexität | Performance | Status |
|--------|----------|-------------|-------------|--------|
| Local Development | Entwicklung, Tests | Niedrig | Gut | ✅ Ready |
| Docker Compose | Staging, kleinere Production | Mittel | Sehr gut | ✅ Ready |
| Production Setup | Enterprise, skalierbare Deployments | Hoch | Excellent | ✅ Ready |

---

## 🏠 Development Environment Setup

### Lokales Development (macOS/Linux)

**Zeitaufwand:** 30 Minuten  
**Systemanforderungen:** 8GB RAM, 20GB Disk

#### 1. Quick Setup (Empfohlen)
```bash
# Repository klonen
git clone [repository-url] neuronode
cd neuronode

# Automatisches Setup (alles-in-einem)
./manage.sh dev-setup

# System starten
./manage.sh start

# Status prüfen
./manage.sh status
```

#### 2. Manuelles Setup (für Entwickler)
```bash
# Backend Dependencies
cd neuronode
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend Dependencies  
cd ../neuronode-webapp
npm install

# Services starten
cd ../neuronode
./scripts/system/start-all.sh

# Frontend Development Server
cd ../neuronode-webapp
npm run dev
```

#### 3. Service Configuration

**Backend (.env Konfiguration):**
```bash
# Copy template and customize
cp .env.example .env

# Essential Settings
LLM_PROVIDER=gemini  # oder openai, anthropic
LLM_MODEL=gemini-2.5-flash
API_HOST=localhost
API_PORT=8000

# Database URLs
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

CHROMA_HOST=localhost
CHROMA_PORT=8000

# API Keys (optional für Development)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Development Workflow

#### Service Management
```bash
# Alle Services starten
./manage.sh start

# Einzelne Services
./manage.sh start neo4j
./manage.sh start chroma
./manage.sh start api

# Services stoppen
./manage.sh stop

# Logs ansehen
./manage.sh logs
./manage.sh logs api  # Spezifischer Service
```

#### Model Profile Switching
```bash
# Aktuelles Profil anzeigen
./switch-model-profile.sh --show

# Profil wechseln
./switch-model-profile.sh balanced    # Empfohlen für Development
./switch-model-profile.sh cost_effective  # Günstig für Tests
./switch-model-profile.sh premium     # Beste Qualität

# Nach Profilwechsel System neu starten
./manage.sh restart
```

#### Testing im Development
```bash
# Backend Tests
cd neuronode
python -m pytest tests/

# Frontend Tests  
cd neuronode-webapp
npm test

# E2E Tests
npm run test:e2e

# Integration Tests
cd ../neuronode
python scripts/comprehensive_phase3_testing.py
```

---

## 🐳 Docker Compose Deployment

### Staging Environment

**Zeitaufwand:** 15 Minuten  
**Systemanforderungen:** 16GB RAM, 50GB Disk, Docker & Docker Compose

#### 1. Quick Staging Deployment
```bash
# Repository klonen
git clone [repository-url] neuronode
cd neuronode

# Staging Environment mit Docker
./manage.sh docker-staging

# Services prüfen
docker-compose ps
docker-compose logs -f
```

#### 2. Manueller Docker Setup
```bash
# Docker Compose für Staging
docker-compose -f docker-compose.staging.yml up -d

# Oder Production-ähnlich
docker-compose -f deployment/docker-compose.production.yml up -d
```

#### 3. Docker Service Configuration

**docker-compose.staging.yml (Beispiel-Auszug):**
```yaml
version: '3.8'
services:
  api:
    build: 
      context: ./neuronode
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - CHROMA_HOST=chroma
      - LLM_PROVIDER=gemini
    depends_on:
      - neo4j
      - chroma
      - redis
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  webapp:
    build:
      context: ./neuronode-webapp
      dockerfile: Dockerfile.production
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - api

  neo4j:
    image: neo4j:5.15
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/password
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs

  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    environment:
      CHROMA_SERVER_HOST: 0.0.0.0
    volumes:
      - chroma_data:/chroma/chroma

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  neo4j_data:
  neo4j_logs:
  chroma_data:
  redis_data:
```

#### 4. Docker Management

```bash
# Container Status
docker-compose ps

# Logs verfolgen
docker-compose logs -f api
docker-compose logs -f webapp

# Container neu starten
docker-compose restart api

# Datenbank-Backup
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/var/lib/neo4j/backups/backup.dump

# Services skalieren (wenn nötig)
docker-compose up -d --scale api=2
```

---

## 🏭 Production Deployment

### Enterprise Production Setup

**Zeitaufwand:** 2-4 Stunden  
**Systemanforderungen:** 32GB RAM, 500GB SSD, Load Balancer, SSL Certs

#### 1. Production Server Requirements

**Minimale Hardware:**
```yaml
CPU: 8 Cores (16 recommended)
RAM: 32GB (64GB recommended)
Storage: 500GB SSD (NVMe preferred)
Network: 1Gbps
```

**Empfohlene Server-Konfiguration:**
```yaml
Application Server:
  CPU: 16 Cores
  RAM: 64GB
  Storage: 1TB NVMe SSD
  
Database Server (optional separate):
  CPU: 8 Cores  
  RAM: 32GB
  Storage: 2TB SSD (Neo4j + ChromaDB)
  
Load Balancer:
  CPU: 4 Cores
  RAM: 8GB
  Storage: 100GB SSD
```

#### 2. Production Deployment Steps

**Step 1: Server Preparation**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install nginx (reverse proxy)
sudo apt install nginx certbot python3-certbot-nginx -y
```

**Step 2: Application Deployment**
```bash
# Clone and prepare
git clone [repository-url] /opt/neuronode
cd /opt/neuronode

# Production configuration
cp deployment/production-env.template .env
# Edit .env with production settings

# Deploy with production compose
docker-compose -f deployment/docker-compose.production.yml up -d

# Verify deployment
docker-compose ps
```

**Step 3: SSL and Reverse Proxy Setup**
```bash
# Nginx configuration
sudo cp deployment/nginx.production.conf /etc/nginx/sites-available/neuronode
sudo ln -s /etc/nginx/sites-available/neuronode /etc/nginx/sites-enabled/
sudo nginx -t

# SSL Certificate (Let's Encrypt)
sudo certbot --nginx -d your-domain.com
sudo systemctl reload nginx
```

#### 3. Production Configuration

**Production Environment (.env):**
```bash
# Application Settings
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# LLM Configuration (Production-optimized)
LLM_PROVIDER=gemini
MODEL_PROFILE=balanced  # Recommended for production

# Database Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=strong_production_password

CHROMA_HOST=chroma
CHROMA_PORT=8000

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=strong_redis_password

# Security Settings
JWT_SECRET=very_long_random_string_here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ORIGINS=https://your-domain.com

# API Keys (Production)
OPENAI_API_KEY=prod_openai_key
ANTHROPIC_API_KEY=prod_anthropic_key
GOOGLE_API_KEY=prod_google_key

# Monitoring
SENTRY_DSN=your_sentry_dsn  # Optional
```

**Nginx Production Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Frontend (Next.js)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # API Backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket Support
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # File Upload (increased limits)
    client_max_body_size 100M;
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
}
```

#### 4. Production Monitoring und Maintenance

**System Monitoring:**
```bash
# System Health Check
./manage.sh health-check

# Performance Monitoring
docker stats

# Log Management
docker-compose logs --tail=100 -f api
docker-compose logs --tail=100 -f webapp

# Database Backup (täglich)
./scripts/backup/backup-neo4j.sh
./scripts/backup/backup-chroma.sh
```

**Automated Backups (Crontab):**
```bash
# Backup databases täglich um 2:00 Uhr
0 2 * * * /opt/neuronode/scripts/backup/daily-backup.sh

# Log rotation wöchentlich
0 3 * * 0 /opt/neuronode/scripts/maintenance/rotate-logs.sh

# System health check alle 15 Minuten
*/15 * * * * /opt/neuronode/manage.sh health-check
```

---

## 🔧 Service Management und Operations

### Systemd Service Setup (Production)

**API Service:**
```bash
# /etc/systemd/system/ki-api.service
sudo tee /etc/systemd/system/ki-api.service << EOF
[Unit]
Description=Neuronode API
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/neuronode
ExecStart=/usr/local/bin/docker-compose -f deployment/docker-compose.production.yml up -d
ExecStop=/usr/local/bin/docker-compose -f deployment/docker-compose.production.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Service aktivieren
sudo systemctl enable ki-api.service
sudo systemctl start ki-api.service
```

### Log Management

**Log Locations:**
```bash
# Application Logs
/opt/neuronode/logs/api.log
/opt/neuronode/logs/processing.log
/opt/neuronode/logs/graph-gardener.log

# Database Logs
docker-compose logs neo4j
docker-compose logs chroma

# Nginx Logs
/var/log/nginx/access.log
/var/log/nginx/error.log
```

**Log Rotation Configuration:**
```bash
# /etc/logrotate.d/neuronode
/opt/neuronode/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

### Performance Monitoring

#### System Metrics
```bash
# CPU und Memory Usage
htop
docker stats

# Disk Usage
df -h
du -sh /opt/neuronode/

# Network Monitoring
netstat -tulpn | grep :8000
netstat -tulpn | grep :3000
```

#### Application Metrics
```bash
# API Performance
curl -X GET "http://localhost:8000/health" -w "@curl-format.txt"

# Database Performance
docker-compose exec neo4j cypher-shell -u neo4j -p password "SHOW DATABASES"

# Memory Usage per Service
docker-compose exec api ps aux
docker-compose exec neo4j ps aux
```

---

## 🔄 Updates und Maintenance

### Rolling Updates (Zero-Downtime)

```bash
# Backup vor Update
./scripts/backup/pre-update-backup.sh

# Git Update
git pull origin main

# Service Update (Rolling)
docker-compose -f deployment/docker-compose.production.yml pull
docker-compose -f deployment/docker-compose.production.yml up -d --no-deps api
docker-compose -f deployment/docker-compose.production.yml up -d --no-deps webapp

# Health Check nach Update
./manage.sh health-check
```

### Database Maintenance

**Neo4j Maintenance:**
```bash
# Database Statistics
docker-compose exec neo4j cypher-shell -u neo4j -p password "CALL dbms.showCurrentUser()"

# Index Management
docker-compose exec neo4j cypher-shell -u neo4j -p password "SHOW INDEXES"

# Cleanup unused nodes (optional)
docker-compose exec neo4j cypher-shell -u neo4j -p password "MATCH (n) WHERE size((n)--()) = 0 DELETE n"
```

**ChromaDB Maintenance:**
```bash
# Collection Statistics
curl -X GET "http://localhost:8000/api/v1/collections"

# Database Compaction (bei Bedarf)
docker-compose restart chroma
```

### Security Updates

```bash
# System Updates
sudo apt update && sudo apt upgrade -y

# Docker Image Updates
docker-compose pull
docker-compose up -d

# SSL Certificate Renewal
sudo certbot renew --nginx

# Security Scan (optional)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image neuronode_api:latest
```

---

## 🚨 Troubleshooting und Disaster Recovery

### Häufige Probleme und Lösungen

#### 1. Services starten nicht
```bash
# Check Docker
docker --version
docker-compose --version

# Check Ports
sudo netstat -tulpn | grep :8000
sudo lsof -i :8000

# Restart Services
docker-compose down
docker-compose up -d
```

#### 2. Database Connection Issues
```bash
# Neo4j Connection Test
docker-compose exec neo4j cypher-shell -u neo4j -p password "RETURN 1"

# ChromaDB Connection Test
curl -X GET "http://localhost:8000/api/v1/heartbeat"

# Reset Database (Development only!)
docker-compose down -v
docker-compose up -d
```

#### 3. Memory Issues
```bash
# Check Memory Usage
free -h
docker stats --no-stream

# Clear Docker Cache
docker system prune -a

# Restart Memory-heavy Services
docker-compose restart api
docker-compose restart neo4j
```

#### 4. SSL/Certificate Issues
```bash
# Check Certificate Status
sudo certbot certificates

# Renew Certificate
sudo certbot renew --nginx

# Test Nginx Configuration
sudo nginx -t
sudo systemctl reload nginx
```

### Disaster Recovery

#### 1. Complete System Backup
```bash
# Automated Backup Script
./scripts/backup/full-system-backup.sh

# Manual Backup
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j-$(date +%Y%m%d).dump
docker-compose exec chroma cp -r /chroma/chroma /backups/chroma-$(date +%Y%m%d)/
cp -r /opt/neuronode/data /backups/application-data-$(date +%Y%m%d)/
```

#### 2. System Recovery
```bash
# Stop Services
docker-compose down

# Restore Databases
docker-compose exec neo4j neo4j-admin load --from=/backups/neo4j-backup.dump --database=neo4j --force
docker-compose exec chroma cp -r /backups/chroma-backup/ /chroma/

# Restart Services
docker-compose up -d

# Verify Recovery
./manage.sh health-check
```

#### 3. Emergency Procedures
```bash
# Service Failover (bei kritischen Fehlern)
./scripts/emergency/failover-to-backup.sh

# Emergency Shutdown
./scripts/emergency/emergency-shutdown.sh

# System Recovery Mode
./scripts/emergency/recovery-mode.sh
```

---

## 📈 Scaling und Performance Optimization

### Horizontal Scaling

#### Load Balancer Setup
```bash
# HAProxy Configuration (Beispiel)
# /etc/haproxy/haproxy.cfg
global
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend ki_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/neuronode.pem
    redirect scheme https if !{ ssl_fc }
    default_backend ki_backend

backend ki_backend
    balance roundrobin
    server ki1 10.0.0.10:3000 check
    server ki2 10.0.0.11:3000 check
    server ki3 10.0.0.12:3000 check
```

#### Database Scaling
```bash
# Neo4j Clustering (Enterprise)
# Siehe Neo4j Cluster Documentation für Details

# ChromaDB Scaling
# Mehrere ChromaDB Instanzen mit Load Balancing
docker-compose -f docker-compose.cluster.yml up -d
```

### Vertical Scaling

#### Resource Optimization
```yaml
# docker-compose.production.yml (optimiert)
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
  
  neo4j:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 16G
        reservations:
          cpus: '2.0'
          memory: 8G
    environment:
      NEO4J_dbms_memory_heap_initial__size: 4G
      NEO4J_dbms_memory_heap_max__size: 8G
      NEO4J_dbms_memory_pagecache_size: 4G
```

---

## 📝 Deployment Checklist

### Pre-Deployment
- [ ] Server-Requirements erfüllt
- [ ] Environment Configuration überprüft
- [ ] API Keys und Secrets konfiguriert
- [ ] SSL Certificates bereit
- [ ] Backup-Strategy definiert
- [ ] Monitoring-Setup vorbereitet

### Deployment
- [ ] Git Repository geklont
- [ ] Docker Compose Services gestartet
- [ ] Database Connections getestet
- [ ] Nginx/Load Balancer konfiguriert
- [ ] SSL/TLS aktiviert
- [ ] Health Checks erfolgreich

### Post-Deployment
- [ ] End-to-End Tests ausgeführt
- [ ] Performance Monitoring aktiv
- [ ] Log Aggregation konfiguriert
- [ ] Backup Jobs aktiviert
- [ ] Incident Response Plan aktiviert
- [ ] Team Training durchgeführt

---

## 🎯 Fazit

Das Neuronode bietet **flexible Deployment-Optionen** für verschiedene Anwendungsszenarien:

### ✅ Production-Ready Features
- **Docker-basierte Deployments** für Konsistenz und Skalierbarkeit
- **Automated Service Management** mit systemd Integration
- **SSL/TLS Support** mit automatischer Certificate-Erneuerung
- **Comprehensive Monitoring** und Health Checks
- **Disaster Recovery** Procedures und Backup-Strategien

### 🎯 Empfohlene Deployment-Strategie
1. **Development:** Lokales Setup mit `./manage.sh dev-setup`
2. **Staging:** Docker Compose mit `docker-compose.staging.yml`
3. **Production:** Full Enterprise Setup mit Load Balancer und SSL

**Das System ist bereit für Enterprise-Deployments mit bewährten DevOps-Praktiken und umfassender Dokumentation.**
