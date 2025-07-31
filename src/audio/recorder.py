"""
Audio Recorder voor Radio PrideSync
Neemt audio op van radio en slaat op als MP3
"""

import os
import time
import threading
import logging
from datetime import datetime
from pathlib import Path

import pyaudio
import numpy as np
from pydub import AudioSegment
from pydub.utils import make_chunks

class AudioRecorder:
    """Audio recorder voor radio opnames"""
    
    def __init__(self, config):
        """
        Initialiseer audio recorder
        
        Args:
            config (dict): Audio configuratie
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Audio instellingen
        self.sample_rate = config['recording']['sample_rate']
        self.channels = config['recording']['channels']
        self.chunk_size = 1024
        self.format = pyaudio.paInt16
        
        # Opname status
        self.recording = False
        self.recording_thread = None
        self.current_filename = None
        
        # Audio buffers
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()
        
        # PyAudio instance
        self.audio = None
        self.stream = None
        
        # Output directory
        self.output_dir = Path(config['recording']['output_directory'])
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger.info("Audio recorder geïnitialiseerd")
    
    def _initialize_audio(self):
        """Initialiseer PyAudio"""
        try:
            if self.audio is None:
                self.audio = pyaudio.PyAudio()
            
            # Zoek audio input device
            input_device = self._find_input_device()
            if input_device is None:
                raise Exception("Geen audio input device gevonden")
            
            # Open audio stream
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=input_device,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.logger.info(f"Audio stream geopend (device: {input_device})")
            return True
            
        except Exception as e:
            self.logger.error(f"Audio initialisatie gefaald: {e}")
            return False
    
    def _find_input_device(self):
        """Zoek geschikt audio input device"""
        try:
            device_count = self.audio.get_device_count()
            
            for i in range(device_count):
                device_info = self.audio.get_device_info_by_index(i)
                
                # Zoek device met input channels
                if device_info['maxInputChannels'] > 0:
                    device_name = device_info['name']
                    self.logger.debug(f"Audio input device gevonden: {device_name}")
                    
                    # Prefer USB audio or specific devices
                    if any(keyword in device_name.lower() for keyword in ['usb', 'audio', 'line']):
                        return i
            
            # Fallback naar eerste beschikbare input device
            for i in range(device_count):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    return i
            
            return None
            
        except Exception as e:
            self.logger.error(f"Audio device zoeken gefaald: {e}")
            return None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback voor audio data"""
        if self.recording:
            with self.buffer_lock:
                # Convert bytes to numpy array
                audio_data = np.frombuffer(in_data, dtype=np.int16)
                self.audio_buffer.extend(audio_data)
        
        return (in_data, pyaudio.paContinue)
    
    def start_recording(self, frequency=None):
        """
        Start audio opname
        
        Args:
            frequency (float): Radio frequentie voor bestandsnaam
            
        Returns:
            str: Bestandsnaam van opname
        """
        if self.recording:
            self.logger.warning("Opname is al actief")
            return self.current_filename
        
        try:
            # Initialiseer audio als nodig
            if not self._initialize_audio():
                raise Exception("Audio initialisatie gefaald")
            
            # Genereer bestandsnaam
            self.current_filename = self._generate_filename(frequency)
            
            # Reset buffer
            with self.buffer_lock:
                self.audio_buffer = []
            
            # Start opname
            self.recording = True
            self.stream.start_stream()
            
            # Start opname thread
            self.recording_thread = threading.Thread(
                target=self._recording_worker,
                daemon=True
            )
            self.recording_thread.start()
            
            self.logger.info(f"Opname gestart: {self.current_filename}")
            return self.current_filename
            
        except Exception as e:
            self.logger.error(f"Start opname gefaald: {e}")
            self.recording = False
            return None
    
    def stop_recording(self):
        """
        Stop audio opname
        
        Returns:
            str: Bestandsnaam van opgenomen bestand
        """
        if not self.recording:
            self.logger.warning("Geen actieve opname")
            return None
        
        try:
            # Stop opname
            self.recording = False
            
            if self.stream and self.stream.is_active():
                self.stream.stop_stream()
            
            # Wacht op recording thread
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=5.0)
            
            # Verwerk finale audio data
            self._save_recording()
            
            filename = self.current_filename
            self.current_filename = None
            
            self.logger.info(f"Opname gestopt: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Stop opname gefaald: {e}")
            return None
    
    def _recording_worker(self):
        """Worker thread voor opname verwerking"""
        chunk_duration = 10.0  # Sla elke 10 seconden op
        last_save = time.time()
        
        while self.recording:
            try:
                current_time = time.time()
                
                # Periodiek opslaan om geheugen te beheren
                if current_time - last_save >= chunk_duration:
                    self._save_chunk()
                    last_save = current_time
                
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Recording worker fout: {e}")
                break
    
    def _save_chunk(self):
        """Sla audio chunk op (tussentijds)"""
        try:
            with self.buffer_lock:
                if not self.audio_buffer:
                    return
                
                # Convert buffer to audio segment
                audio_data = np.array(self.audio_buffer, dtype=np.int16)
                
                # Create AudioSegment
                audio_segment = AudioSegment(
                    audio_data.tobytes(),
                    frame_rate=self.sample_rate,
                    sample_width=2,  # 16-bit = 2 bytes
                    channels=self.channels
                )
                
                # Append to file (create if not exists)
                output_path = self.output_dir / self.current_filename
                
                if output_path.exists():
                    # Append to existing file
                    existing_audio = AudioSegment.from_mp3(str(output_path))
                    combined_audio = existing_audio + audio_segment
                else:
                    combined_audio = audio_segment
                
                # Export as MP3
                bitrate = f"{self.config['recording']['bitrate']}k"
                combined_audio.export(
                    str(output_path),
                    format="mp3",
                    bitrate=bitrate
                )
                
                # Clear buffer
                self.audio_buffer = []
                
        except Exception as e:
            self.logger.error(f"Chunk opslaan gefaald: {e}")
    
    def _save_recording(self):
        """Sla finale opname op"""
        try:
            # Sla resterende buffer op
            self._save_chunk()
            
            # Voeg metadata toe
            self._add_metadata()
            
        except Exception as e:
            self.logger.error(f"Finale opname opslaan gefaald: {e}")
    
    def _add_metadata(self):
        """Voeg metadata toe aan MP3 bestand"""
        try:
            if not self.current_filename:
                return
            
            output_path = self.output_dir / self.current_filename
            if not output_path.exists():
                return
            
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC
            
            # Laad MP3 bestand
            audio_file = MP3(str(output_path))
            
            # Voeg ID3 tags toe
            if audio_file.tags is None:
                audio_file.add_tags()
            
            # Basis metadata
            audio_file.tags.add(TIT2(encoding=3, text=f"Radio Opname"))
            audio_file.tags.add(TPE1(encoding=3, text="Radio PrideSync"))
            audio_file.tags.add(TALB(encoding=3, text="Radio Opnames"))
            audio_file.tags.add(TDRC(encoding=3, text=str(datetime.now().year)))
            
            # Sla metadata op
            audio_file.save()
            
            self.logger.debug("Metadata toegevoegd aan opname")
            
        except Exception as e:
            self.logger.error(f"Metadata toevoegen gefaald: {e}")
    
    def _generate_filename(self, frequency=None):
        """
        Genereer bestandsnaam voor opname
        
        Args:
            frequency (float): Radio frequentie
            
        Returns:
            str: Gegenereerde bestandsnaam
        """
        try:
            # Timestamp
            timestamp = datetime.now().strftime(
                self.config['file_naming']['timestamp_format']
            )
            
            # Frequentie string
            freq_str = f"{frequency:.1f}" if frequency else "unknown"
            
            # Gebruik pattern uit config
            pattern = self.config['file_naming']['pattern']
            filename = pattern.format(
                timestamp=timestamp,
                frequency=freq_str
            )
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Bestandsnaam genereren gefaald: {e}")
            return f"radio_recording_{int(time.time())}.mp3"
    
    def is_recording(self):
        """
        Check of opname actief is
        
        Returns:
            bool: True als opname actief
        """
        return self.recording
    
    def get_recording_info(self):
        """
        Krijg informatie over huidige opname
        
        Returns:
            dict: Opname informatie
        """
        if not self.recording:
            return None
        
        return {
            'filename': self.current_filename,
            'duration': time.time() - getattr(self, 'start_time', time.time()),
            'buffer_size': len(self.audio_buffer) if self.audio_buffer else 0
        }
    
    def cleanup(self):
        """Cleanup audio resources"""
        try:
            if self.recording:
                self.stop_recording()
            
            if self.stream:
                self.stream.close()
                self.stream = None
            
            if self.audio:
                self.audio.terminate()
                self.audio = None
            
            self.logger.info("Audio recorder cleanup voltooid")
            
        except Exception as e:
            self.logger.error(f"Audio cleanup gefaald: {e}")
    
    def __del__(self):
        """Destructor"""
        self.cleanup()
