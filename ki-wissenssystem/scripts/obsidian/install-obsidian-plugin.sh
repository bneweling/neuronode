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

# Prüfe ob Plugin-Verzeichnis existiert
PLUGIN_SOURCE="../obsidian-ki-plugin"
if [ ! -d "$PLUGIN_SOURCE" ]; then
    echo -e "${RED}❌ Plugin-Quellverzeichnis nicht gefunden: $PLUGIN_SOURCE${NC}"
    echo "Bitte stellen Sie sicher, dass das obsidian-ki-plugin Verzeichnis existiert."
    exit 1
fi

# Prüfe ob Plugin gebaut wurde
if [ ! -f "$PLUGIN_SOURCE/main.js" ]; then
    echo -e "${YELLOW}⚠️  Plugin noch nicht gebaut. Baue Plugin...${NC}"
    cd "$PLUGIN_SOURCE"
    if command -v npm &> /dev/null; then
        npm install && npm run build
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Plugin-Build fehlgeschlagen${NC}"
            exit 1
        fi
        cd - > /dev/null
    else
        echo -e "${RED}❌ npm nicht gefunden. Bitte installieren Sie Node.js${NC}"
        exit 1
    fi
fi

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
        else:
            print(f"   Status: ⚪ Plugin nicht installiert")
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

# Installiere Plugin
echo -e "${BLUE}📦 Installiere Plugin...${NC}"

if [ -d "$PLUGIN_TARGET" ]; then
    echo -e "${YELLOW}⚠️  Plugin bereits vorhanden. Überschreiben? (j/n): ${NC}"
    read -n 1 OVERWRITE
    echo
    if [[ ! $OVERWRITE =~ ^[Jj]$ ]]; then
        echo "Installation abgebrochen."
        exit 0
    fi
    rm -rf "$PLUGIN_TARGET"
fi

# Kopiere Plugin-Dateien
mkdir -p "$PLUGIN_TARGET"
cp "$PLUGIN_SOURCE/main.js" "$PLUGIN_TARGET/"
cp "$PLUGIN_SOURCE/manifest.json" "$PLUGIN_TARGET/"
cp "$PLUGIN_SOURCE/styles.css" "$PLUGIN_TARGET/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Plugin erfolgreich installiert!${NC}"
    echo
    echo -e "${BLUE}📋 Nächste Schritte:${NC}"
    echo "1. Starten Sie Obsidian neu"
    echo "2. Gehen Sie zu Settings → Community Plugins"
    echo "3. Aktivieren Sie 'KI-Wissenssystem'"
    echo "4. Konfigurieren Sie die API-URL: http://localhost:8080"
    echo
    echo -e "${GREEN}Plugin-Pfad: $PLUGIN_TARGET${NC}"
else
    echo -e "${RED}❌ Plugin-Installation fehlgeschlagen${NC}"
    exit 1
fi 