"""
Helper functies voor Radio PrideSync
"""

import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

def validate_frequency(frequency, freq_range):
    """
    Valideer radio frequentie
    
    Args:
        frequency (float): Frequentie in MHz
        freq_range (dict): Frequentie bereik met min/max
        
    Returns:
        bool: True als geldig
    """
    try:
        freq = float(frequency)
        return freq_range['min'] <= freq <= freq_range['max']
    except (ValueError, TypeError):
        return False

def format_frequency(frequency):
    """
    Formatteer frequentie voor weergave
    
    Args:
        frequency (float): Frequentie in MHz
        
    Returns:
        str: Geformatteerde frequentie
    """
    try:
        return f"{float(frequency):.1f} MHz"
    except (ValueError, TypeError):
        return "Unknown MHz"

def format_duration(seconds):
    """
    Formatteer tijdsduur
    
    Args:
        seconds (float): Tijdsduur in seconden
        
    Returns:
        str: Geformatteerde tijdsduur
    """
    try:
        duration = timedelta(seconds=int(seconds))
        
        # Format als HH:MM:SS
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
            
    except (ValueError, TypeError):
        return "00:00"

def format_file_size(size_bytes):
    """
    Formatteer bestandsgrootte
    
    Args:
        size_bytes (int): Grootte in bytes
        
    Returns:
        str: Geformatteerde grootte
    """
    try:
        size = float(size_bytes)
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        
        return f"{size:.1f} TB"
        
    except (ValueError, TypeError):
        return "0 B"

def get_disk_usage(path='.'):
    """
    Krijg schijfruimte informatie
    
    Args:
        path (str): Pad om te controleren
        
    Returns:
        dict: Schijfruimte info (total, used, free)
    """
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        
        return {
            'total': total,
            'used': used,
            'free': free,
            'total_str': format_file_size(total),
            'used_str': format_file_size(used),
            'free_str': format_file_size(free),
            'usage_percent': (used / total) * 100 if total > 0 else 0
        }
        
    except Exception:
        return {
            'total': 0,
            'used': 0,
            'free': 0,
            'total_str': '0 B',
            'used_str': '0 B',
            'free_str': '0 B',
            'usage_percent': 0
        }

def check_i2c_device(address, bus=1):
    """
    Controleer of I2C device aanwezig is
    
    Args:
        address (int): I2C adres (bijv. 0x10)
        bus (int): I2C bus nummer
        
    Returns:
        bool: True als device gevonden
    """
    try:
        result = subprocess.run(
            ['i2cdetect', '-y', str(bus)],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Parse i2cdetect output
            hex_addr = f"{address:02x}"
            return hex_addr in result.stdout.lower()
        
        return False
        
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False

def get_raspberry_pi_info():
    """
    Krijg Raspberry Pi informatie
    
    Returns:
        dict: RPi informatie
    """
    info = {
        'model': 'Unknown',
        'revision': 'Unknown',
        'serial': 'Unknown',
        'temperature': None
    }
    
    try:
        # CPU info
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if 'Model' in line:
                    info['model'] = line.split(':')[1].strip()
                elif 'Revision' in line:
                    info['revision'] = line.split(':')[1].strip()
                elif 'Serial' in line:
                    info['serial'] = line.split(':')[1].strip()
        
        # Temperatuur
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp_millidegrees = int(f.read().strip())
                info['temperature'] = temp_millidegrees / 1000.0
        except:
            pass
            
    except Exception:
        pass
    
    return info

def safe_json_load(file_path, default=None):
    """
    Veilig JSON bestand laden
    
    Args:
        file_path (str): Pad naar JSON bestand
        default: Standaard waarde bij fout
        
    Returns:
        dict: JSON data of default waarde
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, Exception):
        return default if default is not None else {}

def safe_json_save(data, file_path):
    """
    Veilig JSON bestand opslaan
    
    Args:
        data: Data om op te slaan
        file_path (str): Pad naar JSON bestand
        
    Returns:
        bool: True als succesvol
    """
    try:
        # Maak directory als nodig
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Schrijf naar tijdelijk bestand eerst
        temp_path = f"{file_path}.tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Verplaats naar finale locatie (atomisch)
        os.rename(temp_path, file_path)
        return True
        
    except Exception:
        # Cleanup tijdelijk bestand
        try:
            os.remove(f"{file_path}.tmp")
        except:
            pass
        return False

def cleanup_old_files(directory, max_age_days=7, pattern="*.log"):
    """
    Ruim oude bestanden op
    
    Args:
        directory (str): Directory om op te ruimen
        max_age_days (int): Maximale leeftijd in dagen
        pattern (str): Bestandspatroon
        
    Returns:
        int: Aantal verwijderde bestanden
    """
    try:
        directory = Path(directory)
        if not directory.exists():
            return 0
        
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        removed_count = 0
        
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    removed_count += 1
                except:
                    pass
        
        return removed_count
        
    except Exception:
        return 0

def get_audio_devices():
    """
    Krijg lijst van beschikbare audio devices
    
    Returns:
        list: Audio devices info
    """
    devices = []
    
    try:
        import pyaudio
        
        audio = pyaudio.PyAudio()
        device_count = audio.get_device_count()
        
        for i in range(device_count):
            try:
                device_info = audio.get_device_info_by_index(i)
                devices.append({
                    'index': i,
                    'name': device_info['name'],
                    'max_input_channels': device_info['maxInputChannels'],
                    'max_output_channels': device_info['maxOutputChannels'],
                    'default_sample_rate': device_info['defaultSampleRate']
                })
            except:
                pass
        
        audio.terminate()
        
    except ImportError:
        pass
    except Exception:
        pass
    
    return devices

def test_audio_input(device_index=None, duration=1.0):
    """
    Test audio input device
    
    Args:
        device_index (int): Device index (None voor default)
        duration (float): Test duur in seconden
        
    Returns:
        dict: Test resultaten
    """
    try:
        import pyaudio
        import numpy as np
        
        audio = pyaudio.PyAudio()
        
        # Test parameters
        sample_rate = 44100
        chunk_size = 1024
        
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=chunk_size
        )
        
        # Record test data
        frames = []
        for _ in range(int(sample_rate * duration / chunk_size)):
            data = stream.read(chunk_size)
            frames.append(np.frombuffer(data, dtype=np.int16))
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # Analyze audio
        audio_data = np.concatenate(frames)
        rms = np.sqrt(np.mean(audio_data**2))
        max_amplitude = np.max(np.abs(audio_data))
        
        return {
            'success': True,
            'rms_level': float(rms),
            'max_amplitude': float(max_amplitude),
            'has_signal': rms > 100  # Threshold voor signaal detectie
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'rms_level': 0,
            'max_amplitude': 0,
            'has_signal': False
        }
