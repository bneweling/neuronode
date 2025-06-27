#!/bin/bash

# =================================================================
# BSI Synthetic Data Import Script
# Importiert die synthetischen BSI-Daten in Neo4j und ChromaDB
# =================================================================

echo "🚀 BSI Synthetic Data Import"
echo "=================================="

# Change to ki-wissenssystem directory first
cd ki-wissenssystem

# Check if files exist
if [[ ! -f "BST1.json" ]]; then
    echo "❌ BST1.json not found in ki-wissenssystem directory"
    exit 1
fi

if [[ ! -f "BST2.json" ]]; then
    echo "❌ BST2.json not found in ki-wissenssystem directory"
    exit 1
fi

if [[ ! -f "BSTcypher.txt" ]]; then
    echo "❌ BSTcypher.txt not found in ki-wissenssystem directory"
    exit 1
fi

echo "✅ All required files found in ki-wissenssystem directory"
echo ""

# Check if virtual environment exists
if [[ -d "venv" ]]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️ No virtual environment found. Using system Python..."
fi

# Install requirements if needed
echo "📦 Checking dependencies..."
python3 -c "import neo4j, chromadb" 2>/dev/null
if [[ $? -ne 0 ]]; then
    echo "📦 Installing missing dependencies..."
    pip3 install -r requirements.txt
fi

# Run the import script
echo ""
echo "🗄️ Starting data import..."
python3 import_synthetic_data.py

# Check import success
if [[ $? -eq 0 ]]; then
    echo ""
    echo "🎉 Import completed successfully!"
    echo ""
    echo "📊 You can now check the data with:"
    echo "  cd ki-wissenssystem"
    echo "  ./ki-cli.sh stats"
    echo "  ./ki-cli.sh query 'Zeige mir BSI Controls'"
    echo ""
else
    echo ""
    echo "❌ Import failed. Check error messages above."
    exit 1
fi 