# SI4703 FM Radio Wiring Diagram voor Raspberry Pi Zero 2 W

## Correcte Bedrading

### Raspberry Pi Zero 2 W naar SI4703 Breakout Board

```
RASPBERRY PI ZERO 2 W                    SI4703 BREAKOUT BOARD
┌─────────────────────┐                 ┌─────────────────────┐
│  1 │ 3.3V      ●────┼─────────────────┼──● VCC              │
│  2 │ 5V        ●    │                 │                     │
│  3 │ GPIO 2    ●────┼─────────────────┼──● SDA (I2C Data)   │
│  4 │ 5V        ●    │                 │                     │
│  5 │ GPIO 3    ●────┼─────────────────┼──● SCL (I2C Clock)  │
│  6 │ GND       ●────┼─────────────────┼──● GND              │
│  7 │ GPIO 4    ●    │                 │                     │
│  8 │ GPIO 14   ●    │                 │                     │
│  9 │ GND       ●    │                 │                     │
│ 10 │ GPIO 15   ●    │                 │                     │
│ 11 │ GPIO 17   ●────┼─────────────────┼──● RST (Reset)      │
│ 12 │ GPIO 18   ●    │                 │                     │
│ 13 │ GPIO 27   ●────┼─────────────────┼──● SEN (Enable)     │
│ 14 │ GND       ●    │                 │                     │
│    │ ...       ...  │                 │                     │
└─────────────────────┘                 └─────────────────────┘
```

### Antenne Verbinding
```
3.5mm Audio Jack ──────────────────────── ANT pin op SI4703
(Gebruik de tip van de jack als antenne)
```

## Pin Toewijzingen

| Raspberry Pi Pin | GPIO | SI4703 Pin | Functie |
|------------------|------|------------|---------|
| Pin 1            | 3.3V | VCC        | Voeding |
| Pin 3            | GPIO 2 | SDA      | I2C Data |
| Pin 5            | GPIO 3 | SCL      | I2C Clock |
| Pin 6            | GND  | GND        | Ground |
| Pin 11           | GPIO 17 | RST     | Reset |
| Pin 13           | GPIO 27 | SEN     | Enable (I2C Mode) |

## Belangrijke Opmerkingen

1. **Voeding**: SI4703 werkt op 3.3V - gebruik NOOIT 5V!
2. **I2C Adres**: SI4703 gebruikt standaard adres 0x10
3. **Power-up Sequence**: 
   - Eerst RST en SEN laag
   - Dan SEN hoog (voor I2C mode)
   - Dan RST hoog (reset vrijgeven)
4. **Antenne**: Een 3.5mm audio jack werkt goed als antenne
5. **Pull-up Resistors**: Raspberry Pi heeft ingebouwde pull-ups voor I2C

## Test Procedure

1. Controleer alle verbindingen volgens bovenstaand schema
2. Voer het test script uit: `python3 test_powerup.py`
3. Het script zal:
   - De correcte power-up sequence uitvoeren
   - Een I2C scan doen om de SI4703 te detecteren
   - Resultaat rapporteren

## Troubleshooting

Als de SI4703 niet wordt gedetecteerd:

1. **Controleer voeding**: Meet 3.3V tussen VCC en GND
2. **Controleer verbindingen**: Alle draden goed aangesloten?
3. **I2C enabled**: `sudo raspi-config` → Interface Options → I2C → Enable
4. **I2C tools**: `sudo apt-get install i2c-tools`
5. **Handmatige I2C scan**: `i2cdetect -y 1`

## Volgende Stappen

Na succesvolle hardware test:
1. Implementeer FM radio control functies
2. Voeg RDS (Radio Data System) ondersteuning toe
3. Maak een gebruikersinterface
4. Test verschillende radiostations
