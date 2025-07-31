# Radio PrideSync - Installatie Handleiding

Deze handleiding leidt je stap voor stap door de installatie van Radio PrideSync op je Raspberry Pi Zero 2 W.

## 📋 Vereisten

### Hardware
- **Raspberry Pi Zero 2 W** met GPIO headers
- **SI4703 RDS FM Radio Tuner Module**
- **MicroSD kaart** (minimaal 16GB, Class 10 aanbevolen)
- **Jumper wires** voor verbindingen
- **Breadboard** voor prototyping
- **3.5mm audio kabel** of **USB audio adapter**

### Software
- **Raspberry Pi OS** (Lite of Desktop versie)
- **SSH toegang** (aanbevolen voor remote installatie)

## 🔧 Stap 1: Raspberry Pi OS Installatie

### 1.1 Download en Flash Raspberry Pi OS
```bash
# Download Raspberry Pi Imager
# https://www.raspberrypi.org/software/

# Flash naar SD kaart met deze instellingen:
# - SSH inschakelen
# - WiFi configureren
# - Gebruiker: pi
# - Wachtwoord: [jouw wachtwoord]
```

### 1.2 Eerste Boot en Update
```bash
# SSH naar je Raspberry Pi
ssh pi@[IP_ADRES]

# Update systeem
sudo apt update && sudo apt upgrade -y

# Herstart
sudo reboot
```

## 🔌 Stap 2: Hardware Aansluiting

### 2.1 SI4703 Module Aansluiting

**⚠️ BELANGRIJK: Schakel Raspberry Pi UIT voordat je verbindingen maakt!**

| SI4703 Pin | Raspberry Pi Pin | GPIO | Functie | Kleur Wire |
|------------|------------------|------|---------|------------|
| VCC        | Pin 1 (3.3V)     | -    | Voeding | Rood       |
| GND        | Pin 6 (GND)      | -    | Ground  | Zwart      |
| SDA        | Pin 3            | GPIO2| I2C Data| Blauw      |
| SCL        | Pin 5            | GPIO3| I2C Clock| Geel      |
| RST        | Pin 11           | GPIO17| Reset  | Groen      |
| GPIO2      | Pin 13           | GPIO27| Control| Wit        |

### 2.2 Audio Aansluiting
```
Optie 1: 3.5mm Audio Jack
- Sluit audio kabel aan op Raspberry Pi audio uitgang
- Verbind met versterker of koptelefoon

Optie 2: USB Audio Adapter (aanbevolen voor opname)
- Sluit USB audio adapter aan
- Biedt betere audio kwaliteit voor opnames
```

### 2.3 Antenne Aansluiting
```
- Sluit antenne aan op ANT pin van SI4703
- Voor betere ontvangst: gebruik externe FM antenne
- Tijdelijk: gebruik jumper wire als antenne (30cm lang)
```

## 🚀 Stap 3: Software Installatie

### 3.1 Project Download
```bash
# Clone het project
git clone https://github.com/jouw-username/Radio-PrideSync.git
cd Radio-PrideSync

# Of download en unzip handmatig
wget https://github.com/jouw-username/Radio-PrideSync/archive/main.zip
unzip main.zip
cd Radio-PrideSync-main
```

### 3.2 Automatische Setup
```bash
# Maak setup script uitvoerbaar
chmod +x setup.sh

# Voer setup uit
./setup.sh

# Volg de instructies op het scherm
```

### 3.3 Handmatige Setup (als automatisch faalt)
```bash
# Update systeem
sudo apt update && sudo apt upgrade -y

# Installeer systeem dependencies
sudo apt install -y python3-pip python3-venv python3-dev git i2c-tools
sudo apt install -y libasound2-dev portaudio19-dev libportaudio2
sudo apt install -y ffmpeg lame alsa-utils

# Schakel I2C in
sudo raspi-config nonint do_i2c 0

# Maak Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Installeer Python packages
pip install --upgrade pip
pip install -r requirements.txt
```

## 🔍 Stap 4: Hardware Test

### 4.1 I2C Test
```bash
# Test I2C verbinding
sudo i2cdetect -y 1

# Verwachte output: SI4703 op adres 0x10
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# 10: 10 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# ...
```

### 4.2 GPIO Test
```bash
# Test GPIO toegang
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.HIGH)
print('GPIO test succesvol')
GPIO.cleanup()
"
```

