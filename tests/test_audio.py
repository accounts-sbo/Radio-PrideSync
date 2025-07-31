"""
Unit tests voor Radio PrideSync audio module
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import tempfile
import os
from pathlib import Path

# Voeg src directory toe aan path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from audio.recorder import AudioRecorder

class TestAudioRecorder(unittest.TestCase):
    """Test cases voor AudioRecorder klasse"""
    
    def setUp(self):
        """Setup voor elke test"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
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
    
    def tearDown(self):
        """Cleanup na elke test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('audio.recorder.pyaudio')
    def test_init(self, mock_pyaudio):
        """Test AudioRecorder initialisatie"""
        recorder = AudioRecorder(self.config)
        
        # Controleer configuratie
        self.assertEqual(recorder.config, self.config)
        self.assertEqual(recorder.sample_rate, 44100)
        self.assertEqual(recorder.channels, 2)
        self.assertFalse(recorder.recording)
        self.assertIsNone(recorder.current_filename)
        
        # Controleer output directory
        self.assertTrue(Path(self.temp_dir).exists())
    
    @patch('audio.recorder.pyaudio')
    def test_filename_generation(self, mock_pyaudio):
        """Test bestandsnaam generatie"""
        recorder = AudioRecorder(self.config)
        
        # Test met frequentie
        filename = recorder._generate_filename(101.5)
        self.assertIn('101.5', filename)
        self.assertTrue(filename.endswith('.mp3'))
        self.assertIn('radio_recording_', filename)
        
        # Test zonder frequentie
        filename = recorder._generate_filename(None)
        self.assertIn('unknown', filename)
        self.assertTrue(filename.endswith('.mp3'))
    
    @patch('audio.recorder.pyaudio')
    def test_audio_device_detection(self, mock_pyaudio):
        """Test audio device detectie"""
        # Mock PyAudio
        mock_audio = MagicMock()
        mock_pyaudio.PyAudio.return_value = mock_audio
        mock_audio.get_device_count.return_value = 3
        
        # Mock device info
        device_infos = [
            {'name': 'Built-in Output', 'maxInputChannels': 0, 'maxOutputChannels': 2},
            {'name': 'USB Audio', 'maxInputChannels': 2, 'maxOutputChannels': 2},
            {'name': 'Built-in Input', 'maxInputChannels': 1, 'maxOutputChannels': 0}
        ]
        mock_audio.get_device_info_by_index.side_effect = device_infos
        
        recorder = AudioRecorder(self.config)
        device_index = recorder._find_input_device()
        
        # Moet USB Audio kiezen (index 1) omdat het "usb" in naam heeft
        self.assertEqual(device_index, 1)
    
    @patch('audio.recorder.pyaudio')
    @patch('audio.recorder.threading.Thread')
    def test_recording_start_stop(self, mock_thread, mock_pyaudio):
        """Test opname start en stop"""
        # Mock PyAudio
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio.PyAudio.return_value = mock_audio
        mock_audio.open.return_value = mock_stream
        
        recorder = AudioRecorder(self.config)
        
        # Mock initialisatie
        with patch.object(recorder, '_initialize_audio', return_value=True):
            # Start opname
            filename = recorder.start_recording(100.5)
            
            self.assertIsNotNone(filename)
            self.assertTrue(recorder.recording)
            self.assertEqual(recorder.current_filename, filename)
            mock_stream.start_stream.assert_called_once()
        
        # Stop opname
        with patch.object(recorder, '_save_recording'):
            result_filename = recorder.stop_recording()
            
            self.assertFalse(recorder.recording)
            self.assertEqual(result_filename, filename)
            mock_stream.stop_stream.assert_called_once()
    
    @patch('audio.recorder.pyaudio')
    def test_audio_callback(self, mock_pyaudio):
        """Test audio callback functionaliteit"""
        recorder = AudioRecorder(self.config)
        recorder.recording = True
        
        # Simuleer audio data
        test_data = b'\x00\x01\x02\x03\x04\x05\x06\x07'
        
        # Call callback
        result = recorder._audio_callback(test_data, 4, None, None)
        
        # Controleer dat data toegevoegd is aan buffer
        self.assertGreater(len(recorder.audio_buffer), 0)
        
        # Controleer return waarde
        self.assertEqual(result[0], test_data)
        self.assertEqual(result[1], mock_pyaudio.paContinue)
    
    @patch('audio.recorder.pyaudio')
    @patch('audio.recorder.AudioSegment')
    def test_audio_processing(self, mock_audiosegment, mock_pyaudio):
        """Test audio data verwerking"""
        recorder = AudioRecorder(self.config)
        recorder.current_filename = 'test.mp3'
        
        # Mock audio data in buffer
        import numpy as np
        test_audio = np.array([1, 2, 3, 4], dtype=np.int16)
        recorder.audio_buffer = test_audio.tolist()
        
        # Mock AudioSegment
        mock_segment = MagicMock()
        mock_audiosegment.return_value = mock_segment
        
        # Test chunk opslaan
        recorder._save_chunk()
        
        # Controleer AudioSegment aanroep
        mock_audiosegment.assert_called_once()
        mock_segment.export.assert_called_once()
        
        # Buffer moet leeg zijn na opslaan
        self.assertEqual(len(recorder.audio_buffer), 0)
    
    @patch('audio.recorder.pyaudio')
    def test_recording_info(self, mock_pyaudio):
        """Test opname informatie"""
        recorder = AudioRecorder(self.config)
        
        # Geen opname actief
        info = recorder.get_recording_info()
        self.assertIsNone(info)
        
        # Opname actief
        recorder.recording = True
        recorder.current_filename = 'test.mp3'
        recorder.audio_buffer = [1, 2, 3, 4]
        
        info = recorder.get_recording_info()
        self.assertIsNotNone(info)
        self.assertEqual(info['filename'], 'test.mp3')
        self.assertEqual(info['buffer_size'], 4)
        self.assertIn('duration', info)
    
    @patch('audio.recorder.pyaudio')
    def test_cleanup(self, mock_pyaudio):
        """Test cleanup functionaliteit"""
        # Mock PyAudio objecten
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio.PyAudio.return_value = mock_audio
        
        recorder = AudioRecorder(self.config)
        recorder.audio = mock_audio
        recorder.stream = mock_stream
        recorder.recording = True
        
        # Mock stop_recording
        with patch.object(recorder, 'stop_recording'):
            recorder.cleanup()
        
        # Controleer cleanup
        mock_stream.close.assert_called_once()
        mock_audio.terminate.assert_called_once()
        self.assertIsNone(recorder.stream)
        self.assertIsNone(recorder.audio)

class TestAudioUtilities(unittest.TestCase):
    """Test audio utility functies"""
    
    def setUp(self):
        """Setup voor utility tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'recording': {
                'format': 'mp3',
                'bitrate': 128,
                'sample_rate': 44100,
                'channels': 2,
                'output_directory': self.temp_dir
            },
            'file_naming': {
                'pattern': 'test_{timestamp}_{frequency}MHz.mp3',
                'timestamp_format': '%Y%m%d_%H%M%S'
            }
        }
    
    def tearDown(self):
        """Cleanup na elke test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('audio.recorder.pyaudio')
    def test_file_naming_patterns(self, mock_pyaudio):
        """Test verschillende bestandsnaam patronen"""
        recorder = AudioRecorder(self.config)
        
        # Test met frequentie
        filename = recorder._generate_filename(95.5)
        self.assertIn('95.5', filename)
        self.assertTrue(filename.startswith('test_'))
        
        # Test timestamp format
        import re
        timestamp_pattern = r'\d{8}_\d{6}'
        self.assertTrue(re.search(timestamp_pattern, filename))
    
    @patch('audio.recorder.pyaudio')
    def test_audio_format_validation(self, mock_pyaudio):
        """Test audio format validatie"""
        recorder = AudioRecorder(self.config)
        
        # Controleer configuratie waarden
        self.assertEqual(recorder.sample_rate, 44100)
        self.assertEqual(recorder.channels, 2)
        self.assertEqual(recorder.chunk_size, 1024)
        
        # Test geldige sample rates
        valid_rates = [22050, 44100, 48000]
        for rate in valid_rates:
            test_config = self.config.copy()
            test_config['recording']['sample_rate'] = rate
            test_recorder = AudioRecorder(test_config)
            self.assertEqual(test_recorder.sample_rate, rate)

class TestAudioIntegration(unittest.TestCase):
    """Integratie tests voor audio functionaliteit"""
    
    def setUp(self):
        """Setup voor integratie tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
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
    
    def tearDown(self):
        """Cleanup na integratie tests"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('audio.recorder.pyaudio')
    @patch('audio.recorder.AudioSegment')
    @patch('audio.recorder.threading.Thread')
    def test_full_recording_workflow(self, mock_thread, mock_audiosegment, mock_pyaudio):
        """Test volledige opname workflow"""
        # Mock PyAudio
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio.PyAudio.return_value = mock_audio
        mock_audio.open.return_value = mock_stream
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_device_info_by_index.return_value = {
            'name': 'Test Device',
            'maxInputChannels': 2,
            'maxOutputChannels': 0
        }
        
        # Mock AudioSegment
        mock_segment = MagicMock()
        mock_audiosegment.return_value = mock_segment
        
        recorder = AudioRecorder(self.config)
        
        # Start opname
        filename = recorder.start_recording(101.1)
        self.assertIsNotNone(filename)
        self.assertTrue(recorder.recording)
        
        # Simuleer audio data
        import numpy as np
        test_data = np.array([100, 200, 300, 400], dtype=np.int16)
        recorder.audio_buffer = test_data.tolist()
        
        # Stop opname
        result_filename = recorder.stop_recording()
        self.assertEqual(result_filename, filename)
        self.assertFalse(recorder.recording)
        
        # Controleer dat export aangeroepen is
        mock_segment.export.assert_called()

if __name__ == '__main__':
    unittest.main()
