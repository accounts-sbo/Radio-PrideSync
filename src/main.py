#!/usr/bin/env python3
"""
Radio PrideSync - Hoofdprogramma
FM Radio ontvanger met SI4703 module voor Raspberry Pi Zero 2 W
"""

import sys
import json
import time
import signal
import logging
from pathlib import Path

# Voeg src directory toe aan Python path
sys.path.append(str(Path(__file__).parent))

from radio.si4703 import SI4703Radio
from audio.recorder import AudioRecorder
from utils.logger import setup_logger

class RadioPrideSync:
    """Hoofdklasse voor Radio PrideSync applicatie"""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.radio = None
        self.recorder = None
        self.running = False
        
        # Laad configuratie
        self.load_config()
        
        # Setup signal handlers voor graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def load_config(self):
        """Laad configuratie bestanden"""
        try:
            # Radio configuratie
            with open('config/radio_config.json', 'r') as f:
                self.radio_config = json.load(f)
            
            # Audio configuratie
            with open('config/audio_config.json', 'r') as f:
                self.audio_config = json.load(f)
                
            self.logger.info("Configuratie succesvol geladen")
            
        except FileNotFoundError as e:
            self.logger.error(f"Configuratie bestand niet gevonden: {e}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            self.logger.error(f"Fout in configuratie bestand: {e}")
            sys.exit(1)
    
    def initialize_hardware(self):
        """Initialiseer radio en audio hardware"""
        try:
            # Initialiseer SI4703 radio
            self.logger.info("Initialiseren van SI4703 radio module...")
            self.radio = SI4703Radio(self.radio_config)
            
            if not self.radio.initialize():
                raise Exception("SI4703 initialisatie gefaald")
            
            # Initialiseer audio recorder
            self.logger.info("Initialiseren van audio recorder...")
            self.recorder = AudioRecorder(self.audio_config)
            
            self.logger.info("Hardware succesvol geïnitialiseerd")
            return True
            
        except Exception as e:
            self.logger.error(f"Hardware initialisatie gefaald: {e}")
            return False
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Shutdown signaal ontvangen: {signum}")
        self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Radio PrideSync wordt afgesloten...")
        self.running = False
        
        if self.recorder and self.recorder.is_recording():
            self.logger.info("Opname wordt gestopt...")
            self.recorder.stop_recording()
        
        if self.radio:
            self.logger.info("Radio wordt uitgeschakeld...")
            self.radio.power_down()
        
        self.logger.info("Afsluiting voltooid")
        sys.exit(0)
    
    def display_status(self):
        """Toon huidige radio status"""
        if not self.radio:
            return
        
        frequency = self.radio.get_frequency()
        volume = self.radio.get_volume()
        rds_info = self.radio.get_rds_info()
        
        print(f"\n📻 Radio Status:")
        print(f"   Frequentie: {frequency:.1f} MHz")
        print(f"   Volume: {volume}/15")
        
        if rds_info:
            if rds_info.get('station_name'):
                print(f"   Station: {rds_info['station_name']}")
            if rds_info.get('radio_text'):
                print(f"   Info: {rds_info['radio_text']}")
        
        if self.recorder and self.recorder.is_recording():
            print(f"   🔴 OPNAME ACTIEF")
        
        print("-" * 40)
    
    def interactive_mode(self):
        """Interactieve modus voor handmatige bediening"""
        print("\n🎵 Radio PrideSync - Interactieve Modus")
        print("=====================================")
        print("Commando's:")
        print("  f <freq>  - Stel frequentie in (bijv: f 100.5)")
        print("  v <vol>   - Stel volume in (0-15)")
        print("  s         - Zoek naar volgende station")
        print("  r         - Start/stop opname")
        print("  i         - Toon radio informatie")
        print("  q         - Afsluiten")
        print()
        
        while self.running:
            try:
                self.display_status()
                command = input("Radio> ").strip().lower()
                
                if command == 'q':
                    break
                elif command == 'i':
                    continue  # Status wordt al getoond
                elif command == 's':
                    print("Zoeken naar station...")
                    if self.radio.seek_up():
                        print("Station gevonden!")
                    else:
                        print("Geen station gevonden")
                elif command == 'r':
                    if self.recorder.is_recording():
                        filename = self.recorder.stop_recording()
                        print(f"Opname gestopt: {filename}")
                    else:
                        frequency = self.radio.get_frequency()
                        filename = self.recorder.start_recording(frequency)
                        print(f"Opname gestart: {filename}")
                elif command.startswith('f '):
                    try:
                        freq = float(command.split()[1])
                        if self.radio.set_frequency(freq):
                            print(f"Frequentie ingesteld op {freq:.1f} MHz")
                        else:
                            print("Ongeldige frequentie")
                    except (IndexError, ValueError):
                        print("Gebruik: f <frequentie> (bijv: f 100.5)")
                elif command.startswith('v '):
                    try:
                        vol = int(command.split()[1])
                        if self.radio.set_volume(vol):
                            print(f"Volume ingesteld op {vol}")
                        else:
                            print("Ongeldig volume (0-15)")
                    except (IndexError, ValueError):
                        print("Gebruik: v <volume> (bijv: v 10)")
                else:
                    print("Onbekend commando. Typ 'q' om af te sluiten.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Fout in interactieve modus: {e}")
    
    def run(self):
        """Start de radio applicatie"""
        self.logger.info("Radio PrideSync wordt gestart...")
        
        if not self.initialize_hardware():
            self.logger.error("Kan hardware niet initialiseren")
            return False
        
        # Stel standaard frequentie in
        default_freq = self.radio_config.get('default_frequency', 100.0)
        self.radio.set_frequency(default_freq)
        
        # Stel standaard volume in
        default_vol = self.radio_config['volume'].get('default', 8)
        self.radio.set_volume(default_vol)
        
        self.running = True
        self.logger.info("Radio PrideSync is gestart")
        
        # Start interactieve modus
        self.interactive_mode()
        
        return True

def main():
    """Hoofdfunctie"""
    app = RadioPrideSync()
    
    try:
        success = app.run()
        if not success:
            sys.exit(1)
    except Exception as e:
        logging.error(f"Onverwachte fout: {e}")
        sys.exit(1)
    finally:
        app.shutdown()

if __name__ == "__main__":
    main()
