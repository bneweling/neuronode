# 🚀 Neuronode Production Deployment Guide

Umfassende Anleitung für den produktiven Einsatz des Neuronodes mit Docker, Monitoring und automatisierten Deployments.

> **📚 Navigation**: [🏠 Hauptdokumentation](README.md) | [🌐 Web-App Guide](README-WEBAPP.md) | [📖 Dokumentationsübersicht](docs/README.md)

## 📋 Inhalt

- [Quick Start](#quick-start)
- [System-Anforderungen](#system-anforderungen)
- [Installation](#installation)
- [Konfiguration](#konfiguration)
- [Deployment-Strategien](#deployment-strategien)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Wartung & Updates](#wartung--updates)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

## 🚀 Quick Start

```bash
# 1. Repository klonen und in Projekt-Verzeichnis wechseln
git clone <repository-url>
cd neuronode-main

# 2. Production Setup ausführen
chmod +x production-setup.sh
./production-setup.sh

# 3. Environment konfigurieren
cp production-env.template production/config/.env
nano production/config/.env  # Passwörter und API-Keys anpassen

# 4. Erstes Deployment
chmod +x deploy.sh
./deploy.sh fresh

# 5. Status prüfen
./deploy.sh status
```

## 💻 System-Anforderungen

### Minimale Anforderungen
- **CPU**: 4 Kerne
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **OS**: Ubuntu 20.04+, CentOS 8+, Debian 11+

### Empfohlene Anforderungen
- **CPU**: 8 Kerne
- **RAM**: 16 GB
- **Storage**: 100 GB SSD
- **Network**: 1 Gbps

### Software-Dependencies
- Docker 24.0+
- Docker Compose 2.20+
- Git 2.30+
- curl, wget
- Optional: Nginx (für Load Balancing)

## 📦 Installation

### 1. System vorbereiten

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose git curl wget

# CentOS/RHEL
sudo yum update -y
sudo yum install -y docker docker-compose git curl wget

# Docker Service starten
sudo systemctl enable docker
sudo systemctl start docker

# User zu docker group hinzufügen
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Automatisiertes Setup

```bash
# Haupt-Setup-Script ausführen
./production-setup.sh
```

Das Script erstellt automatisch:
- Produktions-Verzeichnisstruktur
- Docker-Konfigurationen
- Nginx-Setup
- Monitoring-Stack
- Backup-System
- Systemd-Services

## ⚙️ Konfiguration

### Environment-Datei (`production/config/.env`)

```bash
# Kopiere Template und bearbeite
cp production-env.template production/config/.env
```

**Wichtige Konfigurationen:**

#### 1. Sicherheit (KRITISCH - ÄNDERN!)
```env
# Datenbank-Passwörter
NEO4J_PASSWORD=secure_neo4j_password_change_me
REDIS_PASSWORD=secure_redis_password_change_me
CHROMA_AUTH_PASSWORD=secure_chroma_password_change_me

# JWT & Sessions
JWT_SECRET=your_super_secure_jwt_secret_change_me_minimum_32_characters
SESSION_SECRET=your_super_secure_session_secret_change_me

# Admin-Zugänge
GRAFANA_PASSWORD=secure_grafana_password_change_me
```

#### 2. AI-Provider
```env
# OpenAI (Standard)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Alternative: Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# Alternative: Google Gemini
GOOGLE_API_KEY=your-google-api-key-here
```

#### 3. Domains & URLs
```env
# Produktive URLs anpassen
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_APP_URL=https://your-domain.com
CORS_ORIGINS=https://your-domain.com,https://api.your-domain.com
```

### SSL/TLS Zertifikate

#### Option 1: Let's Encrypt (Automatisch)
```bash
# Let's Encrypt Konfiguration in .env
LETSENCRYPT_EMAIL=admin@your-domain.com
LETSENCRYPT_DOMAINS=your-domain.com,api.your-domain.com

# Zertifikate generieren
./production/scripts/setup-ssl.sh
```

#### Option 2: Eigene Zertifikate
```bash
# Zertifikate in SSL-Verzeichnis kopieren
cp your-cert.pem production/ssl/cert.pem
cp your-key.pem production/ssl/key.pem
cp dhparam.pem production/ssl/dhparam.pem
```

## 🚀 Deployment-Strategien

### 1. Fresh Deployment (Erstinstallation)
```bash
./deploy.sh fresh
```
- Komplette Neuinstallation
- Automatisches Setup
- Initialisierung aller Services

### 2. Rolling Update (Zero-Downtime)
```bash
./deploy.sh update
```
- Automatisches Backup
- Services nacheinander aktualisieren
- Health-Checks
- Rollback bei Fehlern möglich

### 3. Rollback
```bash
./deploy.sh rollback
```
- Zurück zur letzten funktionierenden Version
- Automatische Datenbank-Wiederherstellung

## 📊 Monitoring & Logging

### Übersicht Dashboard
```bash
# Monitoring-URLs anzeigen
./deploy.sh monitor
```

**Verfügbare Dashboards:**
- **Grafana**: http://localhost:3001 (Metriken & Dashboards)
- **Prometheus**: http://localhost:9090 (Metrics Collection)
- **Logs**: Via Grafana Loki Integration

### Wichtige Metriken
- **System**: CPU, RAM, Disk, Network
- **Application**: Response Times, Error Rates, Throughput
- **Database**: Query Performance, Connection Pools
- **AI**: Token Usage, Model Response Times

### Log-Management
```bash
# Live-Logs anzeigen
./deploy.sh logs                    # Alle Services
./deploy.sh logs backend           # Nur Backend
./deploy.sh logs frontend          # Nur Frontend

# Log-Dateien
production/logs/nginx/             # Nginx Access/Error Logs
production/logs/backend/           # Backend Application Logs
production/logs/monitoring/        # Monitoring System Logs
```

## 💾 Backup & Recovery

### Automatisches Backup
```bash
# Cron-Job wird automatisch eingerichtet
# Standard: Täglich 02:00 Uhr
# Konfiguration: BACKUP_SCHEDULE in .env
```

### Manuelles Backup
```bash
# Sofortiges Backup erstellen
./deploy.sh backup
```

### Backup-Umfang
- **Neo4j Datenbank**: Graph-Daten, Indizes
- **ChromaDB**: Vektor-Embeddings
- **Redis**: Cache & Sessions
- **Konfiguration**: .env, Certificates
- **Logs**: Aktuelle Log-Dateien

### Recovery
```bash
# Automatisches Recovery bei Rollback
./deploy.sh rollback

# Manuelles Recovery
BACKUP_DIR="production/backups/20240101_120000"
./production/scripts/restore-backup.sh "$BACKUP_DIR"
```

## 🔧 Wartung & Updates

### Regelmäßige Wartung
```bash
# Wöchentliche Cleanup-Routine
./deploy.sh cleanup
```
- Entfernt alte Docker-Images
- Bereinigt Log-Dateien
- Löscht alte Backups

### System-Updates
```bash
# 1. System-Updates
sudo apt update && sudo apt upgrade -y

# 2. Docker-Updates
sudo apt install docker.io docker-compose

# 3. Application-Update
git pull origin main
./deploy.sh update
```

### Health-Checks
```bash
# System-Status prüfen
./deploy.sh status

# Kontinuierliche Überwachung
watch -n 10 './deploy.sh status'
```

## 🛠️ Troubleshooting

### Häufige Probleme

#### 1. Services starten nicht
```bash
# Logs prüfen
./deploy.sh logs

# Container-Status
docker-compose -f docker-compose.production.yml ps

# Neustart versuchen
./deploy.sh restart
```

#### 2. Datenbank-Verbindungsfehler
```bash
# Neo4j Status prüfen
docker exec ki-prod-neo4j cypher-shell -u neo4j -p your_password "RETURN 1"

# Passwort in .env prüfen
grep NEO4J_PASSWORD production/config/.env
```

#### 3. Performance-Probleme
```bash
# Resource-Usage prüfen
docker stats

# System-Metriken
htop
iostat -x 1
```

#### 4. SSL-Zertifikat-Probleme
```bash
# Zertifikat-Status prüfen
openssl x509 -in production/ssl/cert.pem -text -noout

# Nginx-Konfiguration testen
docker exec ki-prod-nginx nginx -t
```

### Debug-Modus
```bash
# Detaillierte Logs aktivieren
export DEBUG=true
LOG_LEVEL=DEBUG ./deploy.sh start
```

## 🔒 Security

### Best Practices

#### 1. Passwort-Sicherheit
- Alle Standard-Passwörter ändern
- Starke Passwörter verwenden (min. 20 Zeichen)
- Regelmäßige Passwort-Rotation

#### 2. Network-Sicherheit
```bash
# Firewall konfigurieren
sudo ufw enable
sudo ufw allow 22      # SSH
sudo ufw allow 80      # HTTP
sudo ufw allow 443     # HTTPS
sudo ufw deny 8080     # Backend (nur intern)
sudo ufw deny 3000     # Frontend (nur intern)
```

#### 3. SSL/TLS
- HTTPS erzwingen
- Starke Cipher-Suites
- HSTS aktivieren

#### 4. Monitoring
- Fail2Ban für SSH
- Log-Monitoring
- Intrusion Detection

### Security-Checkliste
- [ ] Alle Standard-Passwörter geändert
- [ ] SSL-Zertifikate installiert
- [ ] Firewall konfiguriert
- [ ] Fail2Ban aktiviert
- [ ] Backup-Verschlüsselung
- [ ] Log-Monitoring eingerichtet
- [ ] Security-Updates automatisiert

## 📈 Performance-Tuning

### System-Optimierung
```bash
# Docker-Performance
echo 'DOCKER_OPTS="--storage-driver=overlay2"' >> /etc/default/docker

# System-Limits
echo '* soft nofile 65536' >> /etc/security/limits.conf
echo '* hard nofile 65536' >> /etc/security/limits.conf
```

### Application-Tuning
```env
# Backend-Performance (.env)
GUNICORN_WORKERS=8                    # CPU-Kerne * 2
GUNICORN_WORKER_CONNECTIONS=2000      # Concurrent Connections
DB_POOL_SIZE=30                       # Database Connection Pool

# Neo4j-Tuning
NEO4J_PAGECACHE=4G                    # 50% des verfügbaren RAMs
NEO4J_HEAP=4G                         # 25% des verfügbaren RAMs
```

## 📞 Support & Community

### Dokumentation
- [API-Dokumentation](./API.md)
- [Frontend-Guide](./FRONTEND.md)
- [Backend-Guide](./BACKEND.md)

### Support-Kanäle
- **Issues**: GitHub Issues für Bug-Reports
- **Discussions**: GitHub Discussions für Fragen
- **Wiki**: Erweiterte Dokumentation

### Mitwirken
1. Fork des Repositories
2. Feature-Branch erstellen
3. Tests hinzufügen
4. Pull Request erstellen

---

## 🎯 Checkliste für Production-Deployment

### Vor dem Deployment
- [ ] System-Anforderungen erfüllt
- [ ] Dependencies installiert
- [ ] Environment-Datei konfiguriert
- [ ] SSL-Zertifikate bereitgestellt
- [ ] Firewall konfiguriert
- [ ] DNS-Einträge gesetzt

### Nach dem Deployment
- [ ] Health-Checks bestanden
- [ ] Monitoring-Dashboards erreichbar
- [ ] Backup-System funktional
- [ ] SSL-Verbindung getestet
- [ ] Performance-Tests durchgeführt
- [ ] Security-Scan absolviert

### Regelmäßige Wartung
- [ ] Wöchentliche Cleanup-Routine
- [ ] Monatliche Security-Updates
- [ ] Quartalsweise Backup-Tests
- [ ] Jährliche Security-Audits

---

**Happy Deploying! 🚀**

Bei Fragen oder Problemen öffnen Sie bitte ein Issue oder starten eine Discussion im Repository. 