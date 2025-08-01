#!/usr/bin/env python3
"""
Radio 96.8 MHz - Direct werkende versie
Eenvoudig script voor SI4703 FM radio module
"""

import time
import sys
import signal
import logging
from pathlib import Path

# Setup logging
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

class Radio968:
    """Radio klasse voor 96.8 MHz"""
    
    # SI4703 I2C adres
    SI4703_ADDR = 0x10
    
    # Register adressen
    POWERCFG = 0x02
    CHANNEL = 0x03
    SYSCONFIG1 = 0x04
    SYSCONFIG2 = 0x05
    STATUSRSSI = 0x0A
    READCHAN = 0x0B
    
    def __init__(self, rst_pin=18, sdio_pin=2):
        """Initialiseer radio"""
        self.rst_pin = rst_pin
        self.sdio_pin = sdio_pin
        self.bus = None
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Setup GPIO
        GPIO.setwarnings(False)  # Disable warnings
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.rst_pin, GPIO.OUT)
        GPIO.setup(self.sdio_pin, GPIO.OUT)
        
        logger.info("🎵 Radio 96.8 MHz geïnitialiseerd")
    
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
            # POWERCFG: DMUTE=1 (audio on), ENABLE=1 (power on), DISABLE=0 (tuner enabled)
            self._write_register(self.POWERCFG, 0x4001)  # Enable + Power up
            time.sleep(0.5)

            # Controleer of chip powered up is
            status = self._read_register(self.STATUSRSSI)
            logger.info(f"Power status: 0x{status:04X}")

            # Enable tuner expliciet (zorg dat DISABLE bit (bit 6) = 0)
            logger.info("Tuner wordt expliciet ingeschakeld...")
            # POWERCFG bits: DSMUTE=1, DMUTE=1, MONO=0, RDSM=0, SKMODE=0, SEEKUP=0, SEEK=0, DISABLE=0, ENABLE=1
            powercfg_tuner = 0x4001  # Bit 15=DSMUTE, bit 14=DMUTE, bit 0=ENABLE, bit 6=DISABLE(0)
            self._write_register(self.POWERCFG, powercfg_tuner)
            time.sleep(0.2)

            # Configureer voor stereo ontvangst
            self._write_register(self.SYSCONFIG1, 0x1000)  # RDS enable
            self._write_register(self.SYSCONFIG2, 0x0F10)  # Volume = 15 (max)

            # Verifieer dat tuner actief is
            powercfg_read = self._read_register(self.POWERCFG)
            logger.info(f"POWERCFG register: 0x{powercfg_read:04X}")
            if powercfg_read & 0x0040:  # DISABLE bit
                logger.warning("⚠️  Tuner lijkt nog steeds disabled!")
            else:
                logger.info("✅ Tuner is enabled")
            
            logger.info("✅ SI4703 succesvol geïnitialiseerd")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fout bij initialiseren: {e}")
            return False
    
    def _write_register(self, reg, value):
        """Schrijf naar SI4703 register"""
        try:
            high_byte = (value >> 8) & 0xFF
            low_byte = value & 0xFF
            self.bus.write_i2c_block_data(self.SI4703_ADDR, reg, [high_byte, low_byte])
            time.sleep(0.01)
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
    
    def set_frequency_968(self):
        """Stel frequentie in op 96.8 MHz"""
        freq_mhz = 96.8
        try:
            logger.info(f"📻 Afstemmen op {freq_mhz} MHz...")

            # Bereken channel waarde voor SI4703
            # Channel = (Freq - 87.5) / 0.1 (100kHz stappen)
            channel = int(round((freq_mhz - 87.5) / 0.1))

            logger.info(f"Channel berekening: {freq_mhz} MHz = channel {channel}")
            logger.info(f"Verificatie: channel {channel} = {87.5 + (channel * 0.1):.1f} MHz")

            # Lees huidige CHANNEL register
            current_channel_reg = self._read_register(self.CHANNEL)
            logger.info(f"Huidig CHANNEL register: 0x{current_channel_reg:04X}")

            # Schrijf channel naar register met TUNE bit
            channel_reg = (channel & 0x03FF) | 0x8000  # TUNE bit = 1
            logger.info(f"Nieuwe CHANNEL register: 0x{channel_reg:04X}")
            self._write_register(self.CHANNEL, channel_reg)

            # Wacht tot tuning compleet is
            logger.info("Wachten op tuning complete (STC bit)...")
            tune_success = False
            for i in range(50):
                status = self._read_register(self.STATUSRSSI)
                logger.debug(f"STATUSRSSI: 0x{status:04X}")
                if status & 0x4000:  # STC bit
                    logger.info(f"✅ Tuning compleet na {i*0.1:.1f} seconden")
                    tune_success = True
                    break
                time.sleep(0.1)

            if not tune_success:
                logger.warning("⚠️  Tuning timeout - geen STC bit ontvangen")
                # Probeer alsnog door te gaan

            # Clear TUNE bit (BELANGRIJK!)
            logger.info("Clearing TUNE bit...")
            self._write_register(self.CHANNEL, channel & 0x03FF)

            # Wacht even en verifieer frequentie
            time.sleep(0.2)
            actual_freq = self.get_current_frequency()
            logger.info(f"✅ Afgestemd op {actual_freq:.1f} MHz (gevraagd: {freq_mhz})")

            # Check of frequentie correct is
            if abs(actual_freq - freq_mhz) > 0.2:
                logger.error(f"❌ Frequentie mismatch! Gevraagd: {freq_mhz}, Werkelijk: {actual_freq:.1f}")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Fout bij afstemmen: {e}")
            return False
    
    def get_current_frequency(self):
        """Krijg huidige frequentie"""
        try:
            readchan = self._read_register(self.READCHAN)
            channel = readchan & 0x03FF
            frequency = 87.5 + (channel * 0.1)
            return frequency
        except Exception as e:
            logger.error(f"Fout bij lezen frequentie: {e}")
            return 0.0
    
    def get_signal_strength(self):
        """Krijg signaalsterkte"""
        try:
            status = self._read_register(self.STATUSRSSI)
            rssi = status & 0x00FF
            return rssi
        except Exception as e:
            logger.error(f"Fout bij lezen signaalsterkte: {e}")
            return 0
    
    def start_radio(self):
        """Start radio op 96.8 MHz"""
        logger.info("🚀 Starting radio op 96.8 MHz...")
        
        # Initialiseer radio
        if not self.initialize():
            logger.error("❌ Kan radio niet initialiseren")
            return False
        
        # Stem af op 96.8 MHz
        if not self.set_frequency_968():
            logger.error("❌ Kan niet afstemmen op 96.8 MHz")
            return False
        
        # Toon signaalsterkte
        signal = self.get_signal_strength()
        logger.info(f"📶 Signaalsterkte: {signal}/75")
        
        logger.info("🎧 Radio draait nu op 96.8 MHz")
        logger.info("   Sluit je koptelefoon aan op de audio uitgang!")
        logger.info("   Radio blijft draaien...")
        
        # Blijf draaien
        self.running = True
        try:
            while self.running:
                time.sleep(30)
                # Monitor signaal
                signal = self.get_signal_strength()
                current_freq = self.get_current_frequency()
                logger.info(f"Status: {current_freq:.1f} MHz, Signaal: {signal}/75")
                
        except Exception as e:
            logger.error(f"Fout in radio loop: {e}")
        
        return True
    
    def shutdown(self):
        """Shutdown radio"""
        logger.info("👋 Radio wordt afgesloten...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup GPIO"""
        try:
            if self.bus:
                self.bus.close()
            GPIO.cleanup()
            logger.info("🔌 GPIO opgeruimd")
        except Exception as e:
            logger.error(f"Fout bij cleanup: {e}")

def main():
    """Start radio op 96.8 MHz"""
    logger.info("🎵 Radio 96.8 MHz wordt gestart...")
    
    radio = Radio968()
    
    try:
        success = radio.start_radio()
        if not success:
            logger.error("❌ Radio kon niet starten")
            return
            
    except KeyboardInterrupt:
        logger.info("👋 Radio gestopt door gebruiker")
    except Exception as e:
        logger.error(f"❌ Onverwachte fout: {e}")
    finally:
        radio.shutdown()

if __name__ == "__main__":
    main()
