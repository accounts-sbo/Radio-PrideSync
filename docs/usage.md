# Radio PrideSync - Gebruiksaanwijzing

Deze handleiding legt uit hoe je Radio PrideSync gebruikt voor het ontvangen van FM radio en het opnemen van audio.

## 🚀 Radio Starten

### Basis Start
```bash
# Ga naar project directory
cd Radio-PrideSync

# Start de radio
./scripts/start_radio.sh
```

### Verwachte Output
```
🎵 Radio PrideSync wordt gestart...
Project directory: /home/pi/Radio-PrideSync
🐍 Virtual environment wordt geactiveerd...
📦 Dependencies worden gecontroleerd...
🔌 I2C wordt gecontroleerd...
I2C devices:
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: 10 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
🚀 Radio PrideSync wordt gestart...

📻 Radio Status:
   Frequentie: 100.0 MHz
   Volume: 8/15
----------------------------------------
Radio>
```

## 🎛️ Basis Bediening

### Commando Overzicht
```
f <freq>  - Stel frequentie in (bijv: f 100.5)
v <vol>   - Stel volume in (0-15)
s         - Zoek naar volgende station
r         - Start/stop opname
i         - Toon radio informatie
q         - Afsluiten
```

### Frequentie Instellen
```bash
# Stel frequentie in op 100.5 MHz
Radio> f 100.5

# Stel frequentie in op 95.8 MHz
Radio> f 95.8

# Frequentie bereik: 87.5 - 108.0 MHz
```

### Volume Aanpassen
```bash
# Stel volume in op 10 (van 15)
Radio> v 10

# Minimum volume (stil)
Radio> v 0

# Maximum volume
Radio> v 15
```

### Station Zoeken
```bash
# Zoek naar volgende station (omhoog)
Radio> s

# Output:
Zoeken naar station...
Station gevonden!

📻 Radio Status:
   Frequentie: 101.2 MHz
   Volume: 10/15
   Station: Radio 1
```

## 🎵 Audio Opname

### Opname Starten
```bash
# Start opname van huidige station
Radio> r

# Output:
Opname gestart: radio_recording_20241129_143052_101.2MHz.mp3

📻 Radio Status:
   Frequentie: 101.2 MHz
   Volume: 10/15
   Station: Radio 1
   🔴 OPNAME ACTIEF
```

### Opname Stoppen
```bash
# Stop huidige opname
Radio> r

# Output:
Opname gestopt: radio_recording_20241129_143052_101.2MHz.mp3
```

### Opname Bestanden
```bash
# Opnames worden opgeslagen in:
recordings/

# Bestandsnaam formaat:
radio_recording_[DATUM]_[TIJD]_[FREQUENTIE]MHz.mp3

# Voorbeeld:
radio_recording_20241129_143052_101.2MHz.mp3
```

## 📊 Radio Informatie

### Status Weergave
```bash
# Toon uitgebreide informatie
Radio> i

# Output:
📻 Radio Status:
   Frequentie: 101.2 MHz
   Volume: 10/15
   Station: Radio 1
   Info: Nu speelt: Artist - Song Title
   Signaal: ████████░░ (8/10)
   RDS: Actief
----------------------------------------
```

### RDS Informatie
RDS (Radio Data System) toont extra informatie:
- **Station naam**: Officiële naam van radiostation
- **Radio tekst**: Huidige song/programma informatie
- **Programma type**: Muziek, nieuws, sport, etc.

## 🔧 Geavanceerde Functies

### Configuratie Aanpassen
```bash
# Radio instellingen
nano config/radio_config.json

# Audio instellingen  
nano config/audio_config.json
```

### Belangrijke Instellingen
```json
// radio_config.json
{
    "default_frequency": 100.0,    // Startfrequentie
    "volume": {
        "default": 8               // Standaard volume
    },
    "seek_threshold": 20           // Gevoeligheid station zoeken
}

// audio_config.json
{
    "recording": {
        "bitrate": 128,            // MP3 kwaliteit
        "sample_rate": 44100       // Audio sample rate
    }
}
```

## 📁 Bestandsbeheer

### Opnames Bekijken
```bash
# Lijst van opnames
ls -la recordings/

# Grootte van opnames
du -h recordings/

# Speel opname af (met mpg123)
mpg123 recordings/radio_recording_*.mp3
```

