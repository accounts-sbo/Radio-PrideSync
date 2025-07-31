#!/bin/bash

# Radio PrideSync - Start Script
# Start de radio applicatie

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🎵 Radio PrideSync wordt gestart..."
echo "Project directory: $PROJECT_DIR"

# Ga naar project directory
cd "$PROJECT_DIR"

# Controleer of virtual environment bestaat
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment niet gevonden!"
    echo "Voer eerst setup.sh uit: ./setup.sh"
    exit 1
fi

# Activeer virtual environment
echo "🐍 Virtual environment wordt geactiveerd..."
source venv/bin/activate

# Controleer Python dependencies
echo "📦 Dependencies worden gecontroleerd..."
if ! python -c "import RPi.GPIO, smbus2, pyaudio" 2>/dev/null; then
    echo "❌ Niet alle dependencies zijn geïnstalleerd!"
    echo "Voer eerst setup.sh uit: ./setup.sh"
    exit 1
fi

# Controleer I2C
echo "🔌 I2C wordt gecontroleerd..."
if ! command -v i2cdetect &> /dev/null; then
    echo "⚠️  i2c-tools niet gevonden, I2C test wordt overgeslagen"
else
    echo "I2C devices:"
    sudo i2cdetect -y 1 || echo "⚠️  I2C scan gefaald"
fi

# Controleer GPIO permissions
echo "🔐 GPIO permissions worden gecontroleerd..."
if [ ! -w /dev/gpiomem ]; then
    echo "⚠️  Geen GPIO toegang, mogelijk sudo nodig"
fi

# Maak benodigde directories
mkdir -p logs recordings

# Start de applicatie
echo "🚀 Radio PrideSync wordt gestart..."
echo "Druk Ctrl+C om te stoppen"
echo "================================"

# Start met error handling
if python src/main.py; then
    echo "✅ Radio PrideSync succesvol afgesloten"
else
    echo "❌ Radio PrideSync afgesloten met fout (exit code: $?)"
    echo "Check logs/radio_pridesync_$(date +%Y%m%d).log voor details"
    exit 1
fi
