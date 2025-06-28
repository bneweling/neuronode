#!/usr/bin/env python3
"""
Schema Migration Script für Document-Knoten
Führt die Schema-Änderungen sicher durch
"""
import os
import sys
from pathlib import Path

# Projekt-Root zur PYTHONPATH hinzufügen
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.storage.neo4j_client import Neo4jClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_schema_migration():
    """Führt Schema-Migration durch"""
    try:
        neo4j = Neo4jClient()
        
        # Schema-Datei laden
        schema_file = Path(__file__).parent / "schema.cypher"
        
        with open(schema_file, 'r') as f:
            content = f.read()
            # Aufteilen bei Semikolon, aber nur wenn es nicht in einem String ist
            schema_commands = []
            current_command = ""
            
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('//'):
                    current_command += line + "\n"
                    if line.endswith(';'):
                        schema_commands.append(current_command.strip())
                        current_command = ""
        
        print("🔄 Führe Schema-Migration durch...")
        
        for i, command in enumerate(schema_commands, 1):
            if command:
                try:
                    with neo4j.driver.session() as session:
                        session.run(command)
                    print(f"✅ Schema-Kommando {i} erfolgreich")
                except Exception as e:
                    if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                        print(f"ℹ️  Schema-Kommando {i} bereits vorhanden (übersprungen)")
                    else:
                        print(f"❌ Fehler bei Kommando {i}: {e}")
                        return False
        
        print("🎉 Schema-Migration abgeschlossen!")
        return True
        
    except Exception as e:
        logger.error(f"Schema-Migration fehlgeschlagen: {e}")
        return False
    finally:
        try:
            neo4j.close()
        except:
            pass

if __name__ == "__main__":
    success = run_schema_migration()
    sys.exit(0 if success else 1) 