### Backup Maken
```bash
# Automatische backup van opnames
./scripts/backup_recordings.sh

# Output:
💾 Radio PrideSync Backup wordt gestart...
📁 5 bestanden gevonden voor backup
🗜️  Gecomprimeerde backup wordt gemaakt...
✅ Backup gemaakt: backups/recordings_backup_20241129_143052.tar.gz
📊 Backup grootte: 45M
```

### Oude Bestanden Opruimen
```bash
# Handmatig oude bestanden verwijderen
find recordings/ -name "*.mp3" -mtime +7 -delete

# Of gebruik backup script (ruimt automatisch op)
./scripts/backup_recordings.sh
```

## 🔍 Monitoring en Logs

### Log Bestanden
```bash
# Bekijk huidige logs
tail -f logs/radio_pridesync_$(date +%Y%m%d).log

# Zoek naar fouten
grep ERROR logs/radio_pridesync_*.log

# Zoek naar specifieke events
grep "Station gevonden" logs/radio_pridesync_*.log
```

### Systeem Status
```bash
# Controleer I2C verbinding
sudo i2cdetect -y 1

# Controleer audio devices
aplay -l

# Controleer schijfruimte
df -h
```

## 🚨 Probleemoplossing

### Veelvoorkomende Problemen

#### Radio start niet
```bash
# Controleer I2C verbinding
sudo i2cdetect -y 1

# Controleer logs
tail logs/radio_pridesync_*.log

# Herstart I2C
sudo systemctl restart i2c
```

#### Geen geluid
```bash
# Test audio output
speaker-test -t sine -f 1000 -l 1

# Controleer volume
alsamixer

# Controleer audio configuratie
aplay -l
```

#### Slechte ontvangst
```bash
# Controleer antenne verbinding
# Probeer andere locatie
# Controleer voor interferentie (WiFi, Bluetooth)

# Pas seek threshold aan
nano config/radio_config.json
# Verhoog "seek_threshold" waarde
```

#### Opname werkt niet
```bash
# Controleer audio input devices
python3 -c "
import pyaudio
audio = pyaudio.PyAudio()
for i in range(audio.get_device_count()):
    info = audio.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'{i}: {info[\"name\"]}')
audio.terminate()
"

# Test audio input
arecord -d 5 test.wav
aplay test.wav
```

## 🔄 Automatische Start

### Systemd Service
```bash
# Installeer service
sudo cp radio-pridesync.service /etc/systemd/system/
sudo systemctl enable radio-pridesync.service

# Start service
sudo systemctl start radio-pridesync.service

# Controleer status
sudo systemctl status radio-pridesync.service

# Stop service
sudo systemctl stop radio-pridesync.service
```

### Boot Script
```bash
# Voeg toe aan crontab voor autostart
crontab -e

# Voeg deze regel toe:
@reboot /home/pi/Radio-PrideSync/scripts/start_radio.sh
```

## 📱 Remote Toegang

### SSH Bediening
```bash
# SSH naar Raspberry Pi
ssh pi@[IP_ADRES]

# Start radio in screen sessie
screen -S radio
./scripts/start_radio.sh

# Detach van screen: Ctrl+A, D
# Reattach: screen -r radio
```

### Web Interface (toekomstige functie)
```
Geplande functionaliteit:
- Web browser interface
- Remote bediening via smartphone
- Live audio streaming
- Opname scheduling
```

## 💡 Tips en Trucs

### Betere Ontvangst
```
1. Gebruik externe FM antenne
2. Plaats antenne hoog en vrij van obstakels
3. Vermijd interferentie van WiFi/Bluetooth
4. Test verschillende locaties
5. Gebruik geaarde antenne voor betere kwaliteit
```

### Audio Kwaliteit
```
1. Gebruik USB audio adapter voor opnames
2. Verhoog bitrate in config (192 of 320 kbps)
3. Controleer audio levels (niet te hoog/laag)
4. Gebruik goede audio kabels
5. Minimaliseer achtergrondgeluid
```

### Prestaties
```
1. Gebruik snelle SD kaart (Class 10+)
2. Monitor schijfruimte regelmatig
3. Maak regelmatig backups
4. Ruim oude logs op
5. Herstart systeem wekelijks
```

## 📞 Ondersteuning

Voor hulp en vragen:
- Controleer [troubleshooting.md](troubleshooting.md)
- Bekijk GitHub issues
- Raadpleeg log bestanden
- Test hardware verbindingen

Veel plezier met je Radio PrideSync! 🎵
