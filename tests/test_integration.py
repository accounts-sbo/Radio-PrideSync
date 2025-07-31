"""
Integratie tests voor Radio PrideSync
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import tempfile
import json
from pathlib import Path

# Voeg src directory toe aan path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

class TestRadioPrideSyncIntegration(unittest.TestCase):
    """Integratie tests voor volledige Radio PrideSync systeem"""
    
    def setUp(self):
        """Setup voor integratie tests"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock configuratie bestanden
        self.radio_config = {
            'frequency_range': {'min': 87.5, 'max': 108.0, 'step': 0.1},
            'default_frequency': 100.0,
            'volume': {'min': 0, 'max': 15, 'default': 8},
            'rds_enabled': True,
            'seek_threshold': 20,
            'i2c_address': '0x10',
            'gpio_pins': {'reset': 17, 'gpio2': 27}
        }
        
        self.audio_config = {
            'recording': {
                'format': 'mp3',
                'bitrate': 128,
                'sample_rate': 44100,
                'channels': 2,
                'output_directory': self.temp_dir
            },
            'playback': {
                'device': 'default',
                'buffer_size': 1024
            },
            'file_naming': {
                'pattern': 'radio_recording_{timestamp}_{frequency}MHz.mp3',
                'timestamp_format': '%Y%m%d_%H%M%S'
            }
        }
        
        # Maak tijdelijke config bestanden
        self.config_dir = Path(self.temp_dir) / 'config'
        self.config_dir.mkdir()
        
        with open(self.config_dir / 'radio_config.json', 'w') as f:
            json.dump(self.radio_config, f)
        
        with open(self.config_dir / 'audio_config.json', 'w') as f:
            json.dump(self.audio_config, f)
    
    def tearDown(self):
        """Cleanup na tests"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('main.SI4703Radio')
    @patch('main.AudioRecorder')
    @patch('builtins.open', create=True)
    @patch('json.load')
    def test_radio_pridesync_initialization(self, mock_json_load, mock_open, 
                                          mock_audio_recorder, mock_si4703):
        """Test RadioPrideSync klasse initialisatie"""
        # Mock configuratie laden
        mock_json_load.side_effect = [self.radio_config, self.audio_config]
        
        # Mock hardware klassen
        mock_radio = MagicMock()
        mock_si4703.return_value = mock_radio
        mock_radio.initialize.return_value = True
        
        mock_recorder = MagicMock()
        mock_audio_recorder.return_value = mock_recorder
        
        # Import en test RadioPrideSync
        from main import RadioPrideSync
        
        app = RadioPrideSync()
        
        # Controleer configuratie laden
        self.assertEqual(app.radio_config, self.radio_config)
        self.assertEqual(app.audio_config, self.audio_config)
        
        # Test hardware initialisatie
        result = app.initialize_hardware()
        self.assertTrue(result)
        
        # Controleer dat hardware geïnitialiseerd is
        mock_si4703.assert_called_once_with(self.radio_config)
        mock_audio_recorder.assert_called_once_with(self.audio_config)
        mock_radio.initialize.assert_called_once()
    
    @patch('main.SI4703Radio')
    @patch('main.AudioRecorder')
    @patch('builtins.open', create=True)
    @patch('json.load')
    def test_frequency_and_recording_workflow(self, mock_json_load, mock_open,
                                            mock_audio_recorder, mock_si4703):
        """Test volledige workflow: frequentie instellen en opname"""
        # Setup mocks
        mock_json_load.side_effect = [self.radio_config, self.audio_config]
        
        mock_radio = MagicMock()
        mock_si4703.return_value = mock_radio
        mock_radio.initialize.return_value = True
        mock_radio.set_frequency.return_value = True
        mock_radio.get_frequency.return_value = 101.5
        mock_radio.get_volume.return_value = 10
        mock_radio.get_rds_info.return_value = {
            'station_name': 'Test FM',
            'radio_text': 'Test Song'
        }
        
        mock_recorder = MagicMock()
        mock_audio_recorder.return_value = mock_recorder
        mock_recorder.is_recording.return_value = False
        mock_recorder.start_recording.return_value = 'test_recording.mp3'
        mock_recorder.stop_recording.return_value = 'test_recording.mp3'
        
        # Test workflow
        from main import RadioPrideSync
        
        app = RadioPrideSync()
        app.initialize_hardware()
        
        # Test frequentie instellen
        app.radio.set_frequency(101.5)
        mock_radio.set_frequency.assert_called_with(101.5)
        
        # Test opname starten
        filename = app.recorder.start_recording(101.5)
        mock_recorder.start_recording.assert_called_with(101.5)
        self.assertEqual(filename, 'test_recording.mp3')
        
        # Test opname stoppen
        result = app.recorder.stop_recording()
        mock_recorder.stop_recording.assert_called_once()
        self.assertEqual(result, 'test_recording.mp3')
    
    @patch('main.SI4703Radio')
    @patch('main.AudioRecorder')
    @patch('builtins.open', create=True)
    @patch('json.load')
    def test_error_handling(self, mock_json_load, mock_open,
                           mock_audio_recorder, mock_si4703):
        """Test error handling in verschillende scenario's"""
        # Test configuratie fout
        mock_json_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        from main import RadioPrideSync
        
        with self.assertRaises(SystemExit):
            RadioPrideSync()
        
        # Reset mocks voor hardware fout test
        mock_json_load.side_effect = [self.radio_config, self.audio_config]
        
        mock_radio = MagicMock()
        mock_si4703.return_value = mock_radio
        mock_radio.initialize.return_value = False  # Hardware fout
        
        app = RadioPrideSync()
        result = app.initialize_hardware()
        self.assertFalse(result)
    
    @patch('main.SI4703Radio')
    @patch('main.AudioRecorder')
    @patch('builtins.open', create=True)
    @patch('json.load')
    def test_signal_handling(self, mock_json_load, mock_open,
                           mock_audio_recorder, mock_si4703):
        """Test signal handling voor graceful shutdown"""
        # Setup mocks
        mock_json_load.side_effect = [self.radio_config, self.audio_config]
        
        mock_radio = MagicMock()
        mock_si4703.return_value = mock_radio
        mock_radio.initialize.return_value = True
        
        mock_recorder = MagicMock()
        mock_audio_recorder.return_value = mock_recorder
        mock_recorder.is_recording.return_value = True
        
        from main import RadioPrideSync
        
        app = RadioPrideSync()
        app.initialize_hardware()
        
        # Test signal handler
        with patch('sys.exit') as mock_exit:
            app.signal_handler(2, None)  # SIGINT
            
            # Controleer graceful shutdown
            mock_recorder.stop_recording.assert_called_once()
            mock_radio.power_down.assert_called_once()
            mock_exit.assert_called_once_with(0)

