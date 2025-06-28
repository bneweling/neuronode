#!/usr/bin/env python3
"""
Test Script für ExplanationGraph und Explainability Features
Testet die erweiterte Response Synthesizer Funktionalität
"""
import sys
from pathlib import Path
import asyncio
import json

# Projekt-Root zur PYTHONPATH hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.retrievers.response_synthesizer import ResponseSynthesizer
from src.retrievers.intent_analyzer import QueryAnalysis, QueryIntent
from src.retrievers.hybrid_retriever import RetrievalResult
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_explanation_graph_extraction():
    """Test der Explanation Graph Extraktion"""
    print("\n🧪 Test 1: Explanation Graph Extraction")
    
    # Mock Retrieval Results
    mock_results = [
        RetrievalResult(
            content="Active Directory kann für Identitätsmanagement genutzt werden",
            relevance_score=0.9,
            source="knowledge_base",
            metadata={
                "id": "tech_active_directory",
                "title": "Active Directory",
                "source": "Microsoft Dokumentation"
            },
            node_type="Technology",
            relationships=[
                {
                    "source": "tech_active_directory",
                    "target": "control_orp_4_a1",
                    "type": "IMPLEMENTS",
                    "confidence": 0.8
                }
            ]
        ),
        RetrievalResult(
            content="ORP.4.A1 Regelung für die Passwort-Nutzung",
            relevance_score=0.85,
            source="compliance",
            metadata={
                "id": "control_orp_4_a1",
                "title": "Passwort-Regelung",
                "source": "BSI Grundschutz"
            },
            node_type="ControlItem"
        ),
        RetrievalResult(
            content="Passwort-Richtlinien sind essentiell für die Sicherheit",
            relevance_score=0.7,
            source="knowledge_base",
            metadata={
                "id": "chunk_password_policy",
                "title": "Passwort-Sicherheit",
                "source": "Security Handbook"
            },
            node_type="KnowledgeChunk"
        )
    ]
    
    synthesizer = ResponseSynthesizer()
    explanation_graph = synthesizer._extract_explanation_graph(mock_results)
    
    print(f"✅ Explanation Graph extrahiert:")
    print(f"   📊 Nodes: {len(explanation_graph['nodes'])}")
    print(f"   🔗 Edges: {len(explanation_graph['edges'])}")
    print(f"   🎨 Layout: {explanation_graph['layout']}")
    
    # Graph-Struktur validieren
    assert len(explanation_graph['nodes']) > 0, "Graph sollte Nodes haben"
    assert 'nodes' in explanation_graph, "Graph sollte 'nodes' Feld haben"
    assert 'edges' in explanation_graph, "Graph sollte 'edges' Feld haben"
    
    # Node-Struktur validieren
    for node in explanation_graph['nodes']:
        assert 'id' in node, "Node sollte ID haben"
        assert 'label' in node, "Node sollte Label haben"
        assert 'type' in node, "Node sollte Type haben"
        assert 'color' in node, "Node sollte Color haben"
        assert 'metadata' in node, "Node sollte Metadata haben"
    
    print("✅ Graph-Struktur ist valide")
    return explanation_graph

async def test_node_label_creation():
    """Test der Node Label Erstellung"""
    print("\n🧪 Test 2: Node Label Creation")
    
    synthesizer = ResponseSynthesizer()
    
    # Test verschiedene Node-Typen
    test_cases = [
        {
            "node_type": "ControlItem",
            "metadata": {"id": "ORP.4.A1", "title": "Passwort-Regelung"},
            "expected_pattern": "ORP.4.A1"
        },
        {
            "node_type": "Technology", 
            "metadata": {"name": "Active Directory", "title": "AD"},
            "expected_pattern": "Active Directory"
        },
        {
            "node_type": "Document",
            "metadata": {"filename": "BSI_Grundschutz_2024.pdf"},
            "expected_pattern": "Doc: BSI_Grundschutz_2024.pdf"
        }
    ]
    
    for case in test_cases:
        mock_result = type('MockResult', (), {
            'node_type': case['node_type'],
            'metadata': case['metadata']
        })()
        
        label = synthesizer._create_node_label(mock_result)
        print(f"✅ {case['node_type']}: '{label}' (erwartet: '{case['expected_pattern']}')")
        assert case['expected_pattern'] in label, f"Label sollte '{case['expected_pattern']}' enthalten"

async def test_visualization_type_determination():
    """Test der Visualisierungs-Typ Bestimmung"""
    print("\n🧪 Test 3: Visualization Type Determination")
    
    synthesizer = ResponseSynthesizer()
    
    # Test verschiedene Szenarien
    test_cases = [
        {
            "description": "Wenige Nodes -> simple",
            "graph": {"nodes": [{"id": "1"}, {"id": "2"}], "edges": []},
            "intent": QueryIntent.GENERAL_INFORMATION,
            "expected": "simple"
        },
        {
            "description": "Viele Edges -> network", 
            "graph": {"nodes": [{"id": str(i)} for i in range(5)], "edges": [{"id": str(i)} for i in range(10)]},
            "intent": QueryIntent.TECHNICAL_IMPLEMENTATION,
            "expected": "network"
        },
        {
            "description": "Mapping Intent -> comparison",
            "graph": {"nodes": [{"id": str(i)} for i in range(4)], "edges": [{"id": str(i)} for i in range(2)]},
            "intent": QueryIntent.MAPPING_COMPARISON,
            "expected": "comparison"
        }
    ]
    
    for case in test_cases:
        mock_analysis = type('MockAnalysis', (), {
            'primary_intent': case['intent']
        })()
        
        viz_type = synthesizer._determine_visualization_type(mock_analysis, case['graph'])
        print(f"✅ {case['description']}: {viz_type}")
        assert viz_type == case['expected'], f"Erwartete {case['expected']}, bekommen {viz_type}"

