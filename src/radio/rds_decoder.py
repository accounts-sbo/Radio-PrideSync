"""
RDS (Radio Data System) Decoder voor SI4703
Decodeert RDS informatie van FM radio stations
"""

import logging
from typing import Dict, Optional, List

class RDSDecoder:
    """RDS data decoder voor FM radio"""
    
    def __init__(self):
        """Initialiseer RDS decoder"""
        self.logger = logging.getLogger(__name__)
        
        # RDS data storage
        self.program_service = [''] * 8  # PS name (8 characters)
        self.radio_text = [''] * 64      # Radio text (64 characters)
        self.program_type = 0            # PTY code
        self.traffic_program = False     # TP flag
        self.traffic_announcement = False # TA flag
        self.music_speech = False        # M/S flag
        
        # Decoding state
        self.ps_segments = [False] * 4   # PS segment received flags
        self.rt_segments = [False] * 16  # RT segment received flags
        self.rt_ab_flag = None           # RT A/B flag
        
        # Program Type Names (PTY)
        self.pty_names = {
            0: "None", 1: "News", 2: "Current Affairs", 3: "Information",
            4: "Sport", 5: "Education", 6: "Drama", 7: "Culture",
            8: "Science", 9: "Varied", 10: "Pop Music", 11: "Rock Music",
            12: "Easy Listening", 13: "Light Classical", 14: "Serious Classical",
            15: "Other Music", 16: "Weather", 17: "Finance", 18: "Children's",
            19: "Social Affairs", 20: "Religion", 21: "Phone In", 22: "Travel",
            23: "Leisure", 24: "Jazz Music", 25: "Country Music", 26: "National Music",
            27: "Oldies Music", 28: "Folk Music", 29: "Documentary", 30: "Alarm Test",
            31: "Alarm"
        }
        
        self.logger.debug("RDS decoder geïnitialiseerd")
    
    def decode_group(self, rdsa: int, rdsb: int, rdsc: int, rdsd: int) -> Dict:
        """
        Decodeer RDS groep
        
        Args:
            rdsa, rdsb, rdsc, rdsd (int): RDS register waarden
            
        Returns:
            dict: Gedecodeerde RDS informatie
        """
        try:
            # Extract group type en version
            group_type = (rdsb >> 12) & 0x0F
            version = (rdsb >> 11) & 0x01  # 0=A, 1=B
            
            self.logger.debug(f"RDS Group {group_type}{chr(65+version)}: "
                            f"A={rdsa:04X} B={rdsb:04X} C={rdsc:04X} D={rdsd:04X}")
            
            # Decode based on group type
            if group_type == 0:
                return self._decode_group_0(rdsa, rdsb, rdsc, rdsd, version)
            elif group_type == 1:
                return self._decode_group_1(rdsa, rdsb, rdsc, rdsd, version)
            elif group_type == 2:
                return self._decode_group_2(rdsa, rdsb, rdsc, rdsd, version)
            elif group_type == 4:
                return self._decode_group_4(rdsa, rdsb, rdsc, rdsd, version)
            else:
                self.logger.debug(f"Onbekend RDS group type: {group_type}")
                return {}
                
        except Exception as e:
            self.logger.error(f"RDS decode fout: {e}")
            return {}
    
    def _decode_group_0(self, rdsa: int, rdsb: int, rdsc: int, rdsd: int, version: int) -> Dict:
        """
        Decodeer Group 0 - Program Service Name en basis info
        
        Returns:
            dict: PS name en basis RDS info
        """
        # Program Identification (PI) code
        pi_code = rdsa
        
        # Program Type (PTY)
        self.program_type = (rdsb >> 5) & 0x1F
        
        # Traffic Program (TP) en Traffic Announcement (TA)
        self.traffic_program = bool(rdsb & 0x0400)
        self.traffic_announcement = bool(rdsb & 0x0010)
        
        # Music/Speech (M/S)
        self.music_speech = bool(rdsb & 0x0008)
        
        # PS segment address
        ps_segment = rdsb & 0x03
        
        # Extract PS characters from RDS D register
        char1 = chr((rdsd >> 8) & 0xFF) if (rdsd >> 8) & 0xFF >= 32 else ' '
        char2 = chr(rdsd & 0xFF) if rdsd & 0xFF >= 32 else ' '
        
        # Store PS characters
        self.program_service[ps_segment * 2] = char1
        self.program_service[ps_segment * 2 + 1] = char2
        self.ps_segments[ps_segment] = True
        
        # Alternative Frequency (AF) info in Group 0A
        af_info = []
        if version == 0:  # Group 0A
            af1 = (rdsc >> 8) & 0xFF
            af2 = rdsc & 0xFF
            
            if 1 <= af1 <= 204:
                af_freq = 87.5 + (af1 - 1) * 0.1
                af_info.append(af_freq)
            
            if 1 <= af2 <= 204:
                af_freq = 87.5 + (af2 - 1) * 0.1
                af_info.append(af_freq)
        
        result = {
            'group_type': '0A' if version == 0 else '0B',
            'pi_code': f"{pi_code:04X}",
            'program_type': self.pty_names.get(self.program_type, f"PTY {self.program_type}"),
            'traffic_program': self.traffic_program,
            'traffic_announcement': self.traffic_announcement,
            'music_speech': 'Music' if self.music_speech else 'Speech',
            'ps_segment': ps_segment,
            'ps_chars': char1 + char2
        }
        
        if af_info:
            result['alternative_frequencies'] = af_info
        
        # Check if complete PS name is received
        if all(self.ps_segments):
            ps_name = ''.join(self.program_service).strip()
            if ps_name:
                result['station_name'] = ps_name
                self.logger.info(f"Complete PS name: {ps_name}")
        
        return result
    
    def _decode_group_1(self, rdsa: int, rdsb: int, rdsc: int, rdsd: int, version: int) -> Dict:
        """
        Decodeer Group 1 - Program Item Number en Slow Labeling
        
        Returns:
            dict: Program item informatie
        """
        # Program Item Number (PIN)
        pin = rdsc if version == 0 else None
        
        # Slow Labeling Codes
        slow_labeling = rdsd if version == 0 else None
        
        result = {
            'group_type': '1A' if version == 0 else '1B',
            'pi_code': f"{rdsa:04X}"
        }
        
        if pin is not None:
            result['program_item_number'] = pin
        
        if slow_labeling is not None:
            result['slow_labeling'] = f"{slow_labeling:04X}"
        
        return result
    
    def _decode_group_2(self, rdsa: int, rdsb: int, rdsc: int, rdsd: int, version: int) -> Dict:
        """
        Decodeer Group 2 - Radio Text
        
        Returns:
            dict: Radio text informatie
        """
        # Radio Text A/B flag
        rt_ab = bool(rdsb & 0x0010)
        
        # Check for A/B flag change (indicates new radio text)
        if self.rt_ab_flag is not None and self.rt_ab_flag != rt_ab:
            self.logger.debug("RT A/B flag changed, clearing radio text")
            self.radio_text = [''] * 64
            self.rt_segments = [False] * 16
        
        self.rt_ab_flag = rt_ab
        
        # Text segment address
        rt_segment = rdsb & 0x0F
        
        if version == 0:  # Group 2A - 4 characters
            # Extract 4 characters from RDS C and D registers
            chars = [
                chr((rdsc >> 8) & 0xFF) if (rdsc >> 8) & 0xFF >= 32 else ' ',
                chr(rdsc & 0xFF) if rdsc & 0xFF >= 32 else ' ',
                chr((rdsd >> 8) & 0xFF) if (rdsd >> 8) & 0xFF >= 32 else ' ',
                chr(rdsd & 0xFF) if rdsd & 0xFF >= 32 else ' '
            ]
            
            # Store characters
            for i, char in enumerate(chars):
                if rt_segment * 4 + i < 64:
                    self.radio_text[rt_segment * 4 + i] = char
            
        else:  # Group 2B - 2 characters
            # Extract 2 characters from RDS D register only
            chars = [
                chr((rdsd >> 8) & 0xFF) if (rdsd >> 8) & 0xFF >= 32 else ' ',
                chr(rdsd & 0xFF) if rdsd & 0xFF >= 32 else ' '
            ]
            
            # Store characters
            for i, char in enumerate(chars):
                if rt_segment * 2 + i < 32:  # Group 2B uses 32 chars max
                    self.radio_text[rt_segment * 2 + i] = char
        
        self.rt_segments[rt_segment] = True
        
        result = {
            'group_type': '2A' if version == 0 else '2B',
            'pi_code': f"{rdsa:04X}",
            'rt_ab_flag': rt_ab,
            'rt_segment': rt_segment,
            'rt_chars': ''.join(chars)
        }
        
        # Check for complete radio text
        max_segments = 16 if version == 0 else 8
        if sum(self.rt_segments[:max_segments]) >= max_segments // 2:  # At least half received
            rt_text = ''.join(self.radio_text).strip()
            # Look for end marker (carriage return)
            if '\r' in rt_text:
                rt_text = rt_text[:rt_text.index('\r')]
            
            if rt_text:
                result['radio_text'] = rt_text
                self.logger.info(f"Radio Text: {rt_text}")
        
        return result
    
    def _decode_group_4(self, rdsa: int, rdsb: int, rdsc: int, rdsd: int, version: int) -> Dict:
        """
        Decodeer Group 4 - Clock Time en Date
        
        Returns:
            dict: Tijd en datum informatie
        """
        if version == 0:  # Group 4A
            # Modified Julian Day (MJD)
            mjd = ((rdsb & 0x03) << 15) | ((rdsc >> 1) & 0x7FFF)
            
            # Hour and minute
            hour = ((rdsc & 0x01) << 4) | ((rdsd >> 12) & 0x0F)
            minute = (rdsd >> 6) & 0x3F
            
            # Local time offset
            offset_sign = (rdsd >> 5) & 0x01
            offset = rdsd & 0x1F
            
            # Convert MJD to date
            if mjd > 0:
                # Simplified MJD to date conversion
                year = int((mjd - 15078.2) / 365.25)
                month = int((mjd - 14956.1 - int(year * 365.25)) / 30.6001)
                day = mjd - 14956 - int(year * 365.25) - int(month * 30.6001)
                
                if month > 13:
                    month -= 13
                    year += 1
                else:
                    month -= 1
                
                year += 1900
                
                result = {
                    'group_type': '4A',
                    'pi_code': f"{rdsa:04X}",
                    'date': f"{year:04d}-{month:02d}-{day:02d}",
                    'time': f"{hour:02d}:{minute:02d}",
                    'utc_offset': f"{'+' if offset_sign else '-'}{offset * 0.5:.1f}h"
                }
                
                self.logger.info(f"RDS Clock: {result['date']} {result['time']} UTC{result['utc_offset']}")
                return result
        
        return {
            'group_type': '4A' if version == 0 else '4B',
            'pi_code': f"{rdsa:04X}"
        }
    
    def get_current_info(self) -> Dict:
        """
        Krijg huidige RDS informatie
        
        Returns:
            dict: Complete RDS informatie
        """
        info = {}
        
        # Station name (PS)
        ps_name = ''.join(self.program_service).strip()
        if ps_name:
            info['station_name'] = ps_name
        
        # Radio text (RT)
        rt_text = ''.join(self.radio_text).strip()
        if '\r' in rt_text:
            rt_text = rt_text[:rt_text.index('\r')]
        if rt_text:
            info['radio_text'] = rt_text
        
        # Program type
        if self.program_type > 0:
            info['program_type'] = self.pty_names.get(self.program_type, f"PTY {self.program_type}")
        
        # Traffic info
        if self.traffic_program:
            info['traffic_program'] = True
        if self.traffic_announcement:
            info['traffic_announcement'] = True
        
        # Music/Speech
        info['content_type'] = 'Music' if self.music_speech else 'Speech'
        
        return info
    
    def reset(self):
        """Reset alle RDS data"""
        self.program_service = [''] * 8
        self.radio_text = [''] * 64
        self.program_type = 0
        self.traffic_program = False
        self.traffic_announcement = False
        self.music_speech = False
        self.ps_segments = [False] * 4
        self.rt_segments = [False] * 16
        self.rt_ab_flag = None
        
        self.logger.debug("RDS data gereset")
    
    def get_completion_status(self) -> Dict:
        """
        Krijg status van RDS data completeness
        
        Returns:
            dict: Completion status
        """
        ps_complete = all(self.ps_segments)
        rt_complete = sum(self.rt_segments[:16]) >= 8  # At least half
        
        return {
            'ps_complete': ps_complete,
            'ps_segments_received': sum(self.ps_segments),
            'rt_complete': rt_complete,
            'rt_segments_received': sum(self.rt_segments),
            'has_program_type': self.program_type > 0
        }
