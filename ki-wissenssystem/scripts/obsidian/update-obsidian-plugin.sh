#!/bin/bash
# update-obsidian-plugin.sh - Aktualisiert das KI-Wissenssystem Plugin automatisch

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔄 KI-Wissenssystem Plugin Update${NC}"
echo

# Prüfe Plugin-Verzeichnis
PLUGIN_SOURCE="../obsidian-ki-plugin"
if [ ! -d "$PLUGIN_SOURCE" ]; then
    echo -e "${RED}❌ Plugin-Quellverzeichnis nicht gefunden: $PLUGIN_SOURCE${NC}"
    exit 1
fi

# Build Plugin
echo -e "${BLUE}🔨 Baue Plugin...${NC}"
cd "$PLUGIN_SOURCE"

# Dependencies prüfen und installieren
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  Dependencies werden installiert...${NC}"
    npm install
fi

# TypeScript Check
npx tsc --noEmit --skipLibCheck
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ TypeScript-Fehler gefunden${NC}"
    exit 1
fi

# Build
npm run build
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build fehlgeschlagen${NC}"
    exit 1
fi

cd - > /dev/null

# Finde installierte Plugins
echo -e "${BLUE}🔍 Suche nach installierten Plugin-Versionen...${NC}"

OBSIDIAN_CONFIG="$HOME/Library/Application Support/obsidian/obsidian.json"
if [ ! -f "$OBSIDIAN_CONFIG" ]; then
    echo -e "${RED}❌ Obsidian-Konfiguration nicht gefunden${NC}"
    exit 1
fi

# Finde alle Vaults mit installiertem Plugin
python3 << 'EOF'
import json
import os
import sys
from datetime import datetime

try:
    with open(os.path.expanduser('~/Library/Application Support/obsidian/obsidian.json'), 'r') as f:
        config = json.load(f)
    
    vaults = config.get('vaults', {})
    installations = []
    
    for vault_id, vault_data in vaults.items():
        vault_path = vault_data.get('path', '')
        vault_name = os.path.basename(vault_path)
        plugin_path = os.path.join(vault_path, '.obsidian', 'plugins', 'obsidian-ki-plugin')
        
        if os.path.exists(plugin_path):
            # Lese aktuelle Version
            current_version = "unknown"
            manifest_path = os.path.join(plugin_path, 'manifest.json')
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                        current_version = manifest.get('version', 'unknown')
                except:
                    pass
            
            # Lese letzte Änderung
            last_modified = "unknown"
            main_js_path = os.path.join(plugin_path, 'main.js')
            if os.path.exists(main_js_path):
                try:
                    mtime = os.path.getmtime(main_js_path)
                    last_modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            installations.append((vault_name, vault_path, current_version, last_modified))
            print(f"✅ {vault_name}")
            print(f"   Pfad: {vault_path}")
            print(f"   Version: {current_version}")
            print(f"   Letzte Änderung: {last_modified}")
            print()
    
    if not installations:
        print("Keine installierten Plugin-Versionen gefunden.")
        sys.exit(1)
    
    # Schreibe Installation-Info
    with open('/tmp/plugin_installations.txt', 'w') as f:
        for name, path, version, modified in installations:
            f.write(f"{name}|{path}|{version}|{modified}\n")
            
    print(f"Gefunden: {len(installations)} Installation(en)")

