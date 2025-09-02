#!/bin/bash

# Enkel startscript för Mac/Linux

echo "🚀 Startar Rekommendationsmotor..."

# Kontrollera om Python finns
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 är inte installerat. Installera från python.org"
    exit 1
fi

# Kontrollera om venv finns, annars skapa
if [ ! -d "venv" ]; then
    echo "📦 Skapar virtuell miljö..."
    python3 -m venv venv
fi

# Aktivera venv
echo "🔧 Aktiverar virtuell miljö..."
source venv/bin/activate

# Installera/uppdatera beroenden
echo "📚 Installerar beroenden..."
pip install -r requirements.txt --quiet

# Starta appen
echo "✅ Startar Streamlit..."
echo "🌐 Öppna http://localhost:8501 i din webbläsare"
streamlit run Home.py
