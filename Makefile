# 🧠 KI-Wissenssystem - Makefile
# Zentrales Build- und Management-System

.PHONY: help setup dev test lint format clean docs production backup monitoring

# ====== HILFE ======
help: ## 📖 Zeigt alle verfügbaren Kommandos
	@echo "🧠 KI-Wissenssystem - Verfügbare Kommandos:"
	@echo ""
	@echo "🚀 ENTWICKLUNG:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "📚 Dokumentation: docs/README.md"
	@echo "🏭 Production: PRODUCTION-DEPLOYMENT.md"

# ====== SETUP & INSTALLATION ======
setup: ## 🔧 Vollständiges System-Setup
	@echo "🔧 System wird eingerichtet..."
	./ki-wissenssystem/setup.sh
	cd ki-wissenssystem-webapp && npm install

setup-production: ## 🏭 Produktions-Setup
	@echo "🏭 Produktionsumgebung wird eingerichtet..."
	./production-setup.sh

# ====== ENTWICKLUNG ======
dev: ## 🚀 Entwicklungsmodus (Backend + Frontend)
	@echo "🚀 Entwicklungsmodus wird gestartet..."
	@echo "Terminal 1: Backend Services..."
	cd ki-wissenssystem && ./start-all.sh &
	@echo "Terminal 2: Frontend Development Server..."
	cd ki-wissenssystem-webapp && npm run dev

dev-backend: ## 🔧 Nur Backend Development
	@echo "🔧 Backend wird gestartet..."
	cd ki-wissenssystem && ./dev-mode.sh

dev-frontend: ## 🌐 Nur Frontend Development
	@echo "🌐 Frontend wird gestartet..."
	cd ki-wissenssystem-webapp && npm run dev

dev-plugin: ## 📔 Plugin Development
	@echo "📔 Plugin wird entwickelt..."
	cd obsidian-ki-plugin && npm run dev

# ====== TESTS ======
test: ## 🧪 Alle Tests ausführen
	@echo "🧪 Tests werden ausgeführt..."
	cd ki-wissenssystem && python -m pytest tests/ -v
	cd ki-wissenssystem-webapp && npm test
	cd obsidian-ki-plugin && npm test

test-backend: ## 🔬 Backend Tests
	@echo "🔬 Backend Tests..."
	cd ki-wissenssystem && python -m pytest tests/ -v --cov=src/

test-frontend: ## 🎯 Frontend Tests
	@echo "🎯 Frontend Tests..."
	cd ki-wissenssystem-webapp && npm test

test-e2e: ## 🔄 End-to-End Tests
	@echo "🔄 E2E Tests..."
	cd ki-wissenssystem-webapp && npm run test:e2e

# ====== CODE QUALITY ======
lint: ## ✅ Code Linting
	@echo "✅ Code wird analysiert..."
	cd ki-wissenssystem && python -m flake8 src/
	cd ki-wissenssystem && python -m mypy src/
	cd ki-wissenssystem-webapp && npm run lint
	cd obsidian-ki-plugin && npm run lint

format: ## 🎨 Code formatieren
	@echo "🎨 Code wird formatiert..."
	cd ki-wissenssystem && python -m black src/
	cd ki-wissenssystem && python -m isort src/
	cd ki-wissenssystem-webapp && npm run format
	cd obsidian-ki-plugin && npm run format

typecheck: ## 📝 TypeScript Type Checking
	@echo "📝 TypeScript wird überprüft..."
	cd ki-wissenssystem-webapp && npm run type-check
	cd obsidian-ki-plugin && npm run type-check

security-check: ## 🔒 Security Scanning
	@echo "🔒 Sicherheit wird überprüft..."
	cd ki-wissenssystem && python -m safety check
	cd ki-wissenssystem-webapp && npm audit
	cd obsidian-ki-plugin && npm audit

# ====== BUILD ======
build: ## 🏗️ Alles bauen
	@echo "🏗️ System wird gebaut..."
	cd ki-wissenssystem-webapp && npm run build
	cd obsidian-ki-plugin && npm run build

build-frontend: ## 🌐 Frontend bauen
	@echo "🌐 Frontend wird gebaut..."
	cd ki-wissenssystem-webapp && npm run build

build-plugin: ## 📔 Plugin bauen
	@echo "📔 Plugin wird gebaut..."
	cd obsidian-ki-plugin && npm run build

build-docker: ## 🐳 Docker Images bauen
	@echo "🐳 Docker Images werden gebaut..."
	cd ki-wissenssystem && docker-compose build
	cd ki-wissenssystem-webapp && docker build -t ki-webapp .

# ====== SERVICES ======
start: ## ▶️ Services starten
	@echo "▶️ Services werden gestartet..."
	cd ki-wissenssystem && ./start-all.sh