except Exception as e:
    print(f"Fehler: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi

# Benutzer-Auswahl
echo -e "${BLUE}🎯 Update-Optionen:${NC}"
echo "1. Alle Installationen aktualisieren"
echo "2. Spezifische Installation auswählen"
echo "3. Nur Backup erstellen und Abbruch"
echo
echo -n "Wählen Sie eine Option (1-3): "
read UPDATE_CHOICE

case $UPDATE_CHOICE in
    1)
        echo -e "${BLUE}📦 Aktualisiere alle Installationen...${NC}"
        while IFS='|' read -r name path version modified; do
            update_installation "$name" "$path" "$version"
        done < /tmp/plugin_installations.txt
        ;;
    2)
        echo -e "${BLUE}📁 Verfügbare Installationen:${NC}"
        i=1
        while IFS='|' read -r name path version modified; do
            echo "$i. $name (Version: $version)"
            i=$((i+1))
        done < /tmp/plugin_installations.txt
        
        echo -n "Welche Installation aktualisieren? (Nummer): "
        read INSTALL_CHOICE
        
        i=1
        while IFS='|' read -r name path version modified; do
            if [ "$i" = "$INSTALL_CHOICE" ]; then
                update_installation "$name" "$path" "$version"
                break
            fi
            i=$((i+1))
        done < /tmp/plugin_installations.txt
        ;;
    3)
        echo -e "${BLUE}💾 Erstelle nur Backups...${NC}"
        while IFS='|' read -r name path version modified; do
            create_backup "$name" "$path"
        done < /tmp/plugin_installations.txt
        echo -e "${GREEN}✅ Backups erstellt${NC}"
        ;;
    *)
        echo -e "${RED}❌ Ungültige Auswahl${NC}"
        exit 1
        ;;
esac

rm -f /tmp/plugin_installations.txt

# Update-Funktion
update_installation() {
    local vault_name="$1"
    local vault_path="$2"
    local current_version="$3"
    local plugin_target="$vault_path/.obsidian/plugins/obsidian-ki-plugin"
    
    echo -e "${BLUE}🔄 Aktualisiere: $vault_name${NC}"
    
    # Backup erstellen
    create_backup "$vault_name" "$vault_path"
    
    # Plugin-Dateien aktualisieren
    echo -e "${YELLOW}📦 Kopiere neue Plugin-Dateien...${NC}"
    
    # Kopiere Hauptdateien
    cp "$PLUGIN_SOURCE/main.js" "$plugin_target/"
    cp "$PLUGIN_SOURCE/manifest.json" "$plugin_target/"
    cp "$PLUGIN_SOURCE/styles.css" "$plugin_target/"
    
    # Zusätzliche Dateien
    if [ -f "$PLUGIN_SOURCE/data.json" ]; then
        cp "$PLUGIN_SOURCE/data.json" "$plugin_target/"
    fi
    
    if [ $? -eq 0 ]; then
        # Neue Version auslesen
        NEW_VERSION=$(python3 -c "import json; print(json.load(open('$plugin_target/manifest.json')).get('version', 'unknown'))")
        echo -e "${GREEN}✅ $vault_name aktualisiert ($current_version → $NEW_VERSION)${NC}"
    else
        echo -e "${RED}❌ Update fehlgeschlagen für $vault_name${NC}"
    fi
}

# Backup-Funktion
create_backup() {
    local vault_name="$1"
    local vault_path="$2"
    local plugin_target="$vault_path/.obsidian/plugins/obsidian-ki-plugin"
    
    if [ -d "$plugin_target" ]; then
        local backup_dir="$plugin_target.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${YELLOW}💾 Backup für $vault_name: $(basename $backup_dir)${NC}"
        cp -r "$plugin_target" "$backup_dir"
        
        # Alte Backups aufräumen (behalte nur die letzten 5)
        find "$(dirname $plugin_target)" -name "obsidian-ki-plugin.backup.*" -type d | \
        sort -r | tail -n +6 | xargs rm -rf 2>/dev/null || true
    fi
}

echo
echo -e "${GREEN}🎉 Update abgeschlossen!${NC}"
echo
echo -e "${BLUE}📋 Nächste Schritte:${NC}"
echo "1. Starten Sie Obsidian neu"
echo "2. Testen Sie die neuen Features:"
echo "   • Chat-Historie (📚 Historie Button)"
echo "   • Graph-Suche (🔍 Suche Button)"
echo "   • Layout-Modi (⚖️ Layout Buttons)"
echo "3. Prüfen Sie die Plugin-Einstellungen"
echo
echo -e "${BLUE}🆕 Neue Features in diesem Update:${NC}"
echo "• Persistente Chat-Speicherung mit Sitzungsverwaltung"
echo "• Erweiterte Graph-Suche mit 4 Algorithmen"
echo "• Einheitliche Workbench mit flexiblen Layouts"
echo "• Verbesserte Performance und UI" 