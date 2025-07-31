#!/bin/bash
# Eenvoudige installatie voor radio script

echo "🎵 Installeren van eenvoudige radio..."
echo "====================================="

# Update systeem
echo "📦 Systeem updaten..."
sudo apt update

# Installeer alleen essentiële packages
echo "📦 Installeren van Python I2C libraries..."
sudo apt install -y python3-pip python3-smbus python3-rpi.gpio

# Installeer Python dependencies
echo "📦 Installeren van Python packages..."
pip3 install RPi.GPIO smbus2

# Maak script uitvoerbaar
chmod +x simple_radio.py

# Enable I2C
echo "🔧 I2C inschakelen..."
sudo raspi-config nonint do_i2c 0

echo ""
echo "✅ Installatie voltooid!"
echo ""
echo "🚀 Start de radio met:"
echo "   python3 simple_radio.py"
echo ""
echo "📋 Zorg ervoor dat je SI4703 module correct is aangesloten:"
echo "   - VCC naar 3.3V"
echo "   - GND naar GND"
echo "   - SDA naar GPIO 2 (pin 3)"
echo "   - SCL naar GPIO 3 (pin 5)"
echo "   - RST naar GPIO 18 (pin 12)"
echo "   - SDIO naar GPIO 2 (pin 3) - gedeeld met SDA"
echo ""