class TestSystemIntegration(unittest.TestCase):
    """Systeem-niveau integratie tests"""
    
    @patch('subprocess.run')
    def test_i2c_detection(self, mock_run):
        """Test I2C device detectie"""
        # Mock i2cdetect output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: 10 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
"""
        mock_run.return_value = mock_result
        
        from utils.helpers import check_i2c_device
        
        # Test SI4703 detectie
        result = check_i2c_device(0x10, bus=1)
        self.assertTrue(result)
        
        # Test niet-bestaand device
        result = check_i2c_device(0x20, bus=1)
        self.assertFalse(result)
    
    @patch('pyaudio.PyAudio')
    def test_audio_device_enumeration(self, mock_pyaudio):
        """Test audio device enumeratie"""
        # Mock PyAudio
        mock_audio = MagicMock()
        mock_pyaudio.return_value = mock_audio
        mock_audio.get_device_count.return_value = 2
        
        device_infos = [
            {
                'name': 'Built-in Audio',
                'maxInputChannels': 1,
                'maxOutputChannels': 2,
                'defaultSampleRate': 44100
            },
            {
                'name': 'USB Audio Device',
                'maxInputChannels': 2,
                'maxOutputChannels': 2,
                'defaultSampleRate': 48000
            }
        ]
        mock_audio.get_device_info_by_index.side_effect = device_infos
        
        from utils.helpers import get_audio_devices
        
        devices = get_audio_devices()
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]['name'], 'Built-in Audio')
        self.assertEqual(devices[1]['name'], 'USB Audio Device')
    
    def test_configuration_validation(self):
        """Test configuratie validatie"""
        from utils.helpers import validate_frequency
        
        freq_range = {'min': 87.5, 'max': 108.0}
        
        # Geldige frequenties
        self.assertTrue(validate_frequency(100.0, freq_range))
        self.assertTrue(validate_frequency(87.5, freq_range))
        self.assertTrue(validate_frequency(108.0, freq_range))
        
        # Ongeldige frequenties
        self.assertFalse(validate_frequency(87.4, freq_range))
        self.assertFalse(validate_frequency(108.1, freq_range))
        self.assertFalse(validate_frequency("invalid", freq_range))
    
    def test_file_operations(self):
        """Test bestandsoperaties"""
        from utils.helpers import safe_json_save, safe_json_load
        
        # Test data
        test_data = {'test': 'data', 'number': 42}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            # Test opslaan
            result = safe_json_save(test_data, temp_file)
            self.assertTrue(result)
            
            # Test laden
            loaded_data = safe_json_load(temp_file)
            self.assertEqual(loaded_data, test_data)
            
            # Test laden van niet-bestaand bestand
            missing_data = safe_json_load('nonexistent.json', default={'default': True})
            self.assertEqual(missing_data, {'default': True})
            
        finally:
            # Cleanup
            try:
                os.unlink(temp_file)
            except:
                pass

class TestPerformanceIntegration(unittest.TestCase):
    """Performance en resource integratie tests"""
    
    def test_memory_usage_monitoring(self):
        """Test geheugen gebruik monitoring"""
        from utils.helpers import get_disk_usage
        
        # Test schijfruimte info
        disk_info = get_disk_usage('.')
        
        self.assertIn('total', disk_info)
        self.assertIn('used', disk_info)
        self.assertIn('free', disk_info)
        self.assertIn('usage_percent', disk_info)
        
        # Controleer dat waarden logisch zijn
        self.assertGreaterEqual(disk_info['usage_percent'], 0)
        self.assertLessEqual(disk_info['usage_percent'], 100)
        self.assertEqual(
            disk_info['total'],
            disk_info['used'] + disk_info['free']
        )
    
    @patch('builtins.open', create=True)
    def test_raspberry_pi_info(self, mock_open):
        """Test Raspberry Pi informatie ophalen"""
        # Mock /proc/cpuinfo
        cpuinfo_content = """
processor	: 0
model name	: ARMv7 Processor rev 3 (v7l)
BogoMIPS	: 38.40
Features	: half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm crc32
CPU implementer	: 0x41
CPU architecture: 7
CPU variant	: 0x0
CPU part	: 0xd08
CPU revision	: 3

Hardware	: BCM2835
Revision	: a02082
Serial		: 00000000fedcba98
Model		: Raspberry Pi Zero 2 W Rev 1.0
"""
        
        mock_open.return_value.__enter__.return_value.read.return_value = cpuinfo_content
        
        from utils.helpers import get_raspberry_pi_info
        
        info = get_raspberry_pi_info()
        
        self.assertIn('model', info)
        self.assertIn('revision', info)
        self.assertIn('serial', info)
        self.assertEqual(info['model'], 'Raspberry Pi Zero 2 W Rev 1.0')

if __name__ == '__main__':
    unittest.main()
