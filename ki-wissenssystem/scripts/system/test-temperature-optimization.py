#!/usr/bin/env python3
"""
Test-Skript für optimierte Temperatur-Einstellungen
Validiert die Leistung verschiedener Temperatur-Werte für spezifische Anwendungsfälle
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config.llm_config import LLMRouter, ModelPurpose
from src.config.settings import settings
import time
import json
from typing import Dict, List, Any
from datetime import datetime

class TemperatureOptimizationTester:
    def __init__(self):
        self.router = LLMRouter()
        self.test_results = []
        
    def test_classification_consistency(self, model_name: str, temperatures: List[float]) -> Dict[str, Any]:
        """Test classification consistency across different temperatures"""
        test_prompt = """
        Klassifiziere den folgenden Text in eine der Kategorien: 
        [Technisch, Wissenschaftlich, Geschäftlich, Persönlich]
        
        Text: "Die neue API-Implementierung bietet verbesserte Skalierbarkeit 
        und reduzierte Latenz für unsere Microservices-Architektur."
        
        Antwort nur mit der Kategorie:
        """
        
        results = {}
        for temp in temperatures:
            responses = []
            # Test 5 mal für Konsistenz
            for i in range(5):
                try:
                    model = self.router.models[model_name]
                    model.temperature = temp
                    response = model.invoke(test_prompt)
                    responses.append(response.content.strip())
                except Exception as e:
                    responses.append(f"ERROR: {str(e)}")
                    
            # Berechne Konsistenz
            unique_responses = len(set(responses))
            consistency_score = (5 - unique_responses + 1) / 5  # 1.0 = perfekt konsistent
            
            results[f"temp_{temp}"] = {
                "responses": responses,
                "consistency_score": consistency_score,
                "most_common": max(set(responses), key=responses.count) if responses else "N/A"
            }
            
        return results
    
    def test_extraction_completeness(self, model_name: str, temperatures: List[float]) -> Dict[str, Any]:
        """Test extraction completeness across different temperatures"""
        test_prompt = """
        Extrahiere alle wichtigen Informationen aus folgendem Text:
        
        "Das Projekt Alpha wurde am 15. März 2024 von Team Beta gestartet. 
        Das Budget beträgt 250.000 EUR mit einer Laufzeit von 8 Monaten. 
        Projektleiter ist Dr. Schmidt, Kontakt: schmidt@firma.de, Tel: +49-123-456789."
        
        Strukturiere die Antwort als JSON mit den Feldern:
        - projektname
        - startdatum  
        - team
        - budget
        - laufzeit
        - projektleiter
        - email
        - telefon
        """
        
        results = {}
        expected_fields = ["projektname", "startdatum", "team", "budget", "laufzeit", "projektleiter", "email", "telefon"]
        
        for temp in temperatures:
            try:
                model = self.router.models[model_name]
                model.temperature = temp
                response = model.invoke(test_prompt)
                
                # Versuche JSON zu parsen
                try:
                    json_response = json.loads(response.content.strip())
                    extracted_fields = list(json_response.keys())
                    completeness_score = len([f for f in expected_fields if f in extracted_fields]) / len(expected_fields)
                except json.JSONDecodeError:
                    extracted_fields = []
                    completeness_score = 0.0
                    
                results[f"temp_{temp}"] = {
                    "response": response.content.strip(),
                    "extracted_fields": extracted_fields,
                    "completeness_score": completeness_score
                }
                
            except Exception as e:
                results[f"temp_{temp}"] = {
                    "response": f"ERROR: {str(e)}",
                    "extracted_fields": [],
                    "completeness_score": 0.0
                }
                
        return results
    
    def test_synthesis_creativity(self, model_name: str, temperatures: List[float]) -> Dict[str, Any]:
        """Test synthesis creativity and quality across different temperatures"""
        test_prompt = """
        Schreibe eine kurze, professionelle Zusammenfassung (2-3 Sätze) für folgenden Sachverhalt:
        
        "Unser Unternehmen hat eine neue KI-basierte Lösung entwickelt, die die 
        Effizienz der Datenverarbeitung um 40% steigert und gleichzeitig die 
        Kosten um 25% reduziert."
        """
        
        results = {}
        for temp in temperatures:
            responses = []
            # Test 3 mal für Vielfalt
            for i in range(3):
                try:
                    model = self.router.models[model_name]
                    model.temperature = temp
                    response = model.invoke(test_prompt)
                    responses.append(response.content.strip())
                except Exception as e:
                    responses.append(f"ERROR: {str(e)}")
            
            # Berechne Vielfalt (vereinfacht durch Wortanzahl-Unterschiede)
            word_counts = [len(r.split()) for r in responses if not r.startswith("ERROR")]
            diversity_score = (max(word_counts) - min(word_counts)) / max(word_counts) if word_counts else 0
            
            results[f"temp_{temp}"] = {
                "responses": responses,
                "diversity_score": diversity_score,
                "avg_length": sum(word_counts) / len(word_counts) if word_counts else 0
            }
            
        return results
    
    def test_validation_accuracy(self, model_name: str, temperatures: List[float]) -> Dict[str, Any]:
        """Test validation accuracy across different temperatures"""
        test_cases = [
            {
                "text": "Die Hauptstadt von Deutschland ist Berlin.",
                "expected": "korrekt"
            },
            {
                "text": "Die Hauptstadt von Deutschland ist München.",
                "expected": "inkorrekt"
            },
            {
                "text": "Python ist eine Programmiersprache.",
                "expected": "korrekt"
            }
        ]
        
        results = {}
        for temp in temperatures:
            correct_validations = 0
            total_validations = len(test_cases)
            
            for test_case in test_cases:
                test_prompt = f"""
                Bewerte die folgende Aussage als "korrekt" oder "inkorrekt":
                
                Aussage: "{test_case['text']}"
                
                Antwort nur mit "korrekt" oder "inkorrekt":
                """
                
                try:
                    model = self.router.models[model_name]
                    model.temperature = temp
                    response = model.invoke(test_prompt)
                    
                    if test_case['expected'].lower() in response.content.lower():
                        correct_validations += 1
                        
                except Exception as e:
                    pass  # Fehler wird als falsche Validierung gewertet
            
            accuracy_score = correct_validations / total_validations
            
            results[f"temp_{temp}"] = {
                "accuracy_score": accuracy_score,
                "correct_validations": correct_validations,
                "total_validations": total_validations
            }
            
        return results
    
    def run_comprehensive_test(self):
        """Führt umfassende Tests für alle Anwendungsfälle durch"""
        print("🧪 Starte umfassende Temperatur-Optimierung Tests...")
        print("=" * 60)
        
        # Test-Konfiguration
        test_temperatures = [0.1, 0.2, 0.3, 0.5, 0.7]
        
        # Test-Modelle für verschiedene Anwendungsfälle
        test_models = {
            "classification": ["gemini-2.5-flash", "gemini-2.5-flash-lite-preview-06-17"],
            "extraction": ["gpt-4.1", "gpt-4o-mini"],
            "synthesis": ["claude-opus-4-20250514", "gemini-2.5-pro"],
            "validation": ["gpt-4o", "claude-sonnet-4-20250514"]
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for purpose, models in test_models.items():
            print(f"\n🔍 Testing {purpose.upper()}...")
            
            for model_name in models:
                if model_name not in self.router.models:
                    print(f"⚠️  Model {model_name} not available, skipping...")
                    continue
                    
                print(f"  Testing model: {model_name}")
                
                try:
                    if purpose == "classification":
                        results = self.test_classification_consistency(model_name, test_temperatures)
                    elif purpose == "extraction":
                        results = self.test_extraction_completeness(model_name, test_temperatures)
                    elif purpose == "synthesis":
                        results = self.test_synthesis_creativity(model_name, test_temperatures)
                    elif purpose == "validation":
                        results = self.test_validation_accuracy(model_name, test_temperatures)
                    
                    # Speichere Ergebnisse
                    test_result = {
                        "timestamp": timestamp,
                        "purpose": purpose,
                        "model": model_name,
                        "results": results
                    }
                    self.test_results.append(test_result)
                    
                    # Zeige beste Temperatur
                    best_temp = self.find_best_temperature(results, purpose)
                    print(f"    ✅ Beste Temperatur: {best_temp}")
                    
                except Exception as e:
                    print(f"    ❌ Fehler beim Testen von {model_name}: {str(e)}")
                    
                time.sleep(1)  # Kurze Pause zwischen Tests
        
        # Speichere alle Ergebnisse
        self.save_results(timestamp)
        self.print_summary()
    
    def find_best_temperature(self, results: Dict[str, Any], purpose: str) -> float:
        """Findet die beste Temperatur basierend auf dem Anwendungsfall"""
        best_temp = 0.1
        best_score = 0.0
        
        for temp_key, result in results.items():
            temp = float(temp_key.replace("temp_", ""))
            
            if purpose == "classification":
                score = result.get("consistency_score", 0.0)
            elif purpose == "extraction":
                score = result.get("completeness_score", 0.0)
            elif purpose == "synthesis":
                score = result.get("diversity_score", 0.0)
            elif purpose == "validation":
                score = result.get("accuracy_score", 0.0)
            else:
                score = 0.0
            
            if score > best_score:
                best_score = score
                best_temp = temp
                
        return best_temp
    
    def save_results(self, timestamp: str):
        """Speichert die Testergebnisse in einer JSON-Datei"""
        filename = f"temperature_optimization_results_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
        print(f"\n💾 Ergebnisse gespeichert in: {filepath}")
    
    def print_summary(self):
        """Druckt eine Zusammenfassung der Testergebnisse"""
        print("\n" + "=" * 60)
        print("📊 ZUSAMMENFASSUNG DER TEMPERATUR-OPTIMIERUNG")
        print("=" * 60)
        
        # Gruppiere Ergebnisse nach Anwendungsfall
        by_purpose = {}
        for result in self.test_results:
            purpose = result["purpose"]
            if purpose not in by_purpose:
                by_purpose[purpose] = []
            by_purpose[purpose].append(result)
        
        for purpose, results in by_purpose.items():
            print(f"\n🎯 {purpose.upper()}:")
            
            for result in results:
                model = result["model"]
                best_temp = self.find_best_temperature(result["results"], purpose)
                print(f"  {model}: Optimale Temperatur = {best_temp}")
        
        print("\n✅ Temperatur-Optimierung abgeschlossen!")
        print("📋 Empfohlene Einstellungen wurden in der LLM-Konfiguration implementiert.")

def main():
    """Hauptfunktion für das Temperatur-Optimierung Testing"""
    print("🚀 KI-Wissenssystem - Temperatur-Optimierung Tester")
    print("=" * 60)
    
    # Überprüfe API-Schlüssel
    missing_keys = []
    if not settings.openai_api_key:
        missing_keys.append("OpenAI")
    if not settings.anthropic_api_key:
        missing_keys.append("Anthropic")
    if not settings.google_api_key:
        missing_keys.append("Google")
    
    if missing_keys:
        print(f"⚠️  Warnung: Fehlende API-Schlüssel für: {', '.join(missing_keys)}")
        print("   Einige Tests werden übersprungen.")
    
    # Starte Tests
    tester = TemperatureOptimizationTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main() 