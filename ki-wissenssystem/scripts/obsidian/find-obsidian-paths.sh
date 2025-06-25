#!/bin/bash
# find-obsidian-paths.sh - Findet automatisch Obsidian Plugin-Pfade

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🔍 Suche nach Obsidian-Installationen...${NC}"
echo

# Prüfe verschiedene Obsidian-Pfade
OBSIDIAN_LOCAL="$HOME/Library/Application Support/obsidian"
OBSIDIAN_ICLOUD="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"

if [ -f "$OBSIDIAN_LOCAL/obsidian.json" ]; then
    echo -e "${GREEN}✅ Obsidian gefunden (lokale Installation)${NC}"
    echo "Konfigurations-Pfad: $OBSIDIAN_LOCAL"
    echo
    
    # Parse Vault-Pfade aus obsidian.json
    echo -e "${BLUE}📁 Ihre Obsidian Vaults:${NC}"
    
    # Verwende Python für JSON-Parsing (sicherer als jq)
    python3 << EOF
import json
import os

try:
    with open('$OBSIDIAN_LOCAL/obsidian.json', 'r') as f:
        config = json.load(f)
    
    vaults = config.get('vaults', {})
    if not vaults:
        print("Keine Vaults gefunden.")
    else:
        for vault_id, vault_info in vaults.items():
            vault_path = vault_info.get('path', '')
            vault_name = os.path.basename(vault_path)
            plugin_path = os.path.join(vault_path, '.obsidian', 'plugins')
            
            print(f"  📂 {vault_name}")
            print(f"     Vault-Pfad: {vault_path}")
            print(f"     Plugin-Pfad: {plugin_path}")
            
            # Prüfe ob .obsidian Ordner existiert
            obsidian_dir = os.path.join(vault_path, '.obsidian')
            if os.path.exists(obsidian_dir):
                print(f"     Status: ✅ .obsidian Ordner existiert")
            else:
                print(f"     Status: ⚠️  .obsidian Ordner fehlt (wird automatisch erstellt)")
            
            # Prüfe ob plugins Ordner existiert
            if os.path.exists(plugin_path):
                print(f"     Plugins: ✅ Plugin-Ordner existiert")
            else:
                print(f"     Plugins: ⚠️  Plugin-Ordner fehlt (wird automatisch erstellt)")
            print()

except Exception as e:
    print(f"Fehler beim Lesen der Konfiguration: {e}")
EOF

elif [ -d "$OBSIDIAN_ICLOUD" ]; then
    echo -e "${GREEN}✅ Obsidian gefunden (iCloud-Sync)${NC}"
    echo "Konfigurations-Pfad: $OBSIDIAN_ICLOUD"
    echo
    echo "Ihre Vaults befinden sich wahrscheinlich unter:"
    ls -la "$OBSIDIAN_ICLOUD" 2>/dev/null | grep "^d" | awk '{print $NF}' | while read vault; do
        if [ "$vault" != "." ] && [ "$vault" != ".." ]; then
            echo "  📂 $vault"
            echo "     Plugin-Pfad: $OBSIDIAN_ICLOUD/$vault/.obsidian/plugins/"
            echo
        fi
    done
else
    echo -e "${YELLOW}⚠️  Obsidian-Installation nicht gefunden${NC}"
    echo "Mögliche Gründe:"
    echo "  - Obsidian wurde noch nie gestartet"
    echo "  - Obsidian ist an einem anderen Ort installiert"
    echo "  - Obsidian verwendet eine portable Installation"
    echo
    echo "Standard-Pfade:"
    echo "  - Lokal: ~/Library/Application Support/obsidian/"
    echo "  - iCloud: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/"
fi

echo
echo -e "${BLUE}📋 Plugin-Installation:${NC}"

# Prüfe ob Plugin-Quellverzeichnis existiert
PLUGIN_SOURCE="../obsidian-ki-plugin"
if [ -d "$PLUGIN_SOURCE" ] && [ -f "$PLUGIN_SOURCE/main.js" ]; then
    echo -e "${GREEN}✅ Plugin-Quellverzeichnis gefunden und gebaut${NC}"
    echo
    
    # Biete automatische Installation an
    read -p "Möchten Sie das Plugin jetzt automatisch installieren? (j/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        echo -e "${BLUE}🔌 Starte automatische Plugin-Installation...${NC}"
        ./install-obsidian-plugin.sh
        exit $?
    fi
elif [ -d "$PLUGIN_SOURCE" ] && [ ! -f "$PLUGIN_SOURCE/main.js" ]; then
    echo -e "${YELLOW}⚠️  Plugin-Quellverzeichnis gefunden, aber noch nicht gebaut${NC}"
    echo
    read -p "Möchten Sie das Plugin bauen und installieren? (j/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        echo -e "${BLUE}🔨 Baue und installiere Plugin...${NC}"
        cd "$PLUGIN_SOURCE"
        if command -v npm &> /dev/null; then
            npm install && npm run build
            if [ $? -eq 0 ]; then
                cd - > /dev/null
                ./install-obsidian-plugin.sh
                exit $?
            else
                echo -e "${RED}❌ Plugin-Build fehlgeschlagen${NC}"
                cd - > /dev/null
            fi
        else
            echo -e "${RED}❌ npm nicht gefunden. Bitte installieren Sie Node.js${NC}"
            cd - > /dev/null
        fi
    fi
elif [ ! -d "$PLUGIN_SOURCE" ]; then
    echo -e "${YELLOW}⚠️  Plugin-Quellverzeichnis nicht gefunden: $PLUGIN_SOURCE${NC}"
fi

echo
echo -e "${BLUE}📋 Manuelle Installation:${NC}"
echo "1. Kopieren Sie den 'obsidian-ki-plugin' Ordner nach:"
echo "   [Vault-Pfad]/.obsidian/plugins/obsidian-ki-plugin/"
echo
echo "2. Oder verwenden Sie diesen Befehl:"
echo -e "${GREEN}   cp -r ../obsidian-ki-plugin [Vault-Pfad]/.obsidian/plugins/${NC}"
echo
echo "3. Starten Sie Obsidian neu und aktivieren Sie das Plugin unter:"
echo "   Settings → Community Plugins → KI-Wissenssystem"
echo
echo "4. Konfigurieren Sie die API-URL: http://localhost:8080" 