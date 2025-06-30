#!/usr/bin/env python3
"""
Vereinfachter Gemini API Tier Checker
Verwendet nur requests für HTTP-Calls - keine zusätzlichen Abhängigkeiten
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from src.config.settings import settings
except ImportError:
    print("❌ Kann settings nicht importieren. Prüfe, ob du im richtigen Verzeichnis bist.")
    sys.exit(1)

class SimpleGeminiChecker:
    def __init__(self):
        self.api_key = settings.google_api_key
        if not self.api_key:
            print("❌ Keine Google API Key gefunden!")
            print("Prüfe deine .env Datei oder Umgebungsvariablen.")
            sys.exit(1)
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.results = {}
        
        print(f"🔑 API Key gefunden: {self.api_key[:10]}...{self.api_key[-4:]}")
    
    def test_basic_connectivity(self):
        """Teste grundlegende API-Verbindung"""
        print("\n🔗 Teste grundlegende API-Verbindung...")
        
        try:
            # Liste verfügbare Modelle
            url = f"{self.base_url}/models?key={self.api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                print(f"✅ API-Verbindung erfolgreich!")
                print(f"📊 Verfügbare Modelle: {len(models)}")
                
                self.results['connectivity'] = True
                self.results['total_models'] = len(models)
                return True
            else:
                print(f"❌ API-Fehler: {response.status_code} - {response.text}")
                self.results['connectivity'] = False
                return False
                
        except Exception as e:
            print(f"❌ Verbindungsfehler: {e}")
            self.results['connectivity'] = False
            return False
    
    def test_rate_limits(self):
        """Teste Rate Limits durch schnelle aufeinanderfolgende Requests"""
        print("\n⏱️ Teste Rate Limits...")
        
        url = f"{self.base_url}/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        
        test_requests = []
        start_time = time.time()
        
        # Sende 10 schnelle Requests
        for i in range(10):
            payload = {
                "contents": [{
                    "parts": [{"text": f"Antworte nur mit der Zahl: {i+1}"}]
                }],
                "generationConfig": {
                    "temperature": 0,
                    "maxOutputTokens": 10
                }
            }
            
            try:
                response = requests.post(url, json=payload, timeout=10)
                request_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    text = ""
                    if 'candidates' in data and len(data['candidates']) > 0:
                        if 'content' in data['candidates'][0]:
                            parts = data['candidates'][0]['content'].get('parts', [])
                            if parts and 'text' in parts[0]:
                                text = parts[0]['text']
                    
                    test_requests.append({
                        'request_num': i+1,
                        'time': request_time,
                        'success': True,
                        'response_length': len(text),
                        'status_code': response.status_code
                    })
                    
                    print(f"  Request {i+1}: ✅ ({request_time:.2f}s) - '{text.strip()}'")
                    
                else:
                    error_msg = response.text
                    test_requests.append({
                        'request_num': i+1,
                        'time': request_time,
                        'success': False,
                        'error': error_msg,
                        'status_code': response.status_code
                    })
                    
                    if response.status_code == 429:
                        print(f"  Request {i+1}: ❌ Rate Limit erreicht (429)")
                        break
                    elif "quota" in error_msg.lower():
                        print(f"  Request {i+1}: ❌ Quota erreicht: {error_msg[:100]}")
                        break
                    else:
                        print(f"  Request {i+1}: ❌ Fehler {response.status_code}: {error_msg[:100]}")
                
            except Exception as e:
                test_requests.append({
                    'request_num': i+1,
                    'time': time.time() - start_time,
                    'success': False,
                    'error': str(e)
                })
                print(f"  Request {i+1}: ❌ Exception: {e}")
            
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
        
        # Prüfe auf spezifische Rate Limit Errors
        rate_limit_errors = [r for r in failed_requests if r.get('status_code') == 429]
        quota_errors = [r for r in failed_requests if 'quota' in str(r.get('error', '')).lower()]
        
        if rate_limit_errors:
            print(f"   ⚠️ 429 Rate Limit Errors: {len(rate_limit_errors)}")
        if quota_errors:
            print(f"   ⚠️ Quota Errors: {len(quota_errors)}")
    
    def test_model_access(self):
        """Teste Zugriff auf verschiedene Modelle"""
        print("\n🧪 Teste Modell-Zugriff...")
        
        test_models = [
            'gemini-1.5-pro',
            'gemini-1.5-flash', 
            'gemini-2.0-flash-exp',
            'gemini-pro'
        ]
        
        model_access = {}
        
        for model_name in test_models:
            try:
                url = f"{self.base_url}/models/{model_name}:generateContent?key={self.api_key}"
                payload = {
                    "contents": [{
                        "parts": [{"text": "Sage nur 'OK'"}]
                    }],
                    "generationConfig": {
                        "temperature": 0,
                        "maxOutputTokens": 5
                    }
                }
                
                response = requests.post(url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    print(f"  {model_name}: ✅ Verfügbar")
                    model_access[model_name] = True
                elif response.status_code == 404:
                    print(f"  {model_name}: ❌ Nicht verfügbar (404)")
                    model_access[model_name] = False
                else:
                    print(f"  {model_name}: ❌ Fehler {response.status_code}")
                    model_access[model_name] = False
                    
            except Exception as e:
                print(f"  {model_name}: ❌ Exception: {e}")
                model_access[model_name] = False
            
            time.sleep(0.2)  # Kurze Pause zwischen Tests
        
        self.results['model_access'] = model_access
        
        # Analyse der verfügbaren Modelle
        available_count = sum(model_access.values())
        print(f"   📊 {available_count}/{len(test_models)} Modelle verfügbar")
        
        if available_count >= 3:
            print(f"   🎯 Guter Modell-Zugang - wahrscheinlich Pay-as-you-go")
        elif available_count <= 1:
            print(f"   🎯 Eingeschränkter Modell-Zugang - wahrscheinlich Free Tier")
    
    def generate_report(self):
        """Generiere einen zusammenfassenden Bericht"""
        print("\n" + "="*60)
        print("📋 GEMINI API TIER DIAGNOSE BERICHT")
        print("="*60)
        
        # Bestimme wahrscheinliches Tier
        tier_indicators = []
        
        if 'estimated_tier' in self.results:
            tier_indicators.append(self.results['estimated_tier'])
        
        if 'model_access' in self.results:
            available_models = sum(self.results['model_access'].values())
            if available_models >= 3:
                tier_indicators.append('pay_as_you_go')
            elif available_models <= 1:
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
            print("   https://ai.google.dev/pricing")
        elif most_likely_tier == 'pay_as_you_go':
            print("💳 PAY-AS-YOU-GO TIER")
            print("   • Höhere Rate Limits")
            print("   • Vollständiger Modell-Zugang")
            print("   • Bessere Performance")
        else:
            print("❓ UNBEKANNT")
            print("   • Tier konnte nicht eindeutig bestimmt werden")
        
        # CLI-spezifische Empfehlungen
        print("\n" + "="*60)
        print("🛠️ CLI PROCESSING EMPFEHLUNGEN")
        print("="*60)
        
        if most_likely_tier == 'free':
            print("⚡ SOFORTIGE LÖSUNG - Verwende den --fast Modus:")
            print("   ./ki-cli.sh process test-bsi-dokument.txt --fast --verbose")
            print("\n🐌 Oder verwende längere Timeouts:")
            print("   ./ki-cli.sh process test-bsi-dokument.txt --verbose")
            print("   (kann sehr langsam sein wegen Rate Limits)")
        elif most_likely_tier == 'pay_as_you_go':
            print("✅ Normaler Modus sollte funktionieren:")
            print("   ./ki-cli.sh process test-bsi-dokument.txt --verbose")
        else:
            print("🔍 Teste beide Modi:")
            print("   ./ki-cli.sh process test-bsi-dokument.txt --fast    # Schnell")
            print("   ./ki-cli.sh process test-bsi-dokument.txt --verbose # Vollständig")
        
        # Speichere detaillierte Ergebnisse (K6: Output-Verzeichnis für generierte Dateien)
        with open('output/reports/gemini_tier_report.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Detaillierter Bericht gespeichert: output/reports/gemini_tier_report.json")
        print(f"⏰ Diagnose-Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return most_likely_tier

def main():
    print("🚀 Vereinfachter Gemini API Tier Checker")
    print("="*50)
    
    checker = SimpleGeminiChecker()
    
    # Führe alle Tests durch
    if not checker.test_basic_connectivity():
        print("\n❌ Grundlegende API-Verbindung fehlgeschlagen.")
        print("Prüfe API Key und Internetverbindung.")
        return
    
    checker.test_rate_limits()
    checker.test_model_access()
    
    # Generiere finalen Bericht
    tier = checker.generate_report()

if __name__ == "__main__":
    main() 