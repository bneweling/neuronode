#!/bin/bash
# setup-obsidian.sh - All-in-One Obsidian Plugin Setup

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔌 KI-Wissenssystem Obsidian Plugin Setup${NC}"
echo

# Funktion zur Plugin-Installation
install_plugin_to_vault() {
    local vault_name="$1"
    local vault_path="$2"
    local plugin_target="$vault_path/.obsidian/plugins/obsidian-ki-plugin"
    
    echo -e "${BLUE}📦 Installiere Plugin in Vault: $vault_name${NC}"
    
    # Erstelle Verzeichnisse falls nötig
    mkdir -p "$vault_path/.obsidian/plugins"
    
    # Prüfe ob Plugin bereits existiert
    if [ -d "$plugin_target" ]; then
        echo -e "${YELLOW}⚠️  Plugin bereits vorhanden. Überschreiben? (j/n): ${NC}"
        read -n 1 OVERWRITE
        echo
        if [[ ! $OVERWRITE =~ ^[Jj]$ ]]; then
            echo "Überspringe $vault_name"
            return
        fi
        rm -rf "$plugin_target"
    fi
    
    # Kopiere Plugin-Dateien
    mkdir -p "$plugin_target"
    cp "$PLUGIN_SOURCE/main.js" "$plugin_target/"
    cp "$PLUGIN_SOURCE/manifest.json" "$plugin_target/"
    cp "$PLUGIN_SOURCE/styles.css" "$plugin_target/"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Plugin erfolgreich installiert in: $vault_name${NC}"
    else
        echo -e "${RED}❌ Plugin-Installation fehlgeschlagen für: $vault_name${NC}"
    fi
}

# 1. Prüfe Plugin-Quellverzeichnis
PLUGIN_SOURCE="../obsidian-ki-plugin"
echo -e "${BLUE}📦 Prüfe Plugin-Quellverzeichnis...${NC}"

if [ ! -d "$PLUGIN_SOURCE" ]; then
    echo -e "${RED}❌ Plugin-Quellverzeichnis nicht gefunden: $PLUGIN_SOURCE${NC}"
    echo "Bitte stellen Sie sicher, dass das obsidian-ki-plugin Verzeichnis existiert."
    exit 1
fi

# 2. Prüfe/Baue Plugin falls nötig
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

echo -e "${GREEN}✅ Plugin ist bereit${NC}"

# 3. Finde Obsidian-Vaults
echo -e "${BLUE}🔍 Suche nach Obsidian-Installationen...${NC}"

OBSIDIAN_LOCAL="$HOME/Library/Application Support/obsidian"
OBSIDIAN_ICLOUD="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"

if [ -f "$OBSIDIAN_LOCAL/obsidian.json" ]; then
    echo -e "${GREEN}✅ Obsidian gefunden (lokale Installation)${NC}"
    echo
    
    # Parse und zeige Vaults
    echo -e "${BLUE}📁 Verfügbare Vaults:${NC}"
    
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
    
    # Schreibe Vault-Info in temporäre Datei
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
    
    # 4. Benutzer-Auswahl
    echo -n "Welchen Vault möchten Sie verwenden? (Nummer eingeben oder 'a' für alle): "
    read VAULT_CHOICE
    
    if [ "$VAULT_CHOICE" = "a" ] || [ "$VAULT_CHOICE" = "A" ]; then
        # Installiere in alle Vaults
        echo -e "${BLUE}📦 Installiere Plugin in alle Vaults...${NC}"
        while IFS='|' read -r num name path; do
            install_plugin_to_vault "$name" "$path"
        done < /tmp/vault_info.txt
    else
        # Installiere in ausgewählten Vault
        SELECTED_VAULT_PATH=""
        SELECTED_VAULT_NAME=""
        while IFS='|' read -r num name path; do
            if [ "$num" = "$VAULT_CHOICE" ]; then
                SELECTED_VAULT_PATH="$path"
                SELECTED_VAULT_NAME="$name"
                break
            fi
        done < /tmp/vault_info.txt
        
        if [ -z "$SELECTED_VAULT_PATH" ]; then
            echo -e "${RED}❌ Ungültige Auswahl${NC}"
            rm -f /tmp/vault_info.txt
            exit 1
        fi
        
        install_plugin_to_vault "$SELECTED_VAULT_NAME" "$SELECTED_VAULT_PATH"
    fi
    
    rm -f /tmp/vault_info.txt
    
elif [ -d "$OBSIDIAN_ICLOUD" ]; then
    echo -e "${GREEN}✅ Obsidian gefunden (iCloud-Sync)${NC}"
    echo -e "${YELLOW}⚠️  iCloud-Sync erkannt. Bitte verwenden Sie das manuelle Installationsskript.${NC}"
    echo "Führen Sie aus: ./install-obsidian-plugin.sh"
    exit 0
else
    echo -e "${RED}❌ Obsidian-Installation nicht gefunden${NC}"
    echo "Bitte starten Sie Obsidian mindestens einmal."
    exit 1
fi

echo
echo -e "${GREEN}🎉 Plugin-Setup abgeschlossen!${NC}"
echo
echo -e "${BLUE}📋 Nächste Schritte:${NC}"
echo "1. Starten Sie Obsidian neu"
echo "2. Gehen Sie zu Settings → Community Plugins"
echo "3. Aktivieren Sie 'KI-Wissenssystem'"
echo "4. Konfigurieren Sie die API-URL: http://localhost:8080" 