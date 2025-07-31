"""
SI4703 FM Radio Tuner Driver
Voor Raspberry Pi met I2C communicatie
"""

import time
import logging
from smbus2 import SMBus
import RPi.GPIO as GPIO
from .rds_decoder import RDSDecoder

class SI4703Radio:
    """Driver voor SI4703 FM Radio Tuner module"""
    
    # SI4703 Register adressen
    DEVICEID = 0x00
    CHIPID = 0x01
    POWERCFG = 0x02
    CHANNEL = 0x03
    SYSCONFIG1 = 0x04
    SYSCONFIG2 = 0x05
    SYSCONFIG3 = 0x06
    TEST1 = 0x07
    TEST2 = 0x08
    BOOTCONFIG = 0x09
    STATUSRSSI = 0x0A
    READCHAN = 0x0B
    RDSA = 0x0C
    RDSB = 0x0D
    RDSC = 0x0E
    RDSD = 0x0F
    
    def __init__(self, config):
        """
        Initialiseer SI4703 radio
        
        Args:
            config (dict): Radio configuratie
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # I2C configuratie
        self.i2c_bus = 1  # Raspberry Pi I2C bus
        self.i2c_addr = int(config.get('i2c_address', '0x10'), 16)
        
        # GPIO pins
        self.reset_pin = config['gpio_pins']['reset']
        self.gpio2_pin = config['gpio_pins']['gpio2']
        
        # Radio status
        self.frequency = config.get('default_frequency', 96.8)
        self.volume = config['volume'].get('default', 8)
        self.powered = False

        # RDS decoder
        self.rds_decoder = RDSDecoder() if config.get('rds_enabled', True) else None
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.reset_pin, GPIO.OUT)
        GPIO.setup(self.gpio2_pin, GPIO.OUT)
        
        self.logger.info("SI4703 driver geïnitialiseerd")
    
    def initialize(self):
        """
        Initialiseer de SI4703 chip
        
        Returns:
            bool: True als succesvol
        """
        try:
            self.logger.info("SI4703 wordt geïnitialiseerd...")
            
            # Reset de chip
            self._reset_chip()
            
            # Wacht op chip ready
            time.sleep(0.5)
            
            # Controleer chip ID
            if not self._verify_chip():
                return False
            
            # Power up en configureer
            if not self._power_up():
                return False
            
            # Configureer audio en RDS
            self._configure_chip()
            
            self.powered = True
            self.logger.info("SI4703 succesvol geïnitialiseerd")
            return True
            
        except Exception as e:
            self.logger.error(f"SI4703 initialisatie gefaald: {e}")
            return False
    
    def _reset_chip(self):
        """Reset de SI4703 chip via GPIO"""
        self.logger.debug("SI4703 wordt gereset...")
        
        # Reset sequence
        GPIO.output(self.reset_pin, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.reset_pin, GPIO.HIGH)
        time.sleep(0.1)
        
        # Enable I2C mode via GPIO2
        GPIO.output(self.gpio2_pin, GPIO.HIGH)
        time.sleep(0.1)
    
    def _verify_chip(self):
        """Controleer of SI4703 chip aanwezig is"""
        try:
            with SMBus(self.i2c_bus) as bus:
                # Lees device ID
                device_id = self._read_register(bus, self.DEVICEID)
                chip_id = self._read_register(bus, self.CHIPID)
                
                self.logger.debug(f"Device ID: 0x{device_id:04X}")
                self.logger.debug(f"Chip ID: 0x{chip_id:04X}")
                
                # Verwachte waarden voor SI4703
                if (device_id & 0xFF00) == 0x1200:
                    self.logger.info("SI4703 chip gedetecteerd")
                    return True
                else:
                    self.logger.error("SI4703 chip niet gevonden")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Chip verificatie gefaald: {e}")
            return False
    
    def _power_up(self):
        """Power up de SI4703"""
        try:
            with SMBus(self.i2c_bus) as bus:
                # Power up met oscillator enable
                powercfg = 0x4001  # DMUTE=1, ENABLE=1
                self._write_register(bus, self.POWERCFG, powercfg)
                
                # Wacht op power up
                time.sleep(0.11)  # Minimaal 110ms
                
                self.logger.info("SI4703 powered up")
                return True
                
        except Exception as e:
            self.logger.error(f"Power up gefaald: {e}")
            return False
    
    def _configure_chip(self):
        """Configureer SI4703 instellingen"""
        try:
            with SMBus(self.i2c_bus) as bus:
                # SYSCONFIG1: RDS enable, seek threshold
                sysconfig1 = 0x1000  # RDS=1
                if self.config.get('rds_enabled', True):
                    sysconfig1 |= 0x1000
                
                self._write_register(bus, self.SYSCONFIG1, sysconfig1)
                
                # SYSCONFIG2: Volume en seek settings
                seek_th = self.config.get('seek_threshold', 20)
                sysconfig2 = (seek_th << 8) | self.volume
                self._write_register(bus, self.SYSCONFIG2, sysconfig2)
                
                # SYSCONFIG3: Extended volume range
                sysconfig3 = 0x0100  # VOLEXT=1
                self._write_register(bus, self.SYSCONFIG3, sysconfig3)
                
                self.logger.debug("SI4703 configuratie voltooid")
                
        except Exception as e:
            self.logger.error(f"Configuratie gefaald: {e}")
    
    def _read_register(self, bus, register):
        """Lees 16-bit register van SI4703"""
        # SI4703 gebruikt 16-bit registers
        data = bus.read_i2c_block_data(self.i2c_addr, register, 2)
        return (data[0] << 8) | data[1]
    
    def _write_register(self, bus, register, value):
        """Schrijf 16-bit register naar SI4703"""
        data = [(value >> 8) & 0xFF, value & 0xFF]
        bus.write_i2c_block_data(self.i2c_addr, register, data)
    
    def set_frequency(self, frequency):
        """
        Stel radio frequentie in
        
        Args:
            frequency (float): Frequentie in MHz (87.5 - 108.0)
            
        Returns:
            bool: True als succesvol
        """
        freq_min = self.config['frequency_range']['min']
        freq_max = self.config['frequency_range']['max']
        
        if not (freq_min <= frequency <= freq_max):
            self.logger.warning(f"Frequentie {frequency} buiten bereik ({freq_min}-{freq_max})")
            return False
        
        try:
            with SMBus(self.i2c_bus) as bus:
                # Bereken channel waarde
                # Channel = (Freq - 87.5) / 0.1
                channel = int((frequency - 87.5) / 0.1)
                
                # Lees huidige CHANNEL register
                channel_reg = self._read_register(bus, self.CHANNEL)
                
                # Update channel bits (0-9) en set TUNE bit
                channel_reg = (channel_reg & 0xFC00) | channel | 0x8000
                
                # Schrijf nieuwe frequentie
                self._write_register(bus, self.CHANNEL, channel_reg)
                
                # Wacht op tune complete
                self._wait_for_tune_complete(bus)
                
                self.frequency = frequency
                self.logger.info(f"Frequentie ingesteld op {frequency:.1f} MHz")
                return True
                
        except Exception as e:
            self.logger.error(f"Frequentie instellen gefaald: {e}")
            return False
    
    def _wait_for_tune_complete(self, bus, timeout=2.0):
        """Wacht tot tune operatie voltooid is"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self._read_register(bus, self.STATUSRSSI)
            if status & 0x4000:  # STC bit
                # Clear tune bit
                channel_reg = self._read_register(bus, self.CHANNEL)
                channel_reg &= ~0x8000  # Clear TUNE bit
                self._write_register(bus, self.CHANNEL, channel_reg)
                return True
            time.sleep(0.01)
        
        self.logger.warning("Tune timeout")
        return False
    
    def get_frequency(self):
        """
        Krijg huidige frequentie
        
        Returns:
            float: Huidige frequentie in MHz
        """
        return self.frequency
    
    def set_volume(self, volume):
        """
        Stel volume in
        
        Args:
            volume (int): Volume level (0-15)
            
        Returns:
            bool: True als succesvol
        """
        vol_min = self.config['volume']['min']
        vol_max = self.config['volume']['max']
        
        if not (vol_min <= volume <= vol_max):
            self.logger.warning(f"Volume {volume} buiten bereik ({vol_min}-{vol_max})")
            return False
        
        try:
            with SMBus(self.i2c_bus) as bus:
                # Lees huidige SYSCONFIG2
                sysconfig2 = self._read_register(bus, self.SYSCONFIG2)
                
                # Update volume bits (0-3)
                sysconfig2 = (sysconfig2 & 0xFFF0) | volume
                
                # Schrijf nieuwe volume
                self._write_register(bus, self.SYSCONFIG2, sysconfig2)
                
                self.volume = volume
                self.logger.debug(f"Volume ingesteld op {volume}")
                return True
                
        except Exception as e:
            self.logger.error(f"Volume instellen gefaald: {e}")
            return False
    
    def get_volume(self):
        """
        Krijg huidig volume

        Returns:
            int: Huidig volume level
        """
        return self.volume

    def seek_up(self):
        """
        Zoek naar volgende station (omhoog)

        Returns:
            bool: True als station gevonden
        """
        return self._seek(True)

    def seek_down(self):
        """
        Zoek naar vorige station (omlaag)

        Returns:
            bool: True als station gevonden
        """
        return self._seek(False)

    def _seek(self, seek_up=True):
        """
        Zoek naar station

        Args:
            seek_up (bool): True voor omhoog, False voor omlaag

        Returns:
            bool: True als station gevonden
        """
        try:
            with SMBus(self.i2c_bus) as bus:
                # Lees huidige POWERCFG
                powercfg = self._read_register(bus, self.POWERCFG)

                # Set SEEK bit en richting
                powercfg |= 0x0100  # SEEK=1
                if seek_up:
                    powercfg |= 0x0200  # SEEKUP=1
                else:
                    powercfg &= ~0x0200  # SEEKUP=0

                # Start seek
                self._write_register(bus, self.POWERCFG, powercfg)

                # Wacht op seek complete
                if self._wait_for_seek_complete(bus):
                    # Lees nieuwe frequentie
                    readchan = self._read_register(bus, self.READCHAN)
                    channel = readchan & 0x03FF
                    self.frequency = 87.5 + (channel * 0.1)

                    self.logger.info(f"Station gevonden op {self.frequency:.1f} MHz")
                    return True
                else:
                    self.logger.info("Geen station gevonden")
                    return False

        except Exception as e:
            self.logger.error(f"Seek gefaald: {e}")
            return False

    def _wait_for_seek_complete(self, bus, timeout=10.0):
        """Wacht tot seek operatie voltooid is"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self._read_register(bus, self.STATUSRSSI)
            if status & 0x4000:  # STC bit
                # Clear seek bit
                powercfg = self._read_register(bus, self.POWERCFG)
                powercfg &= ~0x0100  # Clear SEEK bit
                self._write_register(bus, self.POWERCFG, powercfg)

                # Check if station found
                return bool(status & 0x2000)  # SF bit
            time.sleep(0.1)

        self.logger.warning("Seek timeout")
        return False

    def get_signal_strength(self):
        """
        Krijg signaal sterkte

        Returns:
            int: RSSI waarde (0-75)
        """
        try:
            with SMBus(self.i2c_bus) as bus:
                status = self._read_register(bus, self.STATUSRSSI)
                rssi = status & 0x00FF
                return rssi

        except Exception as e:
            self.logger.error(f"RSSI lezen gefaald: {e}")
            return 0

    def get_rds_info(self):
        """
        Krijg RDS informatie

        Returns:
            dict: RDS data (station_name, radio_text, etc.)
        """
        if not self.config.get('rds_enabled', True) or not self.rds_decoder:
            return None

        try:
            with SMBus(self.i2c_bus) as bus:
                # Check RDS ready
                status = self._read_register(bus, self.STATUSRSSI)
                if not (status & 0x8000):  # RDSR bit
                    return self.rds_decoder.get_current_info()

                # Lees RDS registers
                rdsa = self._read_register(bus, self.RDSA)
                rdsb = self._read_register(bus, self.RDSB)
                rdsc = self._read_register(bus, self.RDSC)
                rdsd = self._read_register(bus, self.RDSD)

                # Decode RDS data met professionele decoder
                decoded_info = self.rds_decoder.decode_group(rdsa, rdsb, rdsc, rdsd)

                # Return huidige complete RDS info
                return self.rds_decoder.get_current_info()

        except Exception as e:
            self.logger.error(f"RDS lezen gefaald: {e}")
            return None



    def power_down(self):
        """Schakel radio uit"""
        try:
            if not self.powered:
                return

            with SMBus(self.i2c_bus) as bus:
                # Clear ENABLE bit
                powercfg = self._read_register(bus, self.POWERCFG)
                powercfg &= ~0x0001  # ENABLE=0
                self._write_register(bus, self.POWERCFG, powercfg)

            self.powered = False
            self.logger.info("SI4703 uitgeschakeld")

        except Exception as e:
            self.logger.error(f"Power down gefaald: {e}")
        finally:
            # Cleanup GPIO
            GPIO.cleanup([self.reset_pin, self.gpio2_pin])

    def is_powered(self):
        """
        Check of radio aan staat

        Returns:
            bool: True als radio aan staat
        """
        return self.powered
