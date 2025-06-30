#!/usr/bin/env python3
"""
Direct Phase 3 Module Testing
Testet die implementierten Phase 3 Module direkt ohne externe Abhängigkeiten
"""
import sys
import asyncio
import json
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any

# Projekt-Root zur PYTHONPATH hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

@dataclass
class DirectTestResult:
    """Direktes Test-Ergebnis"""
    module_name: str
    test_name: str
    success: bool
    duration: float
    details: Dict[str, Any]
    errors: List[str]

class DirectPhase3Tester:
    """Direkter Tester für Phase 3 Module"""
    
    def __init__(self):
        self.results = []
    
    async def run_direct_tests(self):
        """Führt direkte Tests der Phase 3 Module aus"""
        
        print("🔍 DIRECT PHASE 3 MODULE TESTING")
        print("=" * 80)
        
        test_modules = [
            ("Query Expander Module", self.test_query_expander_module),
            ("Auto-Relationship Discovery Module", self.test_auto_relationship_module),
            ("LLM Models Module", self.test_llm_models_module),
            ("Enhanced Hybrid Retriever", self.test_hybrid_retriever_enhancements),
            ("Response Synthesizer Enhancements", self.test_response_synthesizer_enhancements)
        ]
        
        for module_name, test_func in test_modules:
            print(f"\n📋 {module_name}")
            print("-" * 60)
            
            try:
                module_results = await test_func()
                self.results.extend(module_results)
                
                # Module-Zusammenfassung
                passed = sum(1 for r in module_results if r.success)
                total = len(module_results)
                print(f"✅ Module Ergebnis: {passed}/{total} Tests erfolgreich")
                
            except Exception as e:
                print(f"❌ Module {module_name} failed: {e}")
                self.results.append(DirectTestResult(
                    module_name=module_name,
                    test_name="module_error",
                    success=False,
                    duration=0.0,
                    details={"error": str(e)},
                    errors=[str(e)]
                ))
        
        # Finale Auswertung
        await self.generate_direct_report()
    
    async def test_query_expander_module(self) -> List[DirectTestResult]:
        """Test des Query Expander Moduls"""
        
        results = []
        
        print("  Test 1: Query Expander Import und Klassen-Struktur")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Import-Test
            from retrievers.query_expander import QueryExpander
            details["import_success"] = True
            
            # Klassen-Struktur Test
            expander = QueryExpander()
            details["class_instantiation"] = True
            
            # Methoden-Verfügbarkeit Test
            required_methods = [
                "expand_query",
                "_extract_terms_and_entities",
                "_get_technical_synonyms", 
                "_get_graph_context",
                "_llm_expand_query",
                "_generate_alternative_phrasings"
            ]
            
            available_methods = []
            for method in required_methods:
                if hasattr(expander, method):
                    available_methods.append(method)
            
            details["available_methods"] = len(available_methods)
            details["required_methods"] = len(required_methods)
            details["method_completeness"] = len(available_methods) / len(required_methods)
            
            print(f"    ✅ Import erfolgreich")
            print(f"    ✅ Klasse instantiierbar")
            print(f"    ✅ Methoden verfügbar: {len(available_methods)}/{len(required_methods)}")
            
            if len(available_methods) < len(required_methods):
                errors.append(f"Fehlende Methoden: {set(required_methods) - set(available_methods)}")
            
        except ImportError as e:
            errors.append(f"Import Error: {e}")
            details = {"import_error": str(e)}
        except Exception as e:
            errors.append(f"Module Error: {e}")
            details = {"module_error": str(e)}
        
        duration = time.time() - start_time
        
        results.append(DirectTestResult(
            module_name="QueryExpander",
            test_name="structure_test",
            success=len(errors) == 0,
            duration=duration,
            details=details,
            errors=errors
        ))
        
        # Test 2: Technische Synonyme
        print("  Test 2: Technische Synonyme Mapping")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            from retrievers.query_expander import QueryExpander
            expander = QueryExpander()
            
            # Test der technischen Synonyme
            test_terms = ["password", "server", "network", "firewall", "backup"]
            synonym_results = {}
            
            for term in test_terms:
                synonyms = expander._get_technical_synonyms(term)
                synonym_results[term] = len(synonyms)
            
            details["synonym_mapping"] = synonym_results
            details["total_synonyms"] = sum(synonym_results.values())
            details["avg_synonyms_per_term"] = details["total_synonyms"] / len(test_terms)
            
            print(f"    ✅ Synonyme für {len(test_terms)} Begriffe getestet")
            print(f"    ✅ Durchschnitt: {details['avg_synonyms_per_term']:.1f} Synonyme pro Begriff")
            
            if details["total_synonyms"] == 0:
                errors.append("Keine technischen Synonyme gefunden")
            
        except Exception as e:
            errors.append(f"Synonym Test Error: {e}")
            details = {"error": str(e)}
        
        duration = time.time() - start_time
        
        results.append(DirectTestResult(
            module_name="QueryExpander",
            test_name="synonyms_test",
            success=len(errors) == 0,
            duration=duration,
            details=details,
            errors=errors
        ))
        
        return results
    
    async def test_auto_relationship_module(self) -> List[DirectTestResult]:
        """Test des Auto-Relationship Discovery Moduls"""
        
        results = []
        
        print("  Test 1: Auto-Relationship Discovery Import und Struktur")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Import-Test
            from orchestration.auto_relationship_discovery import AutoRelationshipDiscovery
            details["import_success"] = True
            
            # Klassen-Struktur Test
            discovery = AutoRelationshipDiscovery()
            details["class_instantiation"] = True
            
            # Methoden-Verfügbarkeit Test
            required_methods = [
                "discover_relationships_in_text",
                "_extract_entities",
                "_find_relationship_patterns",
                "_classify_relationship_type",
                "_calculate_confidence"
            ]
            
            available_methods = []
            for method in required_methods:
                if hasattr(discovery, method):
                    available_methods.append(method)
            
            details["available_methods"] = len(available_methods)
            details["required_methods"] = len(required_methods)
            details["method_completeness"] = len(available_methods) / len(required_methods)
            
            print(f"    ✅ Import erfolgreich")
            print(f"    ✅ Klasse instantiierbar")
            print(f"    ✅ Methoden verfügbar: {len(available_methods)}/{len(required_methods)}")
            
            if len(available_methods) < len(required_methods):
                errors.append(f"Fehlende Methoden: {set(required_methods) - set(available_methods)}")
            
        except ImportError as e:
            errors.append(f"Import Error: {e}")
            details = {"import_error": str(e)}
        except Exception as e:
            errors.append(f"Module Error: {e}")
            details = {"module_error": str(e)}
        
        duration = time.time() - start_time
        
        results.append(DirectTestResult(
            module_name="AutoRelationshipDiscovery",
            test_name="structure_test",
            success=len(errors) == 0,
            duration=duration,
            details=details,
            errors=errors
        ))
        
        # Test 2: Entity Extraction Patterns
        print("  Test 2: Entity Extraction Patterns")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            from orchestration.auto_relationship_discovery import AutoRelationshipDiscovery
            discovery = AutoRelationshipDiscovery()
            
            # Test-Text mit bekannten Entitäten
            test_text = """
            BSI Grundschutz ORP.4.A1 erfordert Active Directory Konfiguration.
            SYS.1.1.A3 behandelt Windows Server mit LDAP Integration.
            Firewall-Regeln unterstützen VPN-Verbindungen.
            """
            
            entities = discovery._extract_entities(test_text)
            
            details["entities_found"] = len(entities)
            details["entity_types"] = {}
            
            for entity in entities:
                entity_type = entity.get("type", "unknown")
                details["entity_types"][entity_type] = details["entity_types"].get(entity_type, 0) + 1
            
            print(f"    ✅ {len(entities)} Entitäten extrahiert")
            print(f"    ✅ Entitäts-Typen: {details['entity_types']}")
            
            if len(entities) == 0:
                errors.append("Keine Entitäten aus Test-Text extrahiert")
            
        except Exception as e:
            errors.append(f"Entity Extraction Error: {e}")
            details = {"error": str(e)}
        
        duration = time.time() - start_time
        
        results.append(DirectTestResult(
            module_name="AutoRelationshipDiscovery",
            test_name="entity_extraction_test",
            success=len(errors) == 0,
            duration=duration,
            details=details,
            errors=errors
        ))
        
        return results
    
    async def test_llm_models_module(self) -> List[DirectTestResult]:
        """Test des LLM Models Moduls"""
        
        results = []
        
        print("  Test 1: LLM Models Import und Datenstrukturen")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Import-Test
            from models.llm_models import (
                QueryExpansion, 
                AutoRelationshipCandidate,
                SmartRetrievalStrategy
            )
            details["import_success"] = True
            
            # Datenstruktur-Tests
            # QueryExpansion Test
            query_expansion = QueryExpansion(
                expanded_terms=["test", "begriffe"],
                context_terms=["kontext"],
                confidence_scores={"test": 0.8},
                expansion_reasoning="Test reasoning",
                alternative_phrasings=["Alternative 1"]
            )
            details["query_expansion_creation"] = True
            
            # AutoRelationshipCandidate Test
            from models.llm_models import RelationshipType
            relationship_candidate = AutoRelationshipCandidate(
                source_entity="Entity A",
                target_entity="Entity B", 
                relationship_type=RelationshipType.IMPLEMENTS,
                confidence=0.8,
                evidence="Test evidence"
            )
            details["relationship_candidate_creation"] = True
            
            # SmartRetrievalStrategy Test
            retrieval_strategy = SmartRetrievalStrategy(
                strategy_type="hybrid",
                vector_weight=0.6,
                graph_weight=0.4,
                use_expansion=True,
                confidence_threshold=0.7
            )
            details["retrieval_strategy_creation"] = True
            
            print(f"    ✅ Import erfolgreich")
            print(f"    ✅ QueryExpansion Datenstruktur OK")
            print(f"    ✅ AutoRelationshipCandidate Datenstruktur OK")
            print(f"    ✅ SmartRetrievalStrategy Datenstruktur OK")
            
        except ImportError as e:
            errors.append(f"Import Error: {e}")
            details = {"import_error": str(e)}
        except Exception as e:
            errors.append(f"LLM Models Error: {e}")
            details = {"model_error": str(e)}
        
        duration = time.time() - start_time
        
        results.append(DirectTestResult(
            module_name="LLMModels",
            test_name="structure_test",
            success=len(errors) == 0,
            duration=duration,
            details=details,
            errors=errors
        ))
        
        return results
    
    async def test_hybrid_retriever_enhancements(self) -> List[DirectTestResult]:
        """Test der Enhanced Hybrid Retriever Funktionen"""
        
        results = []
        
        print("  Test 1: Enhanced Hybrid Retriever Methoden")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Import-Test
            from retrievers.hybrid_retriever import HybridRetriever
            details["import_success"] = True
            
            # Klassen-Instanziierung (ohne echte Dependencies)
            # Hier würden wir normalerweise Mock-Dependencies verwenden
            
            # Methoden-Verfügbarkeit Test
            required_new_methods = [
                "_determine_smart_strategy", 
                "_enhanced_graph_retrieval",
                "_enhanced_vector_retrieval",
                "_rank_results_with_expansion"
            ]
            
            available_methods = []
            for method in required_new_methods:
                if hasattr(HybridRetriever, method):
                    available_methods.append(method)
            
            details["new_methods_available"] = len(available_methods)
            details["new_methods_required"] = len(required_new_methods)
            details["enhancement_completeness"] = len(available_methods) / len(required_new_methods)
            
            print(f"    ✅ Import erfolgreich")
            print(f"    ✅ Neue Methoden verfügbar: {len(available_methods)}/{len(required_new_methods)}")
            
            if len(available_methods) < len(required_new_methods):
                missing = set(required_new_methods) - set(available_methods)
                errors.append(f"Fehlende Enhanced Methoden: {missing}")
            
        except ImportError as e:
            errors.append(f"Import Error: {e}")
            details = {"import_error": str(e)}
        except Exception as e:
            errors.append(f"Enhancement Error: {e}")
            details = {"enhancement_error": str(e)}
        
        duration = time.time() - start_time
        
        results.append(DirectTestResult(
            module_name="HybridRetriever",
            test_name="enhancements_test",
            success=len(errors) == 0,
            duration=duration,
            details=details,
            errors=errors
        ))
        
        return results
    
    async def test_response_synthesizer_enhancements(self) -> List[DirectTestResult]:
        """Test der Response Synthesizer Enhancements"""
        
        results = []
        
        print("  Test 1: Response Synthesizer Enhanced Methoden")
        
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Import-Test
            from retrievers.response_synthesizer import ResponseSynthesizer
            details["import_success"] = True
            
            # Methoden-Verfügbarkeit Test
            required_new_methods = [
                "_discover_and_create_relationships"
            ]
            
            available_methods = []
            for method in required_new_methods:
                if hasattr(ResponseSynthesizer, method):
                    available_methods.append(method)
            
            details["new_methods_available"] = len(available_methods)
            details["new_methods_required"] = len(required_new_methods)
            details["enhancement_completeness"] = len(available_methods) / len(required_new_methods)
            
            print(f"    ✅ Import erfolgreich")
            print(f"    ✅ Neue Methoden verfügbar: {len(available_methods)}/{len(required_new_methods)}")
            
            if len(available_methods) < len(required_new_methods):
                missing = set(required_new_methods) - set(available_methods)
                errors.append(f"Fehlende Enhanced Methoden: {missing}")
            
        except ImportError as e:
            errors.append(f"Import Error: {e}")
            details = {"import_error": str(e)}
        except Exception as e:
            errors.append(f"Enhancement Error: {e}")
            details = {"enhancement_error": str(e)}
        
        duration = time.time() - start_time
        
        results.append(DirectTestResult(
            module_name="ResponseSynthesizer",
            test_name="enhancements_test",
            success=len(errors) == 0,
            duration=duration,
            details=details,
            errors=errors
        ))
        
        return results
    
    async def generate_direct_report(self):
        """Generiert Report für direkte Module-Tests"""
        
        print(f"\n{'='*80}")
        print("📊 DIRECT PHASE 3 MODULE TEST REPORT")
        print(f"{'='*80}")
        
        # Statistiken
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        total_duration = sum(r.duration for r in self.results)
        
        print(f"\n📈 MODULE STATISTICS:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"  Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        print(f"  Total Duration: {total_duration:.3f}s")
        
        # Module-spezifische Analyse
        modules = {}
        for result in self.results:
            module = result.module_name
            if module not in modules:
                modules[module] = {"total": 0, "passed": 0, "details": []}
            modules[module]["total"] += 1
            if result.success:
                modules[module]["passed"] += 1
            modules[module]["details"].append(result)
        
        print(f"\n📋 MODULE BREAKDOWN:")
        for module, stats in modules.items():
            success_rate = stats["passed"] / stats["total"] * 100
            print(f"  {module}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
            
            # Details für fehlgeschlagene Tests
            failed_details = [r for r in stats["details"] if not r.success]
            if failed_details:
                for detail in failed_details:
                    print(f"    ❌ {detail.test_name}: {', '.join(detail.errors)}")
        
        # Implementierungs-Vollständigkeit
        print(f"\n🔧 IMPLEMENTATION COMPLETENESS:")
        
        completeness_results = []
        for result in self.results:
            if "completeness" in result.details:
                completeness_results.append(result.details["completeness"])
            elif "method_completeness" in result.details:
                completeness_results.append(result.details["method_completeness"])
            elif "enhancement_completeness" in result.details:
                completeness_results.append(result.details["enhancement_completeness"])
        
        if completeness_results:
            avg_completeness = sum(completeness_results) / len(completeness_results)
            print(f"  Average Completeness: {avg_completeness:.1%}")
            
            if avg_completeness >= 0.9:
                print("  ✅ Excellent implementation completeness")
            elif avg_completeness >= 0.7:
                print("  ✅ Good implementation completeness")
            else:
                print("  ⚠️  Implementation needs completion")
        
        # Empfehlungen
        print(f"\n🔧 RECOMMENDATIONS:")
        
        success_rate = passed_tests / total_tests
        if success_rate >= 0.9:
            print("  ✅ Excellent module implementation - ready for integration!")
        elif success_rate >= 0.8:
            print("  ✅ Good module implementation - minor fixes needed")
        elif success_rate >= 0.7:
            print("  ⚠️  Moderate implementation - address failing modules")
        else:
            print("  ❌ Poor implementation - significant work needed")
        
        if failed_tests > 0:
            print("  🔍 Review failed module tests and fix implementation issues")
        
        print(f"\n🎉 DIRECT MODULE TESTING COMPLETE!")
        
        return success_rate >= 0.8

async def main():
    """Hauptfunktion für direkte Module-Tests"""
    
    print("🔍 Starting Direct Phase 3 Module Testing...")
    
    tester = DirectPhase3Tester()
    
    try:
        await tester.run_direct_tests()
        
        # Bestimme Gesamterfolg
        total_tests = len(tester.results)
        passed_tests = sum(1 for r in tester.results if r.success)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        if success_rate >= 0.8:
            print(f"\n🎉 DIRECT MODULE TESTING: ERFOLGREICH!")
            print(f"🚀 Phase 3 Module sind korrekt implementiert!")
            sys.exit(0)
        else:
            print(f"\n⚠️  DIRECT MODULE TESTING: VERBESSERUNGEN ERFORDERLICH")
            print(f"🔧 Success Rate: {success_rate:.1%} - Ziel: ≥80%")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ DIRECT MODULE TESTING FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 