# Radio PrideSync - Raspberry Pi Zero 2 W FM Radio Ontvanger

Een professioneel radio ontvanger project met de SI4703 RDS FM radio tuner module voor Raspberry Pi Zero 2 W, inclusief audio opname functionaliteit.

## 📋 Overzicht

Dit project maakt een complete FM radio ontvanger die:
- FM radio stations kan ontvangen met RDS informatie
- Audio kan opnemen als MP3 bestanden op SD kaart
- Bediend kan worden via een eenvoudige interface
- Professioneel georganiseerd is voor eenvoudige uitbreiding

## 🛠️ Benodigde Hardware

### Hoofdcomponenten
- **Raspberry Pi Zero 2 W** (met GPIO headers)
- **SI4703 RDS FM Radio Tuner Module**
- **MicroSD kaart** (minimaal 16GB, Class 10 aanbevolen)
- **3.5mm audio jack** of **I2S audio HAT** (voor audio output)
- **Breadboard** of **PCB** voor prototyping
- **Jumper wires** (vrouwelijk-mannelijk en mannelijk-mannelijk)

### Optionele componenten
- **LCD display** (16x2 I2C) voor station informatie
- **Rotary encoder** voor volume en tuning
- **Push buttons** voor bediening
- **LED indicators** voor status
- **Externe antenne** voor betere ontvangst

## 🔧 Software Vereisten

### Raspberry Pi OS Setup
```bash
# Update systeem
sudo apt update && sudo apt upgrade -y

# Installeer benodigde pakketten
sudo apt install -y python3-pip python3-venv git i2c-tools
sudo apt install -y libasound2-dev portaudio19-dev libportaudio2
sudo apt install -y ffmpeg lame # Voor MP3 encoding
```

### Python Dependencies
```bash
# Maak virtual environment
python3 -m venv venv
source venv/bin/activate

# Installeer Python packages
pip install -r requirements.txt
```

## 📁 Project Structuur

```
Radio-PrideSync/
├── README.md                 # Dit bestand
├── requirements.txt          # Python dependencies
├── setup.sh                 # Automatische setup script
├── config/
│   ├── radio_config.json    # Radio configuratie
│   └── audio_config.json    # Audio instellingen
├── src/
│   ├── main.py              # Hoofdprogramma
│   ├── radio/
│   │   ├── __init__.py
│   │   ├── si4703.py        # SI4703 driver
│   │   └── rds_decoder.py   # RDS data decoder
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── recorder.py      # Audio opname
│   │   └── player.py        # Audio afspelen
│   └── utils/
│       ├── __init__.py
│       ├── logger.py        # Logging utilities
│       └── helpers.py       # Helper functies
├── hardware/
│   ├── schematics/
│   │   ├── wiring_diagram.png
│   │   ├── breadboard_layout.png
│   │   └── pcb_design.kicad_pro
│   └── datasheets/
│       ├── SI4703_datasheet.pdf
│       └── raspberry_pi_pinout.pdf
├── docs/
│   ├── installation.md      # Installatie handleiding
│   ├── usage.md            # Gebruiksaanwijzing
│   ├── troubleshooting.md  # Probleemoplossing
│   └── api_reference.md    # API documentatie
├── tests/
│   ├── test_radio.py       # Radio module tests
│   ├── test_audio.py       # Audio module tests
│   └── test_integration.py # Integratie tests
├── recordings/             # Opgenomen audio bestanden
├── logs/                   # Log bestanden
└── scripts/
    ├── start_radio.sh      # Start script
    ├── stop_radio.sh       # Stop script
    └── backup_recordings.sh # Backup script
```

## 🔌 Hardware Aansluiting

### SI4703 naar Raspberry Pi Zero 2 W

| SI4703 Pin | Raspberry Pi Pin | GPIO | Functie |
|------------|------------------|------|---------|
| VCC        | Pin 1 (3.3V)     | -    | Voeding |
| GND        | Pin 6 (GND)      | -    | Ground  |
| SDA        | Pin 3            | GPIO2| I2C Data|
| SCL        | Pin 5            | GPIO3| I2C Clock|
| RST        | Pin 11           | GPIO17| Reset  |
| GPIO2      | Pin 13           | GPIO27| Control|

**⚠️ Belangrijk:** Controleer altijd de pinout van je specifieke SI4703 module!

## 🚀 Snelle Start

1. **Clone het project:**
   ```bash
   git clone <repository-url>
   cd Radio-PrideSync
   ```

2. **Voer setup uit:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Start de radio:**
   ```bash
   ./scripts/start_radio.sh
   ```

## 📖 Gedetailleerde Documentatie

- [Installatie Handleiding](docs/installation.md)
- [Gebruiksaanwijzing](docs/usage.md)
- [Hardware Schema's](hardware/schematics/)
- [Probleemoplossing](docs/troubleshooting.md)

## 🎵 Functies

- ✅ FM radio ontvangst (87.5 - 108.0 MHz)
- ✅ RDS informatie (station naam, titel, artiest)
- ✅ Audio opname naar MP3
- ✅ Automatische bestandsnaamgeving
- ✅ Web interface voor bediening
- ✅ Logging en foutafhandeling
- ✅ Configureerbare instellingen

## 🤝 Bijdragen

Bijdragen zijn welkom! Zie [CONTRIBUTING.md](CONTRIBUTING.md) voor richtlijnen.

## 📄 Licentie

Dit project is gelicenseerd onder de MIT License - zie [LICENSE](LICENSE) bestand voor details.

## 🆘 Ondersteuning

Voor vragen of problemen, maak een issue aan in de GitHub repository.
