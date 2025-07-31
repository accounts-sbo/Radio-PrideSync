# Radio PrideSync - Aansluitschema

## 🔌 SI4703 naar Raspberry Pi Zero 2 W

### Pinout Overzicht

```
Raspberry Pi Zero 2 W                    SI4703 FM Radio Module
┌─────────────────────┐                 ┌─────────────────────┐
│  1 [3.3V]     [5V] 2│                 │ VCC              ANT│ <- Antenne
│  3 [SDA]     [5V] 4 │ <────────────── │ SDA              GND│
│  5 [SCL]     [GND] 6│ <────────────── │ SCL              RST│
│  7 [GPIO4] [TXD] 8  │                 │ GND            GPIO2│
│  9 [GND]   [RXD] 10 │                 └─────────────────────┘
│ 11 [GPIO17][GPIO18]12│ <──────────────────────────────────┘
│ 13 [GPIO27][GND] 14 │ <──────────────────────────────────┘
│ 15 [GPIO22][GPIO23]16│
│ 17 [3.3V] [GPIO24]18│
│ 19 [MOSI] [GND] 20  │
│ 21 [MISO] [GPIO25]22│
│ 23 [SCLK] [CE0] 24  │
│ 25 [GND]  [CE1] 26  │
│ 27 [ID_SD][ID_SC]28 │
│ 29 [GPIO5] [GND] 30 │
│ 31 [GPIO6][GPIO12]32│
│ 33 [GPIO13][GND] 34 │
│ 35 [GPIO19][GPIO16]36│
│ 37 [GPIO26][GPIO20]38│
│ 39 [GND]  [GPIO21]40│
└─────────────────────┘
```

### Verbindingen Tabel

| Verbinding | Raspberry Pi | SI4703 | Wire Kleur | Functie |
|------------|--------------|--------|------------|---------|
| Voeding    | Pin 1 (3.3V) | VCC    | Rood       | 3.3V voeding |
| Ground     | Pin 6 (GND)  | GND    | Zwart      | Ground referentie |
| I2C Data   | Pin 3 (GPIO2)| SDA    | Blauw      | I2C data lijn |
| I2C Clock  | Pin 5 (GPIO3)| SCL    | Geel       | I2C clock lijn |
| Reset      | Pin 11 (GPIO17)| RST  | Groen      | Reset signaal |
| Control    | Pin 13 (GPIO27)| GPIO2| Wit        | Mode control |

## 🔧 Breadboard Layout

```
Breadboard Layout (bovenaanzicht):
═══════════════════════════════════════════════════════════

    a  b  c  d  e     f  g  h  i  j
 1  ●  ●  ●  ●  ●  |  ●  ●  ●  ●  ●
 2  ●  ●  ●  ●  ●  |  ●  ●  ●  ●  ●
 3  ●  ●  ●  ●  ●  |  ●  ●  ●  ●  ●
 4  ●  ●  ●  ●  ●  |  ●  ●  ●  ●  ●
 5  ●  ●  ●  ●  ●  |  ●  ●  ●  ●  ●
    
    SI4703 Module (rij 5-8):
 5  -  -  -  -  -  |  V  S  S  G  -    VCC SDA SCL GND
 6  -  -  -  -  -  |  C  D  C  N  -
 7  -  -  -  -  -  |  C  A  L  D  -
 8  -  -  -  -  -  |  -  -  -  -  -
    
    Power Rails:
 +  ●──●──●──●──●──●──●──●──●──●──●    3.3V (rood)
 -  ●──●──●──●──●──●──●──●──●──●──●    GND (zwart)

    Verbindingen naar Raspberry Pi:
    f5 (VCC)   -> 3.3V rail (rood wire)
    g5 (SDA)   -> GPIO2/Pin3 (blauw wire)
    h5 (SCL)   -> GPIO3/Pin5 (geel wire)
    i5 (GND)   -> GND rail (zwart wire)
    
    Extra verbindingen:
    RST pin    -> GPIO17/Pin11 (groen wire)
    GPIO2 pin  -> GPIO27/Pin13 (wit wire)

═══════════════════════════════════════════════════════════
```

## 📐 Fysieke Opstelling

### Stap 1: Voorbereiding
```
1. Schakel Raspberry Pi UIT
2. Leg alle benodigde materialen klaar:
   - Breadboard
   - SI4703 module
   - 6x jumper wires (verschillende kleuren)
   - Raspberry Pi Zero 2 W
```

