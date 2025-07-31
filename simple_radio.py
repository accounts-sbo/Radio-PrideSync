#!/usr/bin/env python3
"""
Standalone Radio - Automatisch opstarten op 96.8 MHz
Minimaal script voor SI4703 FM radio module
Start automatisch bij boot van Raspberry Pi
"""

import time
import sys
import signal
import logging
from pathlib import Path

# Setup logging - schrijf naar home directory
log_file = str(Path.home() / 'radio.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    import smbus2
    logger.info("GPIO en I2C libraries succesvol geladen")
except ImportError as e:
    logger.error(f"Fout: Kan benodigde library niet importeren: {e}")
    logger.error("Installeer met: sudo apt install python3-rpi.gpio python3-smbus")
    sys.exit(1)

class StandaloneRadio:
    """Standalone SI4703 radio klasse voor automatisch opstarten"""

    # SI4703 I2C adres
    SI4703_ADDR = 0x10

    # Register adressen
    POWERCFG = 0x02
    CHANNEL = 0x03
    SYSCONFIG1 = 0x04
    SYSCONFIG2 = 0x05
    STATUSRSSI = 0x0A
    READCHAN = 0x0B

    # Standaard frequentie: 96.8 MHz
    DEFAULT_FREQUENCY = 96.8

    def __init__(self, rst_pin=18, sdio_pin=2):
        """Initialiseer radio met reset en SDIO pinnen"""
        self.rst_pin = rst_pin
        self.sdio_pin = sdio_pin
        self.bus = None
        self.running = False

        # Setup signal handlers voor graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.rst_pin, GPIO.OUT)
        GPIO.setup(self.sdio_pin, GPIO.OUT)

        logger.info("🎵 Standalone Radio geïnitialiseerd")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Shutdown signaal ontvangen: {signum}")
        self.shutdown()
    
    def initialize(self):
        """Initialiseer de SI4703 chip"""
        try:
            logger.info("Resetten van SI4703...")

            # Reset sequence
            GPIO.output(self.sdio_pin, GPIO.LOW)
            GPIO.output(self.rst_pin, GPIO.LOW)
            time.sleep(0.1)
            GPIO.output(self.rst_pin, GPIO.HIGH)
            time.sleep(0.1)

            # Switch naar I2C modus
            GPIO.setup(self.sdio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Open I2C bus
            self.bus = smbus2.SMBus(1)
            time.sleep(0.1)

            # Power up de chip
            logger.info("SI4703 wordt ingeschakeld...")
            self._write_register(self.POWERCFG, 0x4001)  # Enable + Power up
            time.sleep(0.5)

            # Configureer voor stereo ontvangst
            self._write_register(self.SYSCONFIG1, 0x1000)  # RDS enable
            self._write_register(self.SYSCONFIG2, 0x0F10)  # Volume = 15 (max)

            logger.info("✅ SI4703 succesvol geïnitialiseerd")
            return True

        except Exception as e:
            logger.error(f"❌ Fout bij initialiseren: {e}")
            return False
    
    def _write_register(self, reg, value):
        """Schrijf naar SI4703 register"""
        try:
            # SI4703 gebruikt 16-bit registers, big endian
            high_byte = (value >> 8) & 0xFF
            low_byte = value & 0xFF
            self.bus.write_i2c_block_data(self.SI4703_ADDR, reg, [high_byte, low_byte])
            time.sleep(0.01)  # Korte delay
        except Exception as e:
            logger.error(f"Fout bij schrijven naar register {reg:02X}: {e}")

    def _read_register(self, reg):
        """Lees van SI4703 register"""
        try:
            data = self.bus.read_i2c_block_data(self.SI4703_ADDR, reg, 2)
            return (data[0] << 8) | data[1]
        except Exception as e:
            logger.error(f"Fout bij lezen van register {reg:02X}: {e}")
            return 0
    
    def set_frequency(self, freq_mhz):
        """Stel frequentie in (87.5 - 108.0 MHz) - Geoptimaliseerd voor 96.8 MHz"""
        if freq_mhz < 87.5 or freq_mhz > 108.0:
            logger.error(f"❌ Ongeldige frequentie: {freq_mhz} MHz")
            return False

        try:
            logger.info(f"📻 Afstemmen op {freq_mhz} MHz...")

            # Bereken channel waarde - Correcte formule voor SI4703
            # Channel = (Freq - 87.5) / 0.1 (SI4703 gebruikt 100kHz stappen)
            channel = int((freq_mhz - 87.5) / 0.1)

            logger.debug(f"Channel berekening: {freq_mhz} MHz = channel {channel}")

            # Schrijf channel naar register met TUNE bit
            channel_reg = (channel & 0x03FF) | 0x8000  # TUNE bit = 1, channel in bits 0-9
            self._write_register(self.CHANNEL, channel_reg)

            # Wacht tot tuning compleet is
            logger.info("Wachten op tuning...")
            for i in range(50):  # Max 5 seconden wachten
                status = self._read_register(self.STATUSRSSI)
                if status & 0x4000:  # STC bit (Seek/Tune Complete)
                    logger.debug(f"Tuning compleet na {i*0.1:.1f} seconden")
                    break
                time.sleep(0.1)
            else:
                logger.warning("Tuning timeout")

            # Clear TUNE bit
            self._write_register(self.CHANNEL, channel & 0x03FF)

            # Verifieer frequentie
            actual_freq = self.get_current_frequency()
            logger.info(f"✅ Afgestemd op {actual_freq:.1f} MHz (gevraagd: {freq_mhz} MHz)")
            return True

        except Exception as e:
            logger.error(f"❌ Fout bij afstemmen: {e}")
            return False

    def get_current_frequency(self):
        """Krijg huidige frequentie van de chip"""
        try:
            readchan = self._read_register(self.READCHAN)
            channel = readchan & 0x03FF  # Channel bits 0-9
            frequency = 87.5 + (channel * 0.1)
            return frequency
        except Exception as e:
            logger.error(f"Fout bij lezen frequentie: {e}")
            return 0.0
    
    def get_signal_strength(self):
        """Krijg signaalsterkte (0-75)"""
        try:
            status = self._read_register(self.STATUSRSSI)
            rssi = status & 0x00FF
            return rssi
        except Exception as e:
            logger.error(f"Fout bij lezen signaalsterkte: {e}")
            return 0

    def run_standalone(self):
        """Start radio in standalone modus - blijft draaien tot gestopt"""
        logger.info("🚀 Starting standalone radio op 96.8 MHz...")

        # Initialiseer radio
        if not self.initialize():
            logger.error("❌ Kan radio niet initialiseren")
            return False

        # Stem af op 96.8 MHz
        if not self.set_frequency(self.DEFAULT_FREQUENCY):
            logger.error(f"❌ Kan niet afstemmen op {self.DEFAULT_FREQUENCY} MHz")
            return False

        # Toon signaalsterkte
        signal = self.get_signal_strength()
        logger.info(f"📶 Signaalsterkte: {signal}/75")

        logger.info(f"🎧 Radio draait nu op {self.DEFAULT_FREQUENCY} MHz")
        logger.info("   Radio blijft draaien tot systeem wordt afgesloten")

        # Blijf draaien en monitor signaal elke 30 seconden
        self.running = True
        try:
            while self.running:
                time.sleep(30)
                # Monitor signaal
                signal = self.get_signal_strength()
                current_freq = self.get_current_frequency()
                logger.debug(f"Status: {current_freq:.1f} MHz, Signaal: {signal}/75")

        except Exception as e:
            logger.error(f"Fout in standalone loop: {e}")

        return True

    def shutdown(self):
        """Graceful shutdown"""
        logger.info("👋 Radio wordt afgesloten...")
        self.running = False
        self.cleanup()

    def cleanup(self):
        """Ruim GPIO op"""
        try:
            if self.bus:
                self.bus.close()
            GPIO.cleanup()
            logger.info("🔌 GPIO opgeruimd")
        except Exception as e:
            logger.error(f"Fout bij cleanup: {e}")

def main():
    """Hoofdfunctie - start radio op 96.8 MHz"""
    print("🎵 Eenvoudige Radio - 96.8 MHz")
    print("=" * 35)
    
    radio = SimpleRadio()
    
    try:
        # Initialiseer radio
        if not radio.initialize():
            print("❌ Kan radio niet initialiseren")
            return
        
        # Stem af op 96.8 MHz
        if not radio.set_frequency(96.8):
            print("❌ Kan niet afstemmen op 96.8 MHz")
            return
        
        # Toon signaalsterkte
        signal = radio.get_signal_strength()
        print(f"📶 Signaalsterkte: {signal}/75")
        
        print("\n🎧 Radio is nu afgestemd op 96.8 MHz")
        print("   Sluit je koptelefoon aan en luister!")
        print("   Druk Ctrl+C om te stoppen")
        
        # Blijf draaien tot gebruiker stopt
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 Radio wordt gestopt...")
    except Exception as e:
        print(f"❌ Onverwachte fout: {e}")
    finally:
        radio.cleanup()

if __name__ == "__main__":
    main()