stop: ## ⏹️ Services stoppen
	@echo "⏹️ Services werden gestoppt..."
	cd ki-wissenssystem && ./stop-all.sh

restart: ## 🔄 Services neustarten
	@echo "🔄 Services werden neugestartet..."
	make stop
	make start

status: ## 📊 Service Status
	@echo "📊 Service Status:"
	cd ki-wissenssystem && docker-compose ps

logs: ## 📋 Service Logs
	@echo "📋 Service Logs:"
	cd ki-wissenssystem && docker-compose logs -f

# ====== PRODUCTION ======
production-deploy: ## 🚀 Production Deployment
	@echo "🚀 Production Deployment wird gestartet..."
	./deploy.sh fresh

production-update: ## 🔄 Production Update
	@echo "🔄 Production Update..."
	./deploy.sh update

production-rollback: ## ⏪ Production Rollback
	@echo "⏪ Production Rollback..."
	./deploy.sh rollback

production-status: ## 📈 Production Status
	@echo "📈 Production Status:"
	./deploy.sh status

# ====== BACKUP & MONITORING ======
backup: ## 💾 Backup erstellen
	@echo "💾 Backup wird erstellt..."
	./deploy.sh backup

monitoring: ## 📊 Monitoring Dashboard öffnen
	@echo "📊 Monitoring wird geöffnet..."
	./deploy.sh monitor

# ====== DOKUMENTATION ======
docs: ## 📚 Dokumentation generieren
	@echo "📚 Dokumentation wird generiert..."
	@echo "Hauptdokumentation: README.md"
	@echo "Dokumentationsübersicht: docs/README.md"
	@echo "Web-App Guide: README-WEBAPP.md"
	@echo "Production Guide: PRODUCTION-DEPLOYMENT.md"
	@echo "Development Guide: ENTWICKLUNG.md"

docs-serve: ## 🌐 Dokumentation lokal servieren
	@echo "🌐 Dokumentation wird serviert auf http://localhost:8080"
	python -m http.server 8080

docs-validate: ## ✅ Dokumentations-Links prüfen
	@echo "✅ Dokumentations-Links werden geprüft..."
	@echo "Überprüfung der Markdown-Links:"
	find . -name "*.md" -not -path "./node_modules/*" -not -path "./ki-wissenssystem-webapp/node_modules/*" -not -path "./obsidian-ki-plugin/node_modules/*" -not -path "./ki-wissenssystem/venv/*" | xargs grep -l "](.*\.md)" | head -5

# ====== CLEANUP ======
clean: ## 🧹 Aufräumen
	@echo "🧹 System wird aufgeräumt..."
	cd ki-wissenssystem && docker-compose down
	docker system prune -f
	cd ki-wissenssystem-webapp && rm -rf .next node_modules/.cache
	cd obsidian-ki-plugin && rm -rf dist

clean-all: ## 🗑️ Vollständige Bereinigung
	@echo "🗑️ Vollständige Bereinigung..."
	make clean
	cd ki-wissenssystem-webapp && rm -rf node_modules
	cd obsidian-ki-plugin && rm -rf node_modules
	cd ki-wissenssystem && rm -rf venv __pycache__

# ====== UTILITIES ======
install-deps: ## 📦 Dependencies installieren
	@echo "📦 Dependencies werden installiert..."
	cd ki-wissenssystem && pip install -r requirements.txt
	cd ki-wissenssystem-webapp && npm install
	cd obsidian-ki-plugin && npm install

update-deps: ## 🔄 Dependencies aktualisieren
	@echo "🔄 Dependencies werden aktualisiert..."
	cd ki-wissenssystem && pip install --upgrade -r requirements.txt
	cd ki-wissenssystem-webapp && npm update
	cd obsidian-ki-plugin && npm update

health-check: ## 🏥 System Health Check
	@echo "🏥 System Health Check:"
	@echo "Docker Status:"
	@docker --version || echo "❌ Docker nicht verfügbar"
	@echo "Node.js Status:"
	@node --version || echo "❌ Node.js nicht verfügbar"
	@echo "Python Status:"
	@python --version || echo "❌ Python nicht verfügbar"
	@echo "Services Status:"
	@cd ki-wissenssystem && docker-compose ps || echo "❌ Services nicht gestartet"

# ====== QUICK ACTIONS ======
quick-start: ## ⚡ Schnellstart für Entwicklung
	@echo "⚡ Schnellstart wird ausgeführt..."
	make setup
	make start
	make dev-frontend

reset: ## 🔄 System zurücksetzen
	@echo "🔄 System wird zurückgesetzt..."
	make clean-all
	make setup

# Default target
.DEFAULT_GOAL := help 