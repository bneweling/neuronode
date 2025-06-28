#!/usr/bin/env python3
"""
Import-Skript für synthetische BSI-Daten
Importiert die JSON-Dateien in Neo4j und ChromaDB
"""

import json
import sys
import os

# Add src to path
sys.path.append('src')

def load_json_data(file_path: str) -> dict:
    """Load JSON data from file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def import_to_neo4j(data: dict):
    """Import data to Neo4j using the graph client"""
    from src.storage.neo4j_client import Neo4jClient
    from src.models.document_types import ControlItem, KnowledgeChunk
    
    neo4j = Neo4jClient()
    
    print(f"📊 Importing {len(data['controls'])} controls to Neo4j...")
    
    # Import ControlItems
    for control_data in data['controls']:
        control = ControlItem(**control_data)
        control_id = neo4j.create_control_item(control)
        print(f"  ✅ Control {control_id} imported")
    
    # Import KnowledgeChunks  
    print(f"📊 Importing {len(data['knowledge_chunks'])} chunks to Neo4j...")
    for chunk_data in data['knowledge_chunks']:
        chunk = KnowledgeChunk(**chunk_data)
        chunk_id = neo4j.create_knowledge_chunk(chunk)
        print(f"  ✅ Chunk {chunk_id} imported")
    
    # Create Technology nodes and relationships
    print(f"📊 Creating {len(data['technologies'])} technology nodes...")
    with neo4j.driver.session() as session:
        for tech in data['technologies']:
            session.run("""
                MERGE (t:Technology {name: $name, category: $category})
                SET t.metadata = $metadata
            """, name=tech['name'], category=tech['category'], 
                metadata=json.dumps(tech.get('metadata', {})))
            
            # Create IMPLEMENTS relationships
            for control_id in tech['implements_controls']:
                session.run("""
                    MATCH (t:Technology {name: $tech_name})
                    MATCH (c:ControlItem {id: $control_id})
                    MERGE (t)-[:IMPLEMENTS]->(c)
                """, tech_name=tech['name'], control_id=control_id)
            
            print(f"  ✅ Technology {tech['name']} imported with relationships")
    
    # Create Entity nodes
    print(f"📊 Creating {len(data['entities'])} entity nodes...")
    with neo4j.driver.session() as session:
        for entity in data['entities']:
            session.run("""
                MERGE (e:Entity {name: $name, type: $type})
                SET e.description = $description
            """, name=entity['name'], type=entity['type'], 
                description=entity.get('description', ''))
            print(f"  ✅ Entity {entity['name']} imported")
    
    # Create explicit relationships
    print(f"📊 Creating {len(data['relationships'])} explicit relationships...")
    with neo4j.driver.session() as session:
        for rel in data['relationships']:
            # Dynamic relationship creation
            session.run(f"""
                MATCH (s {{id: $source_id}})
                MATCH (t {{id: $target_id}})
                MERGE (s)-[r:{rel['type']}]->(t)
                SET r.confidence = $confidence,
                    r.description = $description
            """, source_id=rel['source'], target_id=rel['target'],
                confidence=rel.get('confidence', 0.5),
                description=rel.get('description', ''))
            print(f"  ✅ Relationship {rel['source']} -{rel['type']}-> {rel['target']}")
    
    neo4j.close()
    print("✅ Neo4j import completed!")

def import_to_chromadb(data: dict):
    """Import data to ChromaDB"""
    from src.storage.chroma_client import ChromaClient
    
    chroma = ChromaClient()
    
    # Determine collection (compliance for BSI data)
    collection_name = "compliance"
    
    print(f"📊 Importing {len(data['knowledge_chunks'])} chunks to ChromaDB collection '{collection_name}'...")
    
    for chunk_data in data['knowledge_chunks']:
        try:
            chunk_id = chroma.add_chunk(chunk_data, collection_name)
            print(f"  ✅ Chunk {chunk_id} imported to ChromaDB")
        except Exception as e:
            print(f"  ❌ Error importing chunk {chunk_data['id']}: {e}")
    
    print("✅ ChromaDB import completed!")

def run_cypher_script(cypher_file: str):
    """Execute the Cypher script for additional graph structure"""
    from src.storage.neo4j_client import Neo4jClient
    
    with open(cypher_file, 'r', encoding='utf-8') as f:
        cypher_content = f.read()
    
    # Split by comments to get individual commands
    commands = []
    current_command = []
    
    for line in cypher_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('//'):
            if current_command:
                commands.append('\n'.join(current_command))
                current_command = []
            continue
        current_command.append(line)
    
    if current_command:
        commands.append('\n'.join(current_command))
    
    neo4j = Neo4jClient()
    
    print(f"📊 Executing {len(commands)} Cypher commands...")
    
    with neo4j.driver.session() as session:
        for i, command in enumerate(commands, 1):
            if command.strip():
                try:
                    session.run(command)
                    print(f"  ✅ Command {i}/{len(commands)} executed")
                except Exception as e:
                    print(f"  ⚠️ Command {i} failed: {e}")
                    print(f"     Command: {command[:100]}...")
    
    neo4j.close()
    print("✅ Cypher script execution completed!")

def main():
    """Main import function"""
    print("🚀 Starting synthetic BSI data import...")
    
    # Check if data files exist (in current directory)
    bst1_file = "BST1.json"
    bst2_file = "BST2.json" 
    cypher_file = "BSTcypher.txt"
    
    for file_path in [bst1_file, bst2_file, cypher_file]:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return
    
    try:
        # Load data
        print("📂 Loading JSON data files...")
        bst1_data = load_json_data(bst1_file)
        bst2_data = load_json_data(bst2_file)
        
        print(f"✅ Loaded BSI OPS.1.1.2 data: {len(bst1_data['controls'])} controls, {len(bst1_data['knowledge_chunks'])} chunks")
        print(f"✅ Loaded BSI SYS.1.1 data: {len(bst2_data['controls'])} controls, {len(bst2_data['knowledge_chunks'])} chunks")
        
        # Import to Neo4j
        print("\n🗄️ Starting Neo4j import...")
        import_to_neo4j(bst1_data)
        import_to_neo4j(bst2_data)
        
        # Execute Cypher script for additional structure
        print("\n🔗 Executing Cypher script for graph relationships...")
        run_cypher_script(cypher_file)
        
        # Import to ChromaDB
        print("\n📊 Starting ChromaDB import...")
        import_to_chromadb(bst1_data)
        import_to_chromadb(bst2_data)
        
        print("\n🎉 All synthetic data imported successfully!")
        print("\nℹ️ You can now test the system with:")
        print("  ./ki-cli.sh stats")
        print("  ./ki-cli.sh query 'Zeige mir alle BSI Controls'")
        print("  ./ki-cli.sh graph")
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Please install requirements first: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 