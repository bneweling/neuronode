#!/bin/bash
# install-obsidian-plugin.sh - Installiert das KI-Wissenssystem Plugin automatisch

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔌 KI-Wissenssystem Plugin Installation${NC}"
echo

# Prüfe System-Anforderungen
echo -e "${BLUE}🔧 Prüfe System-Anforderungen...${NC}"

# Node.js Version prüfen
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    echo -e "${GREEN}✅ Node.js gefunden: v$NODE_VERSION${NC}"
    
    # Mindestversion prüfen (>=16)
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1)
    if [ $NODE_MAJOR -lt 16 ]; then
        echo -e "${YELLOW}⚠️  Node.js Version $NODE_VERSION ist alt. Empfohlen: >=16.0.0${NC}"
    fi
else
    echo -e "${RED}❌ Node.js nicht gefunden${NC}"
    echo "Bitte installieren Sie Node.js von: https://nodejs.org/"
    exit 1
fi

# NPM Version prüfen
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✅ npm gefunden: v$NPM_VERSION${NC}"
else
    echo -e "${RED}❌ npm nicht gefunden${NC}"
    exit 1
fi

# Prüfe ob Plugin-Verzeichnis existiert
PLUGIN_SOURCE="../obsidian-ki-plugin"
if [ ! -d "$PLUGIN_SOURCE" ]; then
    echo -e "${RED}❌ Plugin-Quellverzeichnis nicht gefunden: $PLUGIN_SOURCE${NC}"
    echo "Bitte stellen Sie sicher, dass das obsidian-ki-plugin Verzeichnis existiert."
    exit 1
fi

echo -e "${GREEN}✅ System-Anforderungen erfüllt${NC}"
echo

# Prüfe Dependencies und Build-Status
echo -e "${BLUE}📦 Prüfe Plugin-Status...${NC}"
cd "$PLUGIN_SOURCE"

# Dependencies prüfen
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  Dependencies nicht installiert. Installiere...${NC}"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Dependency-Installation fehlgeschlagen${NC}"
        exit 1
    fi
fi

# TypeScript Compilation Check
echo -e "${BLUE}🔍 Prüfe TypeScript-Code...${NC}"
npx tsc --noEmit --skipLibCheck
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ TypeScript-Fehler gefunden. Bitte beheben Sie die Fehler vor der Installation.${NC}"
    exit 1
fi

# Build Plugin falls nötig
if [ ! -f "main.js" ] || [ "main.ts" -nt "main.js" ]; then
    echo -e "${YELLOW}⚠️  Plugin muss neu gebaut werden...${NC}"
    npm run build
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Plugin-Build fehlgeschlagen${NC}"
        exit 1
    fi
fi