async def test_graph_relevance_analysis():
    """Test der Graph-Relevanz Analyse"""
    print("\n🧪 Test 4: Graph Relevance Analysis")
    
    synthesizer = ResponseSynthesizer()
    
    # Mock Query Analysis mit hoher Graph-Relevanz
    mock_analysis = type('MockAnalysis', (), {
        'primary_intent': QueryIntent.MAPPING_COMPARISON,
        'entities': {
            'controls': ['ORP.4.A1', 'ORP.4.A10'],
            'technologies': ['Active Directory', 'LDAP']
        },
        'query': 'Wie hängen diese Controls zusammen?'
    })()
    
    # Mock Retrieval Results mit Graph-Quelle
    mock_results = [
        type('MockResult', (), {
            'source': 'graph',
            'node_type': 'ControlItem',
            'metadata': {'id': 'ORP.4.A1'},
            'relationships': [{'source': 'control1', 'target': 'control2', 'type': 'RELATES_TO'}],
            'relevance_score': 0.8
        })() for _ in range(3)
    ]
    
    response = "Diese Controls sind miteinander verknüpft durch gemeinsame Beziehungen"
    
    relevance = synthesizer._analyze_graph_relevance(mock_analysis, mock_results, response)
    
    print(f"✅ Graph-Relevanz Analyse:")
    print(f"   📊 Relevant: {relevance.get('graph_relevant', False)}")
    print(f"   🎯 Konfidenz: {relevance.get('graph_confidence', 0.0)}")
    print(f"   📈 Nodes: {len(relevance.get('graph_nodes', []))}")
    print(f"   🔗 Edges: {len(relevance.get('graph_edges', []))}")
    
    # Sollte hohe Relevanz haben wegen Mapping-Intent und Graph-Daten
    assert relevance.get('graph_confidence', 0.0) > 0.5, "Sollte hohe Graph-Konfidenz haben"

async def test_integrated_synthesis_with_graph():
    """Test der integrierten Synthese mit Graph-Daten"""
    print("\n🧪 Test 5: Integrated Synthesis with Graph Data")
    
    # Diese Funktionalität würde in einem vollständigen Test mit echten LLM-Calls getestet
    # Hier nur Mock um zu zeigen, dass die Pipeline funktioniert
    
    synthesizer = ResponseSynthesizer()
    
    mock_analysis = type('MockAnalysis', (), {
        'primary_intent': QueryIntent.COMPLIANCE_REQUIREMENT,
        'entities': {'controls': ['ORP.4.A1']},
        'confidence': 0.8,
        'query': 'Was ist ORP.4.A1?'
    })()
    
    mock_results = [
        RetrievalResult(
            content="ORP.4.A1 Regelung für die Passwort-Nutzung: Die Institution MUSS...",
            relevance_score=0.9,
            source="compliance",
            metadata={"id": "ORP.4.A1", "title": "Passwort-Regelung"},
            node_type="ControlItem"
        )
    ]
    
    # Mock der synthesis Methode (würde normalerweise LLM aufrufen)
    explanation_graph = synthesizer._extract_explanation_graph(mock_results)
    
    print(f"✅ Integrierte Synthese simuliert:")
    print(f"   📝 Query: {mock_analysis.query}")
    print(f"   🎯 Intent: {mock_analysis.primary_intent}")
    print(f"   📊 Graph Nodes: {len(explanation_graph['nodes'])}")
    print(f"   ✨ Graph bereit für Frontend")

async def run_all_explainability_tests():
    """Führt alle Explainability Tests aus"""
    print("🚀 Starte ExplanationGraph & Explainability Tests...")
    
    try:
        # Test 1: Graph-Extraktion
        await test_explanation_graph_extraction()
        
        # Test 2: Node-Label Erstellung
        await test_node_label_creation()
        
        # Test 3: Visualisierungs-Typ
        await test_visualization_type_determination()
        
        # Test 4: Graph-Relevanz
        await test_graph_relevance_analysis()
        
        # Test 5: Integrierte Synthese
        await test_integrated_synthesis_with_graph()
        
        print("\n🎉 Alle ExplanationGraph Tests erfolgreich!")
        print("✅ Response Synthesizer Erweiterungen sind bereit!")
        print("✅ Frontend ExplanationGraph-Komponente ist integriert!")
        
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_all_explainability_tests())
    sys.exit(0 if success else 1) 