#!/usr/bin/env python3
"""
Gemini API Tier Diagnostic Script
Testet die Gemini API und identifiziert das aktuelle Tier (Free vs Pay-as-you-go)
"""

import os
import sys
import time
import json
import asyncio
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from src.config.settings import settings
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    import requests
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Stelle sicher, dass alle Abhängigkeiten installiert sind:")
    print("pip install google-generativeai")
    sys.exit(1)

class GeminiTierChecker:
    def __init__(self):
        self.api_key = settings.google_api_key
        if not self.api_key:
            print("❌ Keine Google API Key gefunden!")
            print("Stelle sicher, dass GOOGLE_API_KEY in den Umgebungsvariablen gesetzt ist.")
            sys.exit(1)
        
        genai.configure(api_key=self.api_key)
        self.results = {}
    
    def check_api_key_format(self):
        """Prüfe das Format des API Keys"""
        print("🔍 Prüfe API Key Format...")
        
        if self.api_key.startswith('AIza'):
            print("✅ API Key Format: Standard Google AI Studio Key")
            self.results['key_format'] = 'ai_studio'
        elif len(self.api_key) > 50 and '-' in self.api_key:
            print("✅ API Key Format: Möglicherweise Service Account Key")
            self.results['key_format'] = 'service_account'
        else:
            print("⚠️ API Key Format: Unbekannt")
            self.results['key_format'] = 'unknown'
    
    def test_basic_connectivity(self):
        """Teste grundlegende API-Verbindung"""
        print("\n🔗 Teste grundlegende API-Verbindung...")
        
        try:
            # Liste verfügbare Modelle
            models = genai.list_models()
            model_list = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            
            print(f"✅ API-Verbindung erfolgreich!")
            print(f"📊 Verfügbare Modelle: {len(model_list)}")
            
            self.results['connectivity'] = True
            self.results['available_models'] = model_list[:5]  # Erste 5 Modelle
            
        except Exception as e:
            print(f"❌ API-Verbindung fehlgeschlagen: {e}")
            self.results['connectivity'] = False
            return False
        
        return True
    
    def test_rate_limits(self):
        """Teste Rate Limits durch schnelle aufeinanderfolgende Requests"""
        print("\n⏱️ Teste Rate Limits...")
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        test_requests = []
        
        try:
            start_time = time.time()
            
            # Sende mehrere schnelle Requests
            for i in range(10):
                try:
                    response = model.generate_content(
                        f"Antworte nur mit einer Zahl: {i+1}",
                        generation_config=genai.types.GenerationConfig(
                            temperature=0,
                            max_output_tokens=10
                        )
                    )
                    
                    request_time = time.time() - start_time
                    test_requests.append({
                        'request_num': i+1,
                        'time': request_time,
                        'success': True,
                        'response_length': len(response.text) if response.text else 0
                    })
                    
                    print(f"  Request {i+1}: ✅ ({request_time:.2f}s)")
                    
                except Exception as e:
                    error_msg = str(e)
                    test_requests.append({
                        'request_num': i+1,
                        'time': time.time() - start_time,
                        'success': False,
                        'error': error_msg
                    })
                    
                    if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                        print(f"  Request {i+1}: ❌ Rate Limit erreicht: {error_msg}")
                        break
                    else:
                        print(f"  Request {i+1}: ❌ Fehler: {error_msg}")
                
                # Kleine Pause zwischen Requests
                time.sleep(0.1)
            
            self.results['rate_limit_test'] = test_requests
            
            # Analysiere Rate Limit Verhalten
            successful_requests = [r for r in test_requests if r['success']]
            failed_requests = [r for r in test_requests if not r['success']]
            
            print(f"\n📊 Rate Limit Analyse:")
            print(f"   ✅ Erfolgreiche Requests: {len(successful_requests)}/10")
            print(f"   ❌ Fehlgeschlagene Requests: {len(failed_requests)}/10")
            
            if len(successful_requests) >= 8:
                print("   🎯 Vermutung: Pay-as-you-go Tier (hohe Rate Limits)")
                self.results['estimated_tier'] = 'pay_as_you_go'
            elif len(successful_requests) <= 3:
                print("   🎯 Vermutung: Free Tier (niedrige Rate Limits)")
                self.results['estimated_tier'] = 'free'
            else:
                print("   🎯 Vermutung: Unklares Tier oder temporäre Limits")
                self.results['estimated_tier'] = 'unclear'
                
        except Exception as e:
            print(f"❌ Rate Limit Test fehlgeschlagen: {e}")
            self.results['rate_limit_test'] = []
    
    def test_model_access(self):
        """Teste Zugriff auf verschiedene Modelle"""
        print("\n🧪 Teste Modell-Zugriff...")
        
        test_models = [
            'gemini-1.5-pro',
            'gemini-1.5-flash', 
            'gemini-2.0-flash-exp',
            'gemini-2.5-flash',
            'gemini-2.5-pro'
        ]
        
        model_access = {}
        
        for model_name in test_models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    "Sage nur 'OK'",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0,
                        max_output_tokens=5
                    )
                )
                
                if response.text:
                    print(f"  {model_name}: ✅ Verfügbar")
                    model_access[model_name] = True
                else:
                    print(f"  {model_name}: ⚠️ Antwort leer")
                    model_access[model_name] = False
                    
            except Exception as e:
                error_msg = str(e)
                if "not found" in error_msg.lower() or "not available" in error_msg.lower():
                    print(f"  {model_name}: ❌ Nicht verfügbar")
                else:
                    print(f"  {model_name}: ❌ Fehler: {error_msg}")
                model_access[model_name] = False
            
            time.sleep(0.2)  # Kurze Pause zwischen Tests
        
        self.results['model_access'] = model_access
        
        # Analyse der verfügbaren Modelle
        available_count = sum(model_access.values())
        if available_count >= 4:
            print(f"   🎯 {available_count}/5 Modelle verfügbar - wahrscheinlich Pay-as-you-go")
        elif available_count <= 2:
            print(f"   🎯 {available_count}/5 Modelle verfügbar - wahrscheinlich Free Tier")
        else:
            print(f"   🎯 {available_count}/5 Modelle verfügbar - gemischter Zugang")
    
    def check_quota_headers(self):
        """Versuche Quota-Informationen aus HTTP-Headers zu extrahieren"""
        print("\n📊 Prüfe Quota-Header...")
        
        try:
            # Direkter HTTP-Request zur Gemini API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": "Test"}]
                }],
                "generationConfig": {
                    "temperature": 0,
                    "maxOutputTokens": 5
                }
            }
            
            response = requests.post(url, json=payload)
            
            # Prüfe Response-Headers auf Quota-Informationen
            headers = response.headers
            quota_headers = {}
            
            for header, value in headers.items():
                if any(keyword in header.lower() for keyword in ['quota', 'limit', 'remaining', 'reset']):
                    quota_headers[header] = value
            
            if quota_headers:
                print("   📋 Gefundene Quota-Header:")
                for header, value in quota_headers.items():
                    print(f"      {header}: {value}")
                self.results['quota_headers'] = quota_headers
            else:
                print("   ⚠️ Keine Quota-Header gefunden")
                self.results['quota_headers'] = {}
                
        except Exception as e:
            print(f"   ❌ Fehler beim Prüfen der Header: {e}")
            self.results['quota_headers'] = {}
    
    def generate_report(self):
        """Generiere einen zusammenfassenden Bericht"""
        print("\n" + "="*60)
        print("📋 GEMINI API TIER DIAGNOSE BERICHT")
        print("="*60)
        
        # Bestimme wahrscheinliches Tier
        tier_indicators = []
        
        if hasattr(self, 'results'):
            # Rate Limit Analyse
            if 'estimated_tier' in self.results:
                tier_indicators.append(self.results['estimated_tier'])
            
            # Modell-Zugang
            if 'model_access' in self.results:
                available_models = sum(self.results['model_access'].values())
                if available_models >= 4:
                    tier_indicators.append('pay_as_you_go')
                elif available_models <= 2:
                    tier_indicators.append('free')
        
        # Finale Einschätzung
        if tier_indicators:
            from collections import Counter
            tier_count = Counter(tier_indicators)
            most_likely_tier = tier_count.most_common(1)[0][0]
        else:
            most_likely_tier = 'unknown'
        
        print(f"\n🎯 WAHRSCHEINLICHES TIER: ", end="")
        if most_likely_tier == 'free':
            print("🆓 FREE TIER")
            print("   • Niedrige Rate Limits (15 Requests/Minute)")
            print("   • Eingeschränkter Modell-Zugang")
            print("   • Kann Processing-Hänger verursachen")
            print("\n💡 EMPFEHLUNG: Upgrade auf Pay-as-you-go für produktive Nutzung")
        elif most_likely_tier == 'pay_as_you_go':
            print("💳 PAY-AS-YOU-GO TIER")
            print("   • Höhere Rate Limits")
            print("   • Vollständiger Modell-Zugang")
            print("   • Bessere Performance")
        else:
            print("❓ UNBEKANNT")
            print("   • Tier konnte nicht eindeutig bestimmt werden")
        
        print(f"\n⏰ Diagnose-Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Speichere detaillierte Ergebnisse
        with open('gemini_tier_report.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"📄 Detaillierter Bericht gespeichert: gemini_tier_report.json")
        
        return most_likely_tier

def main():
    print("🚀 Gemini API Tier Checker")
    print("="*40)
    
    checker = GeminiTierChecker()
    
    # Führe alle Tests durch
    checker.check_api_key_format()
    
    if not checker.test_basic_connectivity():
        print("\n❌ Grundlegende API-Verbindung fehlgeschlagen. Prüfe API Key und Internetverbindung.")
        return
    
    checker.test_rate_limits()
    checker.test_model_access()
    checker.check_quota_headers()
    
    # Generiere finalen Bericht
    tier = checker.generate_report()
    
    # CLI-spezifische Empfehlungen
    print("\n" + "="*60)
    print("🛠️ CLI PROCESSING EMPFEHLUNGEN")
    print("="*60)
    
    if tier == 'free':
        print("⚡ Verwende den --fast Modus für Dokument-Processing:")
        print("   ./ki-cli.sh process dokument.txt --fast")
        print("\n🔧 Oder konfiguriere längere Timeouts:")
        print("   ./ki-cli.sh process dokument.txt --verbose")
    elif tier == 'pay_as_you_go':
        print("✅ Normaler Modus sollte funktionieren:")
        print("   ./ki-cli.sh process dokument.txt --verbose")
    else:
        print("🔍 Teste beide Modi:")
        print("   ./ki-cli.sh process dokument.txt --fast    # Für schnelle Tests")
        print("   ./ki-cli.sh process dokument.txt --verbose # Für vollständige Verarbeitung")

if __name__ == "__main__":
    main() 