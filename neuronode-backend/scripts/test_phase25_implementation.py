#!/usr/bin/env python3
"""
Phase 2.5 Implementation Test Suite

Vollständiger Test der Phase 2.5 Implementierung:
- Golden Set Generierung
- Service Quality Validator 
- AI Services Monitor
- Integration Tests
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

# Füge das src-Verzeichnis zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config.settings import Settings
from src.monitoring.service_quality_validator import ServiceQualityValidator
from src.monitoring.ai_services_monitor import AIServicesMonitor, initialize_monitor
from src.processing.gemini_entity_extractor import GeminiEntityExtractor

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase25TestSuite:
    """Vollständige Test Suite für Phase 2.5"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.qa_dir = self.project_root / "quality_assurance"
        self.golden_sets_dir = self.qa_dir / "golden_sets"
        self.monitoring_dir = self.qa_dir / "monitoring"
        self.reports_dir = self.qa_dir / "reports"
        
        # Erstelle Verzeichnisse
        for dir_path in [self.qa_dir, self.golden_sets_dir, self.monitoring_dir, self.reports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.settings = Settings()
        self.test_results = {}
    
    def test_golden_set_generation(self) -> Dict[str, Any]:
        """Test Golden Set Generierung aus code-3.JSON"""
        logger.info("🔍 Teste Golden Set Generierung...")
        
        try:
            # Prüfe ob code-3.JSON existiert
            code3_path = self.project_root / "code-3.JSON"
            if not code3_path.exists():
                return {
                    "success": False,
                    "error": f"code-3.JSON nicht gefunden: {code3_path}",
                    "details": "Golden Set Generation übersprungen"
                }
            
            # Führe Golden Set Generator aus
            import subprocess
            script_path = self.project_root / "scripts" / "create_golden_set_from_code3.py"
            
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300  # 5 Minuten Timeout
            )
            
            # Prüfe ob Golden Sets erstellt wurden
            ner_golden_set = self.golden_sets_dir / "golden_set_ner_v1.0.jsonl"
            classification_golden_set = self.golden_sets_dir / "golden_set_classification_v1.0.jsonl"
            
            ner_exists = ner_golden_set.exists()
            classification_exists = classification_golden_set.exists()
            
            # Zähle Samples wenn Dateien existieren
            ner_samples = 0
            classification_samples = 0
            
            if ner_exists:
                with open(ner_golden_set, 'r', encoding='utf-8') as f:
                    ner_samples = sum(1 for line in f if line.strip())
            
            if classification_exists:
                with open(classification_golden_set, 'r', encoding='utf-8') as f:
                    classification_samples = sum(1 for line in f if line.strip())
            
            return {
                "success": result.returncode == 0,
                "ner_golden_set_created": ner_exists,
                "classification_golden_set_created": classification_exists,
                "ner_samples": ner_samples,
                "classification_samples": classification_samples,
                "stdout": result.stdout,
                "stderr": result.stderr if result.stderr else None
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Golden Set Generation Timeout (>5min)",
                "details": "Prozess zu langsam oder hängt"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Golden Set Generation Fehler: {e}",
                "details": str(e)
            }
    
    def test_ai_services_monitor(self) -> Dict[str, Any]:
        """Test AI Services Monitor"""
        logger.info("🔍 Teste AI Services Monitor...")
        
        try:
            # Initialisiere Monitor
            monitor = initialize_monitor(self.settings, self.monitoring_dir)
            
            # Simuliere API Calls für verschiedene Services
            test_calls = [
                ("GeminiEntityExtractor", "gemini-1.5-flash-latest", 150.5, 245, True, False),
                ("GeminiEntityExtractor", "gemini-1.5-flash-latest", 89.2, 134, True, True),  # Cache hit
                ("DocumentClassifier", "gemini-1.5-pro-latest", 230.8, 456, True, False),
                ("GeminiEntityExtractor", "gemini-1.5-flash-latest", 0, 0, False, False),  # Error
                ("DocumentClassifier", "gemini-1.5-pro-latest", 178.4, 298, True, False),
            ]
            
            for service, model, duration, tokens, success, cache_hit in test_calls:
                error_msg = "Simulated error" if not success else None
                monitor.record_api_call(service, model, duration, tokens, success, cache_hit, error_msg)
            
            # Teste Monitor Funktionen
            system_health = monitor.get_system_health()
            service_stats = monitor.get_service_stats()
            recent_calls = monitor.get_recent_calls(10)
            cost_breakdown = monitor.get_cost_breakdown(1)
            performance_summary = monitor.get_performance_summary(1)
            
            # Speichere Monitoring Report
            report_path = monitor.save_monitoring_report()
            
            return {
                "success": True,
                "active_services": len(service_stats),
                "total_calls": len(recent_calls),
                "system_health_available": system_health is not None,
                "cost_breakdown_available": len(cost_breakdown) > 0,
                "performance_summary_available": performance_summary["total_calls"] > 0,
                "report_saved": report_path.exists(),
                "report_path": str(report_path),
                "gemini_extractor_calls": service_stats.get("GeminiEntityExtractor", {}).total_calls if "GeminiEntityExtractor" in service_stats else 0,
                "document_classifier_calls": service_stats.get("DocumentClassifier", {}).total_calls if "DocumentClassifier" in service_stats else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"AI Services Monitor Fehler: {e}",
                "details": str(e)
            }
    
    def test_service_quality_validator(self) -> Dict[str, Any]:
        """Test Service Quality Validator"""
        logger.info("🔍 Teste Service Quality Validator...")
        
        try:
            # Prüfe ob Golden Sets existieren
            ner_golden_set = self.golden_sets_dir / "golden_set_ner_v1.0.jsonl"
            classification_golden_set = self.golden_sets_dir / "golden_set_classification_v1.0.jsonl"
            
            if not (ner_golden_set.exists() or classification_golden_set.exists()):
                return {
                    "success": False,
                    "error": "Keine Golden Sets verfügbar",
                    "details": "Golden Sets müssen zuerst generiert werden",
                    "ner_validation": False,
                    "classification_validation": False
                }
            
            # Initialisiere Validator
            validator = ServiceQualityValidator(self.golden_sets_dir, self.settings)
            
            validation_results = {}
            
            # NER Service Validation (falls Golden Set existiert)
            if ner_golden_set.exists():
                try:
                    ner_report = validator.validate_ner_service("v1.0")
                    ner_report_path = validator.save_quality_report(ner_report, self.reports_dir)
                    
                    validation_results["ner_validation"] = {
                        "success": True,
                        "f1_score": ner_report.ner_metrics.f1_score,
                        "precision": ner_report.ner_metrics.precision,
                        "recall": ner_report.ner_metrics.recall,
                        "total_samples": ner_report.total_samples,
                        "processing_time_ms": ner_report.processing_time_ms,
                        "error_rate": ner_report.error_rate,
                        "report_path": str(ner_report_path)
                    }
                except Exception as e:
                    validation_results["ner_validation"] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Classification Service Validation (falls Golden Set existiert)
            if classification_golden_set.exists():
                try:
                    classification_report = validator.validate_classification_service("v1.0")
                    classification_report_path = validator.save_quality_report(classification_report, self.reports_dir)
                    
                    validation_results["classification_validation"] = {
                        "success": True,
                        "accuracy": classification_report.classification_metrics.accuracy,
                        "f1_score": classification_report.classification_metrics.f1_score,
                        "precision": classification_report.classification_metrics.precision,
                        "recall": classification_report.classification_metrics.recall,
                        "total_samples": classification_report.total_samples,
                        "processing_time_ms": classification_report.processing_time_ms,
                        "error_rate": classification_report.error_rate,
                        "report_path": str(classification_report_path)
                    }
                except Exception as e:
                    validation_results["classification_validation"] = {
                        "success": False,
                        "error": str(e)
                    }
            
            return {
                "success": True,
                **validation_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Service Quality Validator Fehler: {e}",
                "details": str(e)
            }
    
    async def test_gemini_entity_extractor_integration(self) -> Dict[str, Any]:
        """Test GeminiEntityExtractor mit Monitor Integration"""
        logger.info("🔍 Teste GeminiEntityExtractor Integration...")
        
        try:
            # Initialisiere Services
            extractor = GeminiEntityExtractor()
            monitor = initialize_monitor(self.settings, self.monitoring_dir)
            
            # Test Text
            test_text = """
            Das BSI-Grundschutz-Kompendium enthält Sicherheitsmaßnahmen für die Informationssicherheit.
            Die ISO 27001 ist ein internationaler Standard für Informationssicherheits-Management-Systeme.
            Microsoft Azure bietet Cloud-Computing-Services mit verschiedenen Sicherheitsfeatures.
            """
            
            # Führe Entity Extraction durch (mit Monitor Tracking)
            async def extract_with_monitoring():
                with monitor.track_api_call("GeminiEntityExtractor", "gemini-1.5-flash-latest") as tracking:
                    # Verwende die synchrone extract_entities Methode
                    result = extractor.extract_entities(test_text)
                    
                    # Setze Token-Anzahl (Schätzung basierend auf Text-Länge)
                    estimated_tokens = len(test_text.split()) * 1.3  # Grobe Schätzung
                    tracking['set_tokens'](int(estimated_tokens))
                    
                    # Cache Hit Status (hier immer False, da echter API Call)
                    tracking['set_cache_hit'](False)
                    
                    return result
            
            # Führe Test aus
            extraction_result = await extract_with_monitoring()
            
            # Prüfe Monitor Status
            service_stats = monitor.get_service_stats("GeminiEntityExtractor")
            
            return {
                "success": True,
                "entities_extracted": len(extraction_result.entities),
                "extraction_successful": bool(extraction_result.entities),
                "monitor_recorded_call": "GeminiEntityExtractor" in service_stats,
                "monitored_service_stats": service_stats.get("GeminiEntityExtractor", {}).to_dict() if "GeminiEntityExtractor" in service_stats else None,
                "fallback_used": extraction_result.source == 'fallback',
                "processing_stats": {
                    "processing_time_ms": extraction_result.processing_time_ms,
                    "source": extraction_result.source,
                    "chunk_id": extraction_result.chunk_id
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"GeminiEntityExtractor Integration Fehler: {e}",
                "details": str(e)
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Führe alle Phase 2.5 Tests durch"""
        logger.info("🚀 Starte Phase 2.5 Test Suite...")
        
        # Test 1: Golden Set Generation
        logger.info("=" * 60)
        logger.info("TEST 1: Golden Set Generation")
        logger.info("=" * 60)
        self.test_results["golden_set_generation"] = self.test_golden_set_generation()
        
        # Test 2: AI Services Monitor
        logger.info("=" * 60)
        logger.info("TEST 2: AI Services Monitor")
        logger.info("=" * 60)
        self.test_results["ai_services_monitor"] = self.test_ai_services_monitor()
        
        # Test 3: GeminiEntityExtractor Integration
        logger.info("=" * 60)
        logger.info("TEST 3: GeminiEntityExtractor Integration")
        logger.info("=" * 60)
        self.test_results["gemini_extractor_integration"] = await self.test_gemini_entity_extractor_integration()
        
        # Test 4: Service Quality Validator
        logger.info("=" * 60)
        logger.info("TEST 4: Service Quality Validator")
        logger.info("=" * 60)
        self.test_results["service_quality_validator"] = self.test_service_quality_validator()
        
        return self.test_results
    
    def print_test_summary(self):
        """Drucke Test-Zusammenfassung"""
        logger.info("=" * 80)
        logger.info("📊 PHASE 2.5 TEST SUMMARY")
        logger.info("=" * 80)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result.get("success", False))
        
        logger.info(f"Durchgeführte Tests: {total_tests}")
        logger.info(f"Erfolgreiche Tests: {successful_tests}")
        logger.info(f"Erfolgsquote: {successful_tests/total_tests*100:.1f}%")
        logger.info("")
        
        for test_name, result in self.test_results.items():
            status = "✅ ERFOLGREICH" if result.get("success", False) else "❌ FEHLGESCHLAGEN"
            logger.info(f"{test_name}: {status}")
            
            if not result.get("success", False) and "error" in result:
                logger.info(f"  Fehler: {result['error']}")
            
            # Spezifische Details für verschiedene Tests
            if test_name == "golden_set_generation" and result.get("success", False):
                logger.info(f"  NER Samples: {result.get('ner_samples', 0)}")
                logger.info(f"  Classification Samples: {result.get('classification_samples', 0)}")
            
            elif test_name == "ai_services_monitor" and result.get("success", False):
                logger.info(f"  Aktive Services: {result.get('active_services', 0)}")
                logger.info(f"  Gesamt API Calls: {result.get('total_calls', 0)}")
            
            elif test_name == "service_quality_validator" and result.get("success", False):
                if "ner_validation" in result and result["ner_validation"].get("success", False):
                    logger.info(f"  NER F1-Score: {result['ner_validation']['f1_score']:.3f}")
                if "classification_validation" in result and result["classification_validation"].get("success", False):
                    logger.info(f"  Classification Accuracy: {result['classification_validation']['accuracy']:.3f}")
            
            elif test_name == "gemini_extractor_integration" and result.get("success", False):
                logger.info(f"  Extrahierte Entitäten: {result.get('entities_extracted', 0)}")
                logger.info(f"  Monitor Integration: {'✓' if result.get('monitor_recorded_call', False) else '✗'}")
        
        logger.info("=" * 80)
        
        if successful_tests == total_tests:
            logger.info("🎉 Alle Tests erfolgreich! Phase 2.5 ist bereit für Produktion.")
        else:
            logger.info("⚠️ Einige Tests fehlgeschlagen. Bitte Fehler beheben.")
        
        logger.info(f"📁 Quality Assurance Verzeichnis: {self.qa_dir}")
        logger.info(f"📁 Golden Sets: {self.golden_sets_dir}")
        logger.info(f"📁 Monitoring: {self.monitoring_dir}")
        logger.info(f"📁 Reports: {self.reports_dir}")


async def main():
    """Hauptfunktion"""
    logger.info("🚀 Starte Phase 2.5 Implementation Test Suite")
    
    try:
        test_suite = Phase25TestSuite()
        results = await test_suite.run_all_tests()
        test_suite.print_test_summary()
        
        # Beende mit Exit Code basierend auf Testergebnissen
        all_successful = all(result.get("success", False) for result in results.values())
        sys.exit(0 if all_successful else 1)
        
    except KeyboardInterrupt:
        logger.info("❌ Test Suite durch Benutzer abgebrochen")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler in Test Suite: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
