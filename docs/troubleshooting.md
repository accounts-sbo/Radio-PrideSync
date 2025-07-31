# Radio PrideSync - Probleemoplossing

Deze gids helpt je bij het oplossen van veelvoorkomende problemen met Radio PrideSync.

## 🔍 Diagnose Stappen

### Stap 1: Basis Controles
```bash
# Controleer of alle bestanden aanwezig zijn
ls -la Radio-PrideSync/

# Controleer Python virtual environment
source venv/bin/activate
python --version

# Controleer I2C
sudo i2cdetect -y 1

# Controleer logs
tail -20 logs/radio_pridesync_$(date +%Y%m%d).log
```

## 🚨 Hardware Problemen

### SI4703 Niet Gedetecteerd

**Symptomen:**
- `i2cdetect -y 1` toont geen device op 0x10
- Foutmelding: "SI4703 chip niet gevonden"

**Oplossingen:**
```bash
# 1. Controleer I2C configuratie
sudo raspi-config
# -> Interface Options -> I2C -> Enable

# 2. Controleer I2C modules
lsmod | grep i2c
# Verwacht: i2c_bcm2835

# 3. Herstart I2C service
sudo systemctl restart i2c

# 4. Controleer verbindingen
# VCC -> 3.3V (NIET 5V!)
# GND -> GND
# SDA -> GPIO2/Pin3
# SCL -> GPIO3/Pin5

# 5. Test met multimeter
# Meet spanning op VCC pin (moet 3.3V zijn)
# Controleer continuïteit van alle verbindingen
```

### GPIO Toegang Problemen

**Symptomen:**
- Foutmelding: "Permission denied" bij GPIO toegang
- "RuntimeError: No access to /dev/mem"

**Oplossingen:**
```bash
# 1. Voeg gebruiker toe aan gpio groep
sudo usermod -a -G gpio $USER

# 2. Herstart sessie
sudo reboot

# 3. Controleer groepen
groups $USER
# Moet 'gpio' bevatten

# 4. Alternatief: run met sudo (niet aanbevolen)
sudo python src/main.py
```

### Slechte Radio Ontvangst

**Symptomen:**
- Geen stations gevonden met seek
- Veel ruis/static
- Zwak signaal

**Oplossingen:**
```bash
# 1. Controleer antenne verbinding
# Zorg dat antenne goed aangesloten is op ANT pin

# 2. Probeer externe antenne
# Gebruik telescopische FM antenne
# Plaats antenne hoog en vrij van obstakels

# 3. Vermijd interferentie
# Zet WiFi/Bluetooth uit voor test
# Verplaats weg van computers/routers

# 4. Pas seek threshold aan
nano config/radio_config.json
# Verlaag "seek_threshold" van 20 naar 10

# 5. Test handmatige frequentie
# Probeer bekende lokale stations
f 100.5  # Vervang met lokale frequentie
```

## 🔊 Audio Problemen

### Geen Geluid

**Symptomen:**
- Radio lijkt te werken maar geen audio
- Volume instellingen hebben geen effect

**Oplossingen:**
```bash
# 1. Test audio output
speaker-test -t sine -f 1000 -l 1

# 2. Controleer audio devices
aplay -l

# 3. Controleer ALSA mixer
alsamixer
# Zet volume omhoog, unmute kanalen

# 4. Test met andere audio
aplay /usr/share/sounds/alsa/Front_Left.wav

# 5. Controleer audio routing
# Voor 3.5mm jack:
sudo raspi-config
# -> Advanced Options -> Audio -> Force 3.5mm jack

# 6. Herstart audio service
sudo systemctl restart alsa-state
```

### Audio Opname Werkt Niet

**Symptomen:**
- Opname commando faalt
- Geen MP3 bestanden aangemaakt
- Foutmelding over audio input

**Oplossingen:**
```bash
# 1. Controleer audio input devices
python3 -c "
import pyaudio
audio = pyaudio.PyAudio()
print('Audio input devices:')
for i in range(audio.get_device_count()):
    info = audio.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'{i}: {info[\"name\"]} (channels: {info[\"maxInputChannels\"]})')
audio.terminate()
"

# 2. Test audio input
arecord -d 5 -f cd test.wav
aplay test.wav

# 3. Controleer USB audio adapter
lsusb
# Zoek naar audio device

# 4. Installeer extra audio drivers
sudo apt install pulseaudio pulseaudio-utils

# 5. Configureer audio input in config
nano config/audio_config.json
# Pas device index aan indien nodig
```

## 🐍 Software Problemen

### Python Import Fouten

**Symptomen:**
- "ModuleNotFoundError: No module named 'RPi'"
- "ImportError: No module named 'smbus2'"

**Oplossingen:**
```bash
# 1. Activeer virtual environment
source venv/bin/activate

# 2. Controleer geïnstalleerde packages
pip list

# 3. Herinstalleer requirements
pip install --force-reinstall -r requirements.txt

# 4. Installeer specifieke packages
pip install RPi.GPIO smbus2 pyaudio

# 5. Controleer Python versie
python --version
# Moet Python 3.7+ zijn
```

### Configuratie Fouten

**Symptomen:**
- "FileNotFoundError: config/radio_config.json"
- "JSONDecodeError: Expecting value"

**Oplossingen:**
```bash
# 1. Controleer config bestanden
ls -la config/

# 2. Valideer JSON syntax
python -m json.tool config/radio_config.json
python -m json.tool config/audio_config.json

# 3. Herstel config bestanden
./setup.sh
# Of handmatig kopiëren van backup

# 4. Controleer permissions
chmod 644 config/*.json
```

