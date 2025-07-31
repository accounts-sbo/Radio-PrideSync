#!/usr/bin/env python3
"""
SI4703 FM Radio Test Script voor Raspberry Pi Zero 2 W
Correcte wiring gebaseerd op officiële pinouts:

RASPBERRY PI ZERO 2 W -> SI4703 BREAKOUT
Pin 1  (3.3V)     -> VCC
Pin 3  (GPIO 2)   -> SDA  
Pin 5  (GPIO 3)   -> SCL
Pin 6  (GND)      -> GND
Pin 11 (GPIO 17)  -> RST
Pin 13 (GPIO 27)  -> SEN

Antenne: 3.5mm audio jack naar ANT pin op SI4703
"""

import RPi.GPIO as GPIO
import time
import subprocess
import sys

# Pin definities (BCM nummering)
RST_PIN = 17  # Pin 11 (Physical)
SEN_PIN = 27  # Pin 13 (Physical)
I2C_ADDRESS = 0x10  # SI4703 I2C adres

def si4703_powerup():
    """Voer de correcte power-up sequence uit voor SI4703"""
    print("SI4703 Power-up sequence starten...")
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RST_PIN, GPIO.OUT)
    GPIO.setup(SEN_PIN, GPIO.OUT)
    
    # Stap 1: Beide pins laag (reset state)
    print("Stap 1: Reset en SEN pins laag zetten...")
    GPIO.output(RST_PIN, GPIO.LOW)
    GPIO.output(SEN_PIN, GPIO.LOW)
    time.sleep(0.1)  # 100ms wachten
    
    # Stap 2: SEN hoog voor I2C mode, dan RST hoog
    print("Stap 2: SEN hoog (I2C mode), dan RST hoog...")
    GPIO.output(SEN_PIN, GPIO.HIGH)  # I2C mode selecteren
    time.sleep(0.001)  # 1ms wachten
    GPIO.output(RST_PIN, GPIO.HIGH)  # Reset vrijgeven
    time.sleep(0.01)   # 10ms wachten voor stabilisatie
    
    print("Power-up sequence voltooid!")

def check_i2c_device():
    """Controleer of SI4703 zichtbaar is op I2C bus"""
    print(f"\nControleren of SI4703 zichtbaar is op I2C adres 0x{I2C_ADDRESS:02x}...")
    
    try:
        # Voer i2cdetect uit
        result = subprocess.run(['i2cdetect', '-y', '1'], 
                              capture_output=True, text=True, check=True)
        print("I2C scan resultaat:")
        print(result.stdout)
        
        # Controleer of ons adres aanwezig is
        if f"{I2C_ADDRESS:02x}" in result.stdout:
            print(f"✓ SI4703 gevonden op adres 0x{I2C_ADDRESS:02x}!")
            return True
        else:
            print(f"✗ SI4703 niet gevonden op adres 0x{I2C_ADDRESS:02x}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Fout bij I2C scan: {e}")
        return False
    except FileNotFoundError:
        print("i2cdetect commando niet gevonden. Installeer i2c-tools:")
        print("sudo apt-get install i2c-tools")
        return False

def cleanup():
    """Ruim GPIO pins op"""
    print("\nGPIO pins opruimen...")
    GPIO.cleanup()

def main():
    """Hoofdfunctie"""
    print("=== SI4703 FM Radio Test ===")
    print("Controleer de bedrading volgens het schema in de comments!")
    print()
    
    try:
        # Voer power-up sequence uit
        si4703_powerup()
        
        # Controleer I2C verbinding
        if check_i2c_device():
            print("\n✓ Hardware test geslaagd!")
            print("SI4703 is correct aangesloten en reageert op I2C.")
        else:
            print("\n✗ Hardware test gefaald!")
            print("Controleer de bedrading en probeer opnieuw.")
            
    except KeyboardInterrupt:
        print("\nTest onderbroken door gebruiker.")
    except Exception as e:
        print(f"\nOnverwachte fout: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