### 4.3 Audio Test
```bash
# Test audio devices
python3 -c "
import pyaudio
audio = pyaudio.PyAudio()
print(f'Audio devices: {audio.get_device_count()}')
for i in range(audio.get_device_count()):
    info = audio.get_device_info_by_index(i)
    print(f'{i}: {info[\"name\"]} (in:{info[\"maxInputChannels\"]}, out:{info[\"maxOutputChannels\"]})')
audio.terminate()
"
```

## 🎵 Stap 5: Eerste Test

### 5.1 Start Radio
```bash
# Start de radio applicatie
./scripts/start_radio.sh

# Je zou dit moeten zien:
# 🎵 Radio PrideSync wordt gestart...
# 📦 Dependencies worden gecontroleerd...
# 🔌 I2C wordt gecontroleerd...
# 🚀 Radio PrideSync wordt gestart...
```

### 5.2 Test Commando's
```bash
# In de radio interface:
i          # Toon radio informatie
f 100.5    # Stel frequentie in op 100.5 MHz
v 10       # Stel volume in op 10
s          # Zoek naar station
r          # Start/stop opname
q          # Afsluiten
```

## 🔧 Stap 6: Configuratie

### 6.1 Radio Instellingen
```bash
# Bewerk radio configuratie
nano config/radio_config.json

# Belangrijke instellingen:
# - default_frequency: Standaard frequentie
# - volume.default: Standaard volume
# - seek_threshold: Gevoeligheid voor station zoeken
```

### 6.2 Audio Instellingen
```bash
# Bewerk audio configuratie
nano config/audio_config.json

# Belangrijke instellingen:
# - recording.bitrate: MP3 bitrate (128 aanbevolen)
# - recording.sample_rate: Sample rate (44100 standaard)
# - output_directory: Waar opnames worden opgeslagen
```

## 🚨 Probleemoplossing

### I2C Problemen
```bash
# Controleer I2C configuratie
sudo raspi-config
# -> Interface Options -> I2C -> Enable

# Controleer I2C modules
lsmod | grep i2c

# Herstart I2C service
sudo systemctl restart i2c
```

### Audio Problemen
```bash
# Controleer ALSA configuratie
aplay -l

# Test audio output
speaker-test -t sine -f 1000 -l 1

# Controleer PulseAudio
pulseaudio --check -v
```

### GPIO Problemen
```bash
# Controleer GPIO groep
groups $USER

# Voeg gebruiker toe aan gpio groep
sudo usermod -a -G gpio $USER

# Herstart sessie
sudo reboot
```

### Python Problemen
```bash
# Controleer virtual environment
which python
pip list

# Herinstalleer dependencies
pip install --force-reinstall -r requirements.txt
```

## 🔄 Automatische Start

### Systemd Service (optioneel)
```bash
# Kopieer service bestand
sudo cp radio-pridesync.service /etc/systemd/system/

# Pas pad aan in service bestand
sudo nano /etc/systemd/system/radio-pridesync.service

# Enable service
sudo systemctl enable radio-pridesync.service
sudo systemctl start radio-pridesync.service

# Controleer status
sudo systemctl status radio-pridesync.service
```

## ✅ Verificatie

Als alles correct is geïnstalleerd, zou je het volgende moeten kunnen:

1. ✅ I2C detecteert SI4703 op adres 0x10
2. ✅ Radio start zonder fouten
3. ✅ Frequentie kan worden ingesteld
4. ✅ Volume kan worden aangepast
5. ✅ Stations kunnen worden gevonden met seek
6. ✅ Audio opname werkt en slaat MP3 bestanden op
7. ✅ RDS informatie wordt getoond (als beschikbaar)

## 📞 Hulp Nodig?

- Controleer [troubleshooting.md](troubleshooting.md) voor veelvoorkomende problemen
- Bekijk log bestanden in `logs/` directory
- Maak een issue aan op GitHub met:
  - Raspberry Pi model en OS versie
  - Foutmeldingen uit logs
  - Output van `sudo i2cdetect -y 1`
  - Hardware setup foto's

## 🎉 Volgende Stappen

Na succesvolle installatie:
- Lees [usage.md](usage.md) voor gebruiksaanwijzing
- Bekijk [api_reference.md](api_reference.md) voor uitbreidingen
- Experimenteer met verschillende antennes voor betere ontvangst