### Memory/Performance Problemen

**Symptomen:**
- Systeem wordt traag
- "MemoryError" bij opname
- Audio dropouts

**Oplossingen:**
```bash
# 1. Controleer geheugen gebruik
free -h
htop

# 2. Controleer schijfruimte
df -h

# 3. Ruim oude bestanden op
./scripts/backup_recordings.sh

# 4. Verhoog swap (indien nodig)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# 5. Optimaliseer audio buffer
nano config/audio_config.json
# Verhoog buffer_size
```

## 🔧 Systeem Problemen

### I2C Bus Problemen

**Symptomen:**
- "IOError: [Errno 2] No such file or directory: '/dev/i2c-1'"
- I2C communicatie faalt

**Oplossingen:**
```bash
# 1. Controleer I2C modules
sudo modprobe i2c-dev
sudo modprobe i2c-bcm2835

# 2. Voeg modules toe aan boot
echo 'i2c-dev' | sudo tee -a /etc/modules
echo 'i2c-bcm2835' | sudo tee -a /etc/modules

# 3. Controleer device tree
ls /dev/i2c*
# Moet /dev/i2c-1 tonen

# 4. Herstart systeem
sudo reboot
```

### Permission Problemen

**Symptomen:**
- "Permission denied" fouten
- Kan bestanden niet schrijven

**Oplossingen:**
```bash
# 1. Controleer eigenaarschap
ls -la Radio-PrideSync/
sudo chown -R $USER:$USER Radio-PrideSync/

# 2. Controleer directory permissions
chmod 755 Radio-PrideSync/
chmod 755 recordings/ logs/

# 3. Controleer script permissions
chmod +x scripts/*.sh
chmod +x setup.sh
```

## 📊 Diagnostische Tools

### Hardware Test Script
```bash
# Maak test script
cat > test_hardware.py << 'EOF'
#!/usr/bin/env python3
import sys
try:
    import RPi.GPIO as GPIO
    print("✅ RPi.GPIO geïmporteerd")
except ImportError:
    print("❌ RPi.GPIO niet beschikbaar")

try:
    from smbus2 import SMBus
    bus = SMBus(1)
    devices = []
    for addr in range(0x03, 0x78):
        try:
            bus.read_byte(addr)
            devices.append(hex(addr))
        except:
            pass
    bus.close()
    print(f"✅ I2C devices gevonden: {devices}")
except Exception as e:
    print(f"❌ I2C test gefaald: {e}")

try:
    import pyaudio
    audio = pyaudio.PyAudio()
    device_count = audio.get_device_count()
    print(f"✅ PyAudio: {device_count} audio devices")
    audio.terminate()
except Exception as e:
    print(f"❌ PyAudio test gefaald: {e}")
EOF

python3 test_hardware.py
```

### Log Analyse
```bash
# Zoek naar fouten in logs
grep -i error logs/radio_pridesync_*.log

# Zoek naar warnings
grep -i warning logs/radio_pridesync_*.log

# Toon laatste 50 regels
tail -50 logs/radio_pridesync_$(date +%Y%m%d).log

# Real-time log monitoring
tail -f logs/radio_pridesync_$(date +%Y%m%d).log
```

### Systeem Info Script
```bash
# Systeem informatie verzamelen
cat > system_info.sh << 'EOF'
#!/bin/bash
echo "=== Systeem Informatie ==="
uname -a
cat /etc/os-release | grep PRETTY_NAME

echo -e "\n=== Hardware ==="
cat /proc/cpuinfo | grep Model
vcgencmd measure_temp

echo -e "\n=== I2C ==="
sudo i2cdetect -y 1

echo -e "\n=== Audio ==="
aplay -l

echo -e "\n=== GPIO ==="
gpio readall 2>/dev/null || echo "gpio command niet beschikbaar"

echo -e "\n=== Schijfruimte ==="
df -h

echo -e "\n=== Geheugen ==="
free -h
EOF

chmod +x system_info.sh
./system_info.sh
```

## 🆘 Hulp Krijgen

### Informatie Verzamelen
Voor effectieve hulp, verzamel deze informatie:

```bash
# 1. Systeem info
./system_info.sh > debug_info.txt

# 2. Logs
tail -100 logs/radio_pridesync_*.log >> debug_info.txt

# 3. Configuratie
cat config/radio_config.json >> debug_info.txt
cat config/audio_config.json >> debug_info.txt

# 4. Hardware test
python3 test_hardware.py >> debug_info.txt
```

### GitHub Issue Maken
Wanneer je een issue maakt, voeg toe:
- Raspberry Pi model en OS versie
- Volledige foutmelding
- Output van `system_info.sh`
- Foto van hardware opstelling
- Stappen om probleem te reproduceren

### Community Hulp
- Raspberry Pi forums
- Reddit r/raspberry_pi
- Electronics Stack Exchange
- Local maker spaces

## 🔄 Reset Procedures

### Soft Reset
```bash
# Stop radio
./scripts/stop_radio.sh

# Herstart I2C
sudo systemctl restart i2c

# Start radio
./scripts/start_radio.sh
```

### Hard Reset
```bash
# Volledige herinstallatie
rm -rf venv/
./setup.sh
```

### Factory Reset
```bash
# Backup belangrijke bestanden
cp -r recordings/ recordings_backup/

# Reset naar originele staat
git checkout .
./setup.sh
```

Onthoud: De meeste problemen zijn hardware gerelateerd. Controleer altijd eerst je verbindingen! 🔌