### Stap 2: SI4703 Plaatsing
```
1. Plaats SI4703 module op breadboard
2. Zorg dat pins goed in de gaatjes zitten
3. Controleer pinout op module (VCC, SDA, SCL, GND, RST, GPIO2)
```

### Stap 3: Voeding Verbindingen
```
1. Rood wire: Raspberry Pi Pin 1 (3.3V) -> SI4703 VCC
2. Zwart wire: Raspberry Pi Pin 6 (GND) -> SI4703 GND

⚠️ BELANGRIJK: Gebruik 3.3V, NIET 5V!
SI4703 is een 3.3V module en kan beschadigen bij 5V.
```

### Stap 4: I2C Verbindingen
```
1. Blauw wire: Raspberry Pi Pin 3 (GPIO2/SDA) -> SI4703 SDA
2. Geel wire: Raspberry Pi Pin 5 (GPIO3/SCL) -> SI4703 SCL

Deze verbindingen zijn essentieel voor communicatie.
```

### Stap 5: Control Verbindingen
```
1. Groen wire: Raspberry Pi Pin 11 (GPIO17) -> SI4703 RST
2. Wit wire: Raspberry Pi Pin 13 (GPIO27) -> SI4703 GPIO2

RST = Reset pin voor module initialisatie
GPIO2 = Mode control (I2C mode enable)
```

### Stap 6: Antenne
```
1. Sluit FM antenne aan op ANT pin van SI4703
2. Voor test: gebruik 30cm jumper wire als tijdelijke antenne
3. Voor beste ontvangst: gebruik externe FM antenne
```

## 🔍 Verificatie

### Visuele Controle
```
✅ Alle verbindingen stevig aangesloten
✅ Geen losse draden
✅ Juiste pinnen gebruikt (controleer met schema)
✅ 3.3V gebruikt (NIET 5V)
✅ SI4703 module goed geplaatst
✅ Antenne aangesloten
```

### Elektrische Test
```bash
# Test I2C verbinding
sudo i2cdetect -y 1

# Verwachte output: device op 0x10
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# 10: 10 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
```

## ⚠️ Veiligheidsrichtlijnen

### Voor Aansluiting
```
1. Schakel ALTIJD Raspberry Pi uit voor het maken van verbindingen
2. Controleer polariteit (+ en -) voordat je voeding aansluit
3. Gebruik juiste spanning (3.3V voor SI4703)
4. Controleer alle verbindingen voordat je inschakelt
```

### Tijdens Gebruik
```
1. Raak geen blootliggende draden aan tijdens gebruik
2. Zorg voor stabiele opstelling (breadboard kan niet bewegen)
3. Houd vloeistoffen weg van elektronica
4. Schakel uit bij problemen of rook
```

### Troubleshooting
```
Geen I2C detectie:
- Controleer SDA/SCL verbindingen
- Controleer voeding (3.3V)
- Controleer of I2C enabled is: sudo raspi-config

Module reageert niet:
- Controleer RST verbinding
- Controleer GPIO2 verbinding
- Probeer module reset: kort RST naar GND

Slechte ontvangst:
- Controleer antenne verbinding
- Probeer andere antenne
- Controleer voor interferentie
```

## 🔧 Uitbreidingen

### Optionele Componenten
```
LCD Display (16x2 I2C):
- VCC -> 3.3V
- GND -> GND  
- SDA -> GPIO2 (gedeeld met SI4703)
- SCL -> GPIO3 (gedeeld met SI4703)

Rotary Encoder:
- CLK -> GPIO18
- DT  -> GPIO19
- SW  -> GPIO20
- VCC -> 3.3V
- GND -> GND

Push Buttons:
- Button 1 -> GPIO21 (Seek Up)
- Button 2 -> GPIO22 (Seek Down)
- Button 3 -> GPIO23 (Record)
- Andere kant -> GND
```

### PCB Design
```
Voor permanente installatie:
1. Gebruik KiCad bestanden in hardware/schematics/
2. Bestel PCB bij fabrikant (JLCPCB, PCBWay, etc.)
3. Soldeer componenten volgens schema
4. Test grondig voor eerste gebruik
```

## 📞 Hulp

Bij problemen met hardware:
1. Controleer alle verbindingen met multimeter
2. Vergelijk met foto's van werkende opstelling
3. Test componenten individueel
4. Vraag hulp op forum of GitHub issues
