#!/usr/bin/env python3
"""
Test-Skript für den Gemini API Key
Überprüft, ob der API Key funktioniert und eine Verbindung zur Google Gemini API hergestellt werden kann.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import requests
import json

def list_available_models(api_key):
    """Liste alle verfügbaren Gemini-Modelle auf"""
    print("\n📋 Verfügbare Modelle abfragen...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            models = response.json()
            print("✅ Verfügbare Modelle:")
            for model in models.get('models', []):
                name = model.get('name', '').replace('models/', '')
                if 'generateContent' in model.get('supportedGenerationMethods', []):
                    print(f"   🔹 {name}")
            return models.get('models', [])
        else:
            print(f"❌ Fehler beim Abrufen der Modelle: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der Modelle: {e}")
        return []

def test_gemini_api():
    """Testet den Gemini API Key"""
    print("🔍 Überprüfe Gemini API Key...")
    print("=" * 50)
    
    # Lade .env Datei
    load_dotenv(project_root / ".env")
    
    # Überprüfe ob API Key gesetzt ist
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ FEHLER: GOOGLE_API_KEY nicht gefunden in .env Datei")
        print("💡 Bitte erstellen Sie eine .env Datei aus env.example und setzen Sie Ihren API Key")
        return False
    
    print(f"✅ API Key gefunden: {api_key[:10]}...{api_key[-4:]}")
    
    # Liste verfügbare Modelle auf
    available_models = list_available_models(api_key)
    
    # Teste mit verfügbaren Modellen
    test_models = [
        "gemini-1.5-flash",
        "gemini-1.5-pro", 
        "gemini-2.0-flash",
        "gemini-pro"  # Fallback für ältere APIs
    ]
    
    for model_name in test_models:
        print(f"\n🧪 Teste Modell: {model_name}")
        if test_model(api_key, model_name):
            return True
    
    print("\n❌ Keines der Testmodelle funktioniert")
    return False

def test_model(api_key, model_name):
    """Testet ein spezifisches Modell"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [{
            "parts": [{
                "text": "Sage einfach nur 'Hallo' auf deutsch."
            }]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Modell {model_name} funktioniert!")
            print(f"📝 Antwort: {result['candidates'][0]['content']['parts'][0]['text']}")
            return True
        else:
            print(f"❌ Modell {model_name} - Fehler: Status {response.status_code}")
            if response.status_code == 404:
                print(f"   💡 Modell nicht verfügbar oder deprecated")
            else:
                print(f"   📝 Fehlermeldung: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Verbindungsfehler: Keine Internetverbindung")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout: API-Anfrage dauerte zu lange")
        return False
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        return False

def test_langchain_gemini():
    """Testet die Gemini-Integration über LangChain"""
    print("\n🔗 Teste LangChain Gemini Integration...")
    print("=" * 50)
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from src.config.settings import settings
        
        # Teste mit aktuellen Modellen
        test_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]
        
        for model_name in test_models:
            print(f"🧪 Teste LangChain mit {model_name}...")
            try:
                model = ChatGoogleGenerativeAI(
                    google_api_key=settings.google_api_key,
                    model=model_name,
                    temperature=0.1
                )
                
                # Einfache Testanfrage
                response = model.invoke("Sage nur 'Test erfolgreich' auf deutsch.")
                print(f"✅ LangChain Test mit {model_name} erfolgreich!")
                print(f"📝 Antwort: {response.content}")
                return True
            except Exception as e:
                print(f"❌ {model_name} fehlgeschlagen: {e}")
                continue
        
        print("❌ Alle LangChain Tests fehlgeschlagen")
        return False
        
    except Exception as e:
        print(f"❌ LangChain Import/Setup fehlgeschlagen: {e}")
        return False

def check_env_file():
    """Überprüft die .env Datei"""
    print("\n📄 Überprüfe .env Datei...")
    print("=" * 50)
    
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print("❌ .env Datei nicht gefunden!")
        print("💡 Erstellen Sie eine .env Datei aus env.example:")
        print(f"   cp {project_root}/env.example {project_root}/.env")
        return False
    
    print("✅ .env Datei gefunden")
    
    # Lade und überprüfe Inhalt
    load_dotenv(env_file)
    
    required_keys = ["GOOGLE_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
    missing_keys = []
    
    for key in required_keys:
        value = os.getenv(key)
        if not value or value == f"your_{key.lower().replace('_', '-')}_here":
            missing_keys.append(key)
        else:
            print(f"✅ {key}: {value[:10]}...{value[-4:]}")
    
    if missing_keys:
        print(f"\n❌ Fehlende/ungültige API Keys: {', '.join(missing_keys)}")
        return False
    
    return True

def main():
    """Hauptfunktion"""
    print("🚀 Gemini API Key Test")
    print("=" * 50)
    
    # Überprüfe .env Datei
    if not check_env_file():
        return
    
    # Teste direkte API-Verbindung
    api_test = test_gemini_api()
    
    # Teste LangChain Integration
    langchain_test = test_langchain_gemini()
    
    print("\n📊 Zusammenfassung:")
    print("=" * 50)
    print(f"✅ .env Datei: OK")
    print(f"{'✅' if api_test else '❌'} Direkte API: {'OK' if api_test else 'FEHLER'}")
    print(f"{'✅' if langchain_test else '❌'} LangChain: {'OK' if langchain_test else 'FEHLER'}")
    
    if api_test and langchain_test:
        print("\n🎉 Alle Tests erfolgreich! Ihr Gemini API Key funktioniert.")
        print("\n💡 Empfehlung: Das System sollte jetzt funktionieren.")
        print("   Falls weiterhin Probleme auftreten, starten Sie das System neu:")
        print("   ./ki-restart.sh")
    else:
        print("\n⚠️  Einige Tests sind fehlgeschlagen.")
        if not api_test:
            print("💡 Direkte API-Probleme:")
            print("   - Überprüfen Sie Ihren API Key in der Google Cloud Console")
            print("   - Stellen Sie sicher, dass die Generative Language API aktiviert ist")
            print("   - Überprüfen Sie Ihr Abrechnungskonto")
        if not langchain_test:
            print("💡 LangChain-Probleme:")
            print("   - Aktualisieren Sie LangChain: pip install --upgrade langchain-google-genai")
            print("   - Starten Sie das System neu: ./ki-restart.sh")

if __name__ == "__main__":
    main() 