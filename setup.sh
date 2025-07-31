#!/bin/bash

# Radio PrideSync - Automatische Setup Script
# Voor Raspberry Pi Zero 2 W met SI4703 FM Radio Module

set -e  # Stop bij eerste fout

echo "🎵 Radio PrideSync Setup wordt gestart..."
echo "========================================"

# Controleer of we op Raspberry Pi draaien
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Waarschuwing: Dit script is ontworpen voor Raspberry Pi"
    read -p "Wil je toch doorgaan? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update systeem
echo "📦 Systeem wordt bijgewerkt..."
sudo apt update && sudo apt upgrade -y

# Installeer systeem dependencies
echo "🔧 Installeren van systeem pakketten..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    i2c-tools \
    libasound2-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    ffmpeg \
    lame \
    alsa-utils \
    pulseaudio

# Schakel I2C in
echo "🔌 I2C wordt ingeschakeld..."
sudo raspi-config nonint do_i2c 0

# Maak virtual environment
echo "🐍 Python virtual environment wordt aangemaakt..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activeer virtual environment en installeer Python packages
echo "📚 Python dependencies worden geïnstalleerd..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Maak configuratie bestanden
echo "⚙️  Configuratie bestanden worden aangemaakt..."

# Radio configuratie
cat > config/radio_config.json << 'EOF'
{
    "frequency_range": {
        "min": 87.5,
        "max": 108.0,
        "step": 0.1
    },
    "default_frequency": 100.0,
    "volume": {
        "min": 0,
        "max": 15,
        "default": 8
    },
    "rds_enabled": true,
    "seek_threshold": 20,
    "i2c_address": "0x10",
    "gpio_pins": {
        "reset": 17,
        "gpio2": 27
    }
}
EOF

# Audio configuratie
cat > config/audio_config.json << 'EOF'
{
    "recording": {
        "format": "mp3",
        "bitrate": 128,
        "sample_rate": 44100,
        "channels": 2,
        "output_directory": "recordings"
    },
    "playback": {
        "device": "default",
        "buffer_size": 1024
    },
    "file_naming": {
        "pattern": "radio_recording_{timestamp}_{frequency}MHz.mp3",
        "timestamp_format": "%Y%m%d_%H%M%S"
    }
}
EOF

# Maak scripts uitvoerbaar
echo "🔐 Scripts worden uitvoerbaar gemaakt..."
chmod +x scripts/*.sh

# Controleer I2C
echo "🔍 I2C configuratie wordt gecontroleerd..."
if command -v i2cdetect &> /dev/null; then
    echo "I2C tools zijn geïnstalleerd. Test met: sudo i2cdetect -y 1"
else
    echo "⚠️  I2C tools niet gevonden!"
fi

# Maak log directory
mkdir -p logs

# Maak systemd service (optioneel)
echo "🚀 Systemd service wordt voorbereid..."
cat > radio-pridesync.service << 'EOF'
[Unit]
Description=Radio PrideSync FM Radio Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Radio-PrideSync
Environment=PATH=/home/pi/Radio-PrideSync/venv/bin
ExecStart=/home/pi/Radio-PrideSync/venv/bin/python src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Setup voltooid!"
echo ""
echo "📋 Volgende stappen:"
echo "1. Sluit de SI4703 module aan volgens het schema in hardware/schematics/"
echo "2. Test de I2C verbinding: sudo i2cdetect -y 1"
echo "3. Start de radio: ./scripts/start_radio.sh"
echo "4. Optioneel: installeer systemd service: sudo cp radio-pridesync.service /etc/systemd/system/"
echo ""
echo "📖 Lees docs/installation.md voor gedetailleerde instructies"
echo "🎵 Veel plezier met je radio project!"
