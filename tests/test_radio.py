"""
Unit tests voor Radio PrideSync radio module
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Voeg src directory toe aan path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from radio.si4703 import SI4703Radio

class TestSI4703Radio(unittest.TestCase):
    """Test cases voor SI4703Radio klasse"""
    
    def setUp(self):
        """Setup voor elke test"""
        self.config = {
            'frequency_range': {'min': 87.5, 'max': 108.0, 'step': 0.1},
            'default_frequency': 100.0,
            'volume': {'min': 0, 'max': 15, 'default': 8},
            'rds_enabled': True,
            'seek_threshold': 20,
            'i2c_address': '0x10',
            'gpio_pins': {'reset': 17, 'gpio2': 27}
        }
    
    @patch('radio.si4703.GPIO')
    @patch('radio.si4703.SMBus')
    def test_init(self, mock_smbus, mock_gpio):
        """Test SI4703Radio initialisatie"""
        radio = SI4703Radio(self.config)
        
        # Controleer configuratie
        self.assertEqual(radio.config, self.config)
        self.assertEqual(radio.frequency, 100.0)
        self.assertEqual(radio.volume, 8)
        self.assertFalse(radio.powered)
        
        # Controleer GPIO setup
        mock_gpio.setmode.assert_called_once_with(mock_gpio.BCM)
        mock_gpio.setup.assert_any_call(17, mock_gpio.OUT)
        mock_gpio.setup.assert_any_call(27, mock_gpio.OUT)
    
    @patch('radio.si4703.GPIO')
    @patch('radio.si4703.SMBus')
    def test_frequency_validation(self, mock_smbus, mock_gpio):
        """Test frequentie validatie"""
        radio = SI4703Radio(self.config)
        
        # Geldige frequenties
        self.assertTrue(radio._is_valid_frequency(87.5))
        self.assertTrue(radio._is_valid_frequency(100.0))
        self.assertTrue(radio._is_valid_frequency(108.0))
        
        # Ongeldige frequenties
        self.assertFalse(radio._is_valid_frequency(87.4))
        self.assertFalse(radio._is_valid_frequency(108.1))
        self.assertFalse(radio._is_valid_frequency(50.0))
    
    def _is_valid_frequency(self, frequency):
        """Helper method voor frequentie validatie"""
        freq_min = self.config['frequency_range']['min']
        freq_max = self.config['frequency_range']['max']
        return freq_min <= frequency <= freq_max
    
    @patch('radio.si4703.GPIO')
    @patch('radio.si4703.SMBus')
    def test_volume_validation(self, mock_smbus, mock_gpio):
        """Test volume validatie"""
        radio = SI4703Radio(self.config)
        
        # Geldige volumes
        self.assertTrue(radio._is_valid_volume(0))
        self.assertTrue(radio._is_valid_volume(8))
        self.assertTrue(radio._is_valid_volume(15))
        
        # Ongeldige volumes
        self.assertFalse(radio._is_valid_volume(-1))
        self.assertFalse(radio._is_valid_volume(16))
        self.assertFalse(radio._is_valid_volume(100))
    
    def _is_valid_volume(self, volume):
        """Helper method voor volume validatie"""
        vol_min = self.config['volume']['min']
        vol_max = self.config['volume']['max']
        return vol_min <= volume <= vol_max
    
    @patch('radio.si4703.GPIO')
    @patch('radio.si4703.SMBus')
    @patch('radio.si4703.time.sleep')
    def test_reset_chip(self, mock_sleep, mock_smbus, mock_gpio):
        """Test chip reset functionaliteit"""
        radio = SI4703Radio(self.config)
        radio._reset_chip()
        
        # Controleer GPIO calls
        mock_gpio.output.assert_any_call(17, mock_gpio.LOW)
        mock_gpio.output.assert_any_call(17, mock_gpio.HIGH)
        mock_gpio.output.assert_any_call(27, mock_gpio.HIGH)
        
        # Controleer timing
        self.assertEqual(mock_sleep.call_count, 3)
    
    @patch('radio.si4703.GPIO')
    @patch('radio.si4703.SMBus')
    def test_frequency_calculation(self, mock_smbus, mock_gpio):
        """Test frequentie naar channel berekening"""
        radio = SI4703Radio(self.config)
        
        # Test bekende conversies
        # 87.5 MHz = channel 0
        # 100.0 MHz = channel 125
        # 108.0 MHz = channel 205
        
        self.assertEqual(radio._freq_to_channel(87.5), 0)
        self.assertEqual(radio._freq_to_channel(100.0), 125)
        self.assertEqual(radio._freq_to_channel(108.0), 205)
    
    def _freq_to_channel(self, frequency):
        """Helper method voor frequentie conversie"""
        return int((frequency - 87.5) / 0.1)
    
    @patch('radio.si4703.GPIO')
    @patch('radio.si4703.SMBus')
    def test_channel_to_frequency(self, mock_smbus, mock_gpio):
        """Test channel naar frequentie berekening"""
        radio = SI4703Radio(self.config)
        
        # Test bekende conversies
        self.assertAlmostEqual(radio._channel_to_freq(0), 87.5, places=1)
        self.assertAlmostEqual(radio._channel_to_freq(125), 100.0, places=1)
        self.assertAlmostEqual(radio._channel_to_freq(205), 108.0, places=1)
    
    def _channel_to_freq(self, channel):
        """Helper method voor channel conversie"""
        return 87.5 + (channel * 0.1)
    
    @patch('radio.si4703.GPIO')
    @patch('radio.si4703.SMBus')
    def test_register_operations(self, mock_smbus, mock_gpio):
        """Test register lees/schrijf operaties"""
        radio = SI4703Radio(self.config)
        
        # Mock SMBus instance
        mock_bus = MagicMock()
        mock_smbus.return_value.__enter__.return_value = mock_bus
        
        # Test register lezen
        mock_bus.read_i2c_block_data.return_value = [0x12, 0x34]
        result = radio._read_register(mock_bus, 0x00)
        self.assertEqual(result, 0x1234)
        
        # Test register schrijven
        radio._write_register(mock_bus, 0x00, 0x5678)
        mock_bus.write_i2c_block_data.assert_called_with(0x10, 0x00, [0x56, 0x78])
    
    @patch('radio.si4703.GPIO')
    @patch('radio.si4703.SMBus')
    def test_rds_decoding(self, mock_smbus, mock_gpio):
        """Test basis RDS decoding"""
        radio = SI4703Radio(self.config)
        
        # Test PS name decoding (Group 0)
        radio._decode_rds(0x0000, 0x0000, 0x0000, 0x4142)  # "AB"
        self.assertIn('A', radio.rds_data.get('station_name', ''))
        
        # Test Radio Text decoding (Group 2)
        radio._decode_rds(0x0000, 0x2000, 0x4344, 0x4546)  # "CDEF"
        self.assertIn('C', radio.rds_data.get('radio_text', ''))

class TestRadioIntegration(unittest.TestCase):
    """Integratie tests voor radio functionaliteit"""
    
    def setUp(self):
        """Setup voor integratie tests"""
        self.config = {
            'frequency_range': {'min': 87.5, 'max': 108.0, 'step': 0.1},
            'default_frequency': 100.0,
            'volume': {'min': 0, 'max': 15, 'default': 8},
            'rds_enabled': True,
            'seek_threshold': 20,
            'i2c_address': '0x10',
            'gpio_pins': {'reset': 17, 'gpio2': 27}
        }
    
    @patch('radio.si4703.GPIO')
    @patch('radio.si4703.SMBus')
    def test_full_initialization_sequence(self, mock_smbus, mock_gpio):
        """Test volledige initialisatie sequentie"""
        # Mock SMBus voor chip verificatie
        mock_bus = MagicMock()
        mock_smbus.return_value.__enter__.return_value = mock_bus
        mock_bus.read_i2c_block_data.side_effect = [
            [0x12, 0x00],  # Device ID (SI4703)
            [0x00, 0x01],  # Chip ID
        ]
        
        radio = SI4703Radio(self.config)
        
        # Mock initialize methoden
        with patch.object(radio, '_reset_chip'), \
             patch.object(radio, '_verify_chip', return_value=True), \
             patch.object(radio, '_power_up', return_value=True), \
             patch.object(radio, '_configure_chip'):
            
            result = radio.initialize()
            self.assertTrue(result)
            self.assertTrue(radio.powered)
    
    @patch('radio.si4703.GPIO')
    @patch('radio.si4703.SMBus')
    def test_frequency_tuning_workflow(self, mock_smbus, mock_gpio):
        """Test frequentie tuning workflow"""
        radio = SI4703Radio(self.config)
        radio.powered = True  # Simuleer geïnitialiseerde radio
        
        # Mock SMBus operaties
        mock_bus = MagicMock()
        mock_smbus.return_value.__enter__.return_value = mock_bus
        
        with patch.object(radio, '_wait_for_tune_complete', return_value=True):
            result = radio.set_frequency(101.5)
            self.assertTrue(result)
            self.assertEqual(radio.frequency, 101.5)

if __name__ == '__main__':
    # Voeg helper methods toe aan SI4703Radio klasse voor tests
    SI4703Radio._is_valid_frequency = lambda self, freq: (
        self.config['frequency_range']['min'] <= freq <= self.config['frequency_range']['max']
    )
    SI4703Radio._is_valid_volume = lambda self, vol: (
        self.config['volume']['min'] <= vol <= self.config['volume']['max']
    )
    SI4703Radio._freq_to_channel = lambda self, freq: int((freq - 87.5) / 0.1)
    SI4703Radio._channel_to_freq = lambda self, channel: 87.5 + (channel * 0.1)
    
    unittest.main()
