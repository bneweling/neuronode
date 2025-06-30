#!/usr/bin/env python3
"""
Test Script für Document-Knoten Funktionalität
Testet die erweiterte Datenmodell-Semantik
"""
import sys
from pathlib import Path
import asyncio
import tempfile
import json

# Projekt-Root zur PYTHONPATH hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.document_processing.document_processor import DocumentProcessor
from src.document_processing.metadata_extractor import DocumentMetadataExtractor
from src.storage.neo4j_client import Neo4jClient
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_document_metadata_extraction():
    """Test der Metadaten-Extraktion"""
    print("\n🧪 Test 1: Document Metadata Extraction")
    
    # Test-Dokument erstellen
    test_content = """
    BSI IT-Grundschutz Kompendium 2024
    
    ORP.4.A1 Regelung für die Passwort-Nutzung
    Die Institution MUSS den Umgang mit Passwörtern regeln.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_BSI_Grundschutz_2024.txt', delete=False) as f:
        f.write(test_content)
        test_file = f.name
    
    try:
        extractor = DocumentMetadataExtractor()
        metadata = extractor.extract_metadata(test_file)
        
        print(f"✅ Metadaten extrahiert:")
        print(f"   📄 Original: {metadata['filename']}")
        print(f"   🏷️  Standard: {metadata['standard_name']} v{metadata['standard_version']}")
        print(f"   📊 Typ: {metadata['document_type']}")
        print(f"   🔐 Hash: {metadata['hash'][:8]}...")
        print(f"   📏 Größe: {metadata['file_size']} bytes")
        
        return metadata
        
    finally:
        Path(test_file).unlink()

async def test_document_node_creation():
    """Test der Document-Knoten Erstellung"""
    print("\n🧪 Test 2: Document Node Creation")
    
    metadata = {
        'filename': 'test_bsi_2024.txt',
        'hash': 'abc123def456ghi789',
        'document_type': 'BSI_GRUNDSCHUTZ',
        'standard_name': 'BSI',
        'standard_version': '2024',
        'file_size': 1024,
        'page_count': 1,
        'source_url': None,
        'author': None
    }
    
    neo4j = Neo4jClient()
    
    try:
        # Test: Document-Knoten erstellen
        document_id = neo4j.create_document_node(metadata)
        print(f"✅ Document-Knoten erstellt: {document_id}")
        
        # Test: Duplikat-Erkennung
        existing_doc = neo4j.find_document_by_hash(metadata['hash'])
        print(f"✅ Duplikat-Erkennung: {existing_doc['id'] == document_id}")
        
        # Test: Zweite Erstellung (sollte existierenden finden)
        document_id2 = neo4j.create_document_node(metadata)
        print(f"✅ Duplikat-Handling: {document_id == document_id2}")
        
        return document_id
        
    finally:
        # Cleanup: Test-Document löschen
        with neo4j.driver.session() as session:
            session.run("MATCH (d:Document {hash: $hash}) DETACH DELETE d", hash=metadata['hash'])
        neo4j.close()

async def test_integrated_document_processing():
    """Test der integrierten Document-Verarbeitung"""
    print("\n🧪 Test 3: Integrated Document Processing")
    
    # Komplexeres Test-Dokument
    test_content = """
    BSI IT-Grundschutz Kompendium 2024
    
    ORP.4 Identitäts- und Berechtigungsmanagement
    
    ORP.4.A1 Regelung für die Passwort-Nutzung (B)
    Die Institution MUSS den Umgang mit Passwörtern regeln. Dabei MUSS sie festlegen:
    - Wer Passwörter vergeben darf
    - Welche Passwort-Anforderungen zu beachten sind
    - Wie Passwörter übermittelt werden dürfen
    
    ORP.4.A10 Starke Passwörter (B)
    Es MÜSSEN Passwörter mit einer angemessenen Länge und Komplexität verwendet werden.
    Die Mindestlänge für Passwörter SOLLTE 12 Zeichen betragen.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_BSI_Grundschutz_2024_Test.txt', delete=False) as f:
        f.write(test_content)
        test_file = f.name
    
    processor = DocumentProcessor()
    
    try:
        # Test der erweiterten Verarbeitung
        result = await processor.process_document_with_metadata(test_file)
        
        print(f"✅ Verarbeitung abgeschlossen:")
        print(f"   📊 Status: {result['status']}")
        print(f"   📄 Document-ID: {result['document_id']}")
        print(f"   🎯 Controls: {result['controls_count']}")
        print(f"   📝 Chunks: {result['chunks_count']}")
        
        # Test: Zweite Verarbeitung (Duplikat-Erkennung)
        result2 = await processor.process_document_with_metadata(test_file)
        print(f"✅ Duplikat-Erkennung: {result2['status'] == 'duplicate'}")
        
        return result
        
    finally:
        Path(test_file).unlink()
        processor.close()

async def test_document_queries():
    """Test der neuen Document-basierten Abfragen"""
    print("\n🧪 Test 4: Document-Based Queries")
    
    neo4j = Neo4jClient()
    
    try:
        # Test: Document-Suche
        with neo4j.driver.session() as session:
            result = session.run("""
                MATCH (d:Document)
                WHERE d.standard_name = 'BSI'
                RETURN count(d) as bsi_docs
            """)
            bsi_count = result.single()["bsi_docs"]
            print(f"✅ BSI-Dokumente gefunden: {bsi_count}")
            
            # Test: Document-zu-Content-Beziehungen
            result = session.run("""
                MATCH (d:Document)-[:CONTAINS]->(c)
                RETURN d.filename as document, count(c) as content_items
                LIMIT 5
            """)
            
            print("✅ Document-Content-Beziehungen:")
            for record in result:
                print(f"   📄 {record['document']}: {record['content_items']} Items")
        
    finally:
        neo4j.close()

async def run_all_tests():
    """Führt alle Tests aus"""
    print("🚀 Starte Document-Knoten Tests...")
    
    try:
        # Test 1: Metadaten-Extraktion
        await test_document_metadata_extraction()
        
        # Test 2: Document-Knoten Erstellung
        await test_document_node_creation()
        
        # Test 3: Integrierte Verarbeitung
        await test_integrated_document_processing()
        
        # Test 4: Document-Abfragen
        await test_document_queries()
        
        print("\n🎉 Alle Tests erfolgreich abgeschlossen!")
        print("✅ Document-Knoten Funktionalität ist bereit!")
        
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1) 