# Plugin-Dateien prüfen
REQUIRED_FILES=("main.js" "manifest.json" "styles.css")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Erforderliche Datei fehlt: $file${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ Plugin ist bereit${NC}"
cd - > /dev/null

# Features-Info anzeigen
echo -e "${BLUE}🚀 Plugin-Features:${NC}"
echo "  • 💬 Persistente Chat-Historie mit Sitzungsverwaltung"
echo "  • 🔍 Erweiterte Graph-Suche (Semantisch, Exakt, Fuzzy, Graph-Walk)"
echo "  • ⚖️ Einheitliche Workbench mit 4 Layout-Modi"
echo "  • 🕸️ Interaktive Knowledge Graph Visualisierung"
echo "  • 📊 Live-Statistiken und Kategorien-Filter"
echo "  • 📱 Responsive Design für Desktop und Mobile"
echo

# Finde Obsidian-Vaults
OBSIDIAN_CONFIG="$HOME/Library/Application Support/obsidian/obsidian.json"

if [ ! -f "$OBSIDIAN_CONFIG" ]; then
    echo -e "${RED}❌ Obsidian-Konfiguration nicht gefunden${NC}"
    echo "Pfad: $OBSIDIAN_CONFIG"
    echo "Bitte starten Sie Obsidian mindestens einmal."
    exit 1
fi

echo -e "${BLUE}📁 Verfügbare Vaults:${NC}"

# Parse Vaults und zeige Auswahl
VAULT_PATHS=()
VAULT_NAMES=()

python3 << 'EOF'
import json
import os
import sys

try:
    with open(os.path.expanduser('~/Library/Application Support/obsidian/obsidian.json'), 'r') as f:
        config = json.load(f)
    
    vaults = config.get('vaults', {})
    if not vaults:
        print("Keine Vaults gefunden.")
        sys.exit(1)
    
    vault_info = []
    for i, (vault_id, vault_data) in enumerate(vaults.items(), 1):
        vault_path = vault_data.get('path', '')
        vault_name = os.path.basename(vault_path)
        vault_info.append((i, vault_name, vault_path))
        print(f"{i}. {vault_name}")
        print(f"   Pfad: {vault_path}")
        
        # Prüfe Plugin-Status
        plugin_path = os.path.join(vault_path, '.obsidian', 'plugins', 'obsidian-ki-plugin')
        if os.path.exists(plugin_path):
            print(f"   Status: ✅ Plugin bereits installiert")
            # Prüfe Version
            manifest_path = os.path.join(plugin_path, 'manifest.json')
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                        version = manifest.get('version', 'unknown')
                        print(f"   Version: {version}")
                except:
                    print(f"   Version: unbekannt")
        else:
            print(f"   Status: ⚪ Plugin nicht installiert")
        
        # Prüfe Vault-Größe
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(vault_path):
                for filename in filenames:
                    if filename.endswith(('.md', '.txt')):
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
            
            if total_size > 0:
                size_mb = total_size / (1024 * 1024)
                print(f"   Größe: {size_mb:.1f} MB ({len([f for f in os.listdir(vault_path) if f.endswith('.md')])} Markdown-Dateien)")
        except:
            pass
        
        print()
    
    # Schreibe Vault-Info in temporäre Datei für Bash
    with open('/tmp/vault_info.txt', 'w') as f:
        for i, name, path in vault_info:
            f.write(f"{i}|{name}|{path}\n")

except Exception as e:
    print(f"Fehler beim Lesen der Konfiguration: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi

# Benutzer-Auswahl
echo -n "Welchen Vault möchten Sie verwenden? (Nummer eingeben): "
read VAULT_CHOICE

# Validiere Auswahl und hole Pfad
SELECTED_VAULT_PATH=""
while IFS='|' read -r num name path; do
    if [ "$num" = "$VAULT_CHOICE" ]; then
        SELECTED_VAULT_PATH="$path"
        SELECTED_VAULT_NAME="$name"
        break
    fi
done < /tmp/vault_info.txt

rm -f /tmp/vault_info.txt

if [ -z "$SELECTED_VAULT_PATH" ]; then
    echo -e "${RED}❌ Ungültige Auswahl${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Ausgewählter Vault: $SELECTED_VAULT_NAME${NC}"
echo "Pfad: $SELECTED_VAULT_PATH"

# Erstelle Plugin-Verzeichnis
PLUGIN_TARGET="$SELECTED_VAULT_PATH/.obsidian/plugins/obsidian-ki-plugin"
echo

# Prüfe ob .obsidian existiert
OBSIDIAN_DIR="$SELECTED_VAULT_PATH/.obsidian"
if [ ! -d "$OBSIDIAN_DIR" ]; then
    echo -e "${YELLOW}⚠️  .obsidian Verzeichnis nicht gefunden. Erstelle...${NC}"
    mkdir -p "$OBSIDIAN_DIR"
fi

# Prüfe ob plugins Verzeichnis existiert
PLUGINS_DIR="$OBSIDIAN_DIR/plugins"
if [ ! -d "$PLUGINS_DIR" ]; then
    echo -e "${YELLOW}⚠️  plugins Verzeichnis nicht gefunden. Erstelle...${NC}"
    mkdir -p "$PLUGINS_DIR"
fi

# Backup erstellen bei Update
if [ -d "$PLUGIN_TARGET" ]; then
    echo -e "${YELLOW}⚠️  Plugin bereits vorhanden. Backup erstellen und überschreiben? (j/n): ${NC}"
    read -n 1 OVERWRITE
    echo
    if [[ ! $OVERWRITE =~ ^[Jj]$ ]]; then
        echo "Installation abgebrochen."
        exit 0
    fi
    
    # Backup erstellen
    BACKUP_DIR="$PLUGIN_TARGET.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${BLUE}📁 Erstelle Backup: $BACKUP_DIR${NC}"
    cp -r "$PLUGIN_TARGET" "$BACKUP_DIR"
    rm -rf "$PLUGIN_TARGET"
fi

# Installiere Plugin
echo -e "${BLUE}📦 Installiere Plugin...${NC}"

# Kopiere Plugin-Dateien
mkdir -p "$PLUGIN_TARGET"
cp "$PLUGIN_SOURCE/main.js" "$PLUGIN_TARGET/"
cp "$PLUGIN_SOURCE/manifest.json" "$PLUGIN_TARGET/"
cp "$PLUGIN_SOURCE/styles.css" "$PLUGIN_TARGET/"

# Zusätzliche Dateien falls vorhanden
if [ -f "$PLUGIN_SOURCE/data.json" ]; then
    cp "$PLUGIN_SOURCE/data.json" "$PLUGIN_TARGET/"
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Plugin erfolgreich installiert!${NC}"
    echo
    echo -e "${BLUE}📋 Nächste Schritte:${NC}"
    echo "1. Starten Sie Obsidian neu (wichtig für neue Features)"
    echo "2. Gehen Sie zu Settings → Community Plugins"
    echo "3. Aktivieren Sie 'KI-Wissenssystem'"
    echo "4. Konfigurieren Sie die Einstellungen:"
    echo "   • API-URL: http://localhost:8080"
    echo "   • WebSocket-URL: ws://localhost:8080/ws/chat"
    echo "   • (Optional) API-Key für erweiterte Features"
    echo
    echo -e "${BLUE}🚀 Neue Features in dieser Version:${NC}"
    echo "• Chat-Historie wird automatisch gespeichert"
    echo "• 4 verschiedene Layout-Modi verfügbar"
    echo "• Erweiterte Graph-Suche mit Filtern"
    echo "• Verbesserte Performance für große Graphs"
    echo
    echo -e "${GREEN}Plugin-Pfad: $PLUGIN_TARGET${NC}"
    
    # Plugin-Info anzeigen
    if [ -f "$PLUGIN_TARGET/manifest.json" ]; then
        VERSION=$(python3 -c "import json; print(json.load(open('$PLUGIN_TARGET/manifest.json')).get('version', 'unknown'))")
        echo -e "${GREEN}Installierte Version: $VERSION${NC}"
    fi
else
    echo -e "${RED}❌ Plugin-Installation fehlgeschlagen${NC}"
    exit 1
fi 