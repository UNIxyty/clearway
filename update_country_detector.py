#!/usr/bin/env python3
"""
Generate updated country_detector.py with complete mapping from JSON
"""

import json
from pathlib import Path
from build_country_mapping import build_complete_mapping

def generate_country_detector():
    """Generate the complete country_detector.py file"""
    mapping = build_complete_mapping()
    
    # Build the prefix mapping dictionary
    prefix_lines = []
    for country_name, data in sorted(mapping.items()):
        prefix = data['prefix']
        # Handle multiple prefixes (like Y for Australia)
        if isinstance(prefix, list):
            for p in prefix:
                prefix_lines.append(f"    '{p}': '{country_name}',")
        else:
            prefix_lines.append(f"    '{prefix}': '{country_name}',")
    
    # Build flag mapping
    flag_lines = []
    for country_name, data in sorted(mapping.items()):
        flag = data['flag']
        flag_lines.append(f"    '{country_name}': '{flag}',")
    
    detector_code = f'''#!/usr/bin/env python3
"""
Country detector based on aip_countries_full.json
Maps ICAO airport code prefixes to country names with flags
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ICAO airport code prefixes mapped to country names
# Generated from aip_countries_full.json
ICAO_PREFIXES = {{
{chr(10).join(prefix_lines)}
}}

# Country flag emojis
COUNTRY_FLAGS = {{
{chr(10).join(flag_lines)}
}}

# Load countries from JSON file
_countries_data = None

def load_countries_data():
    """Load countries data from JSON file"""
    global _countries_data
    if _countries_data is None:
        json_path = Path(__file__).parent / 'assets' / 'aip_countries_full.json'
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                _countries_data = json.load(f)
            logger.info(f"Loaded {{len(_countries_data)}} countries from JSON file")
        except Exception as e:
            logger.error(f"Failed to load countries JSON: {{e}}")
            _countries_data = []
    return _countries_data

def get_country_from_code(airport_code: str) -> Optional[Dict[str, str]]:
    """
    Detect country from airport code using ICAO prefixes
    
    Args:
        airport_code: Airport code (e.g., KJFK, LFBA, EETN, EVRA)
        
    Returns:
        Dictionary with country info or None if not found
        Format: {{'country': 'Country Name', 'region': 'REGION', 'code': 'PREFIX', 'flag': '🇺🇸'}}
    """
    airport_code = airport_code.upper().strip()
    
    if not airport_code or len(airport_code) < 3:
        return None
    
    # Check prefixes in order: 3-letter, 2-letter, 1-letter (longer matches take precedence)
    for prefix_len in [3, 2, 1]:
        if len(airport_code) >= prefix_len:
            prefix = airport_code[:prefix_len]
            if prefix in ICAO_PREFIXES:
                country_name = ICAO_PREFIXES[prefix]
                
                # Try to find this country in the JSON file for more details
                countries_data = load_countries_data()
                for country_data in countries_data:
                    if country_data.get('country', '').strip() == country_name:
                        flag_emoji = COUNTRY_FLAGS.get(country_name, '🏳️')
                        return {{
                            'country': country_data.get('country', country_name),
                            'region': country_data.get('region', 'UNKNOWN'),
                            'code': prefix,
                            'type': country_data.get('type', 'Unknown'),
                            'link': country_data.get('link', ''),
                            'flag': flag_emoji
                        }}
                
                # If not found in JSON, return basic info with flag
                flag_emoji = COUNTRY_FLAGS.get(country_name, '🏳️')
                return {{
                    'country': country_name,
                    'region': 'UNKNOWN',
                    'code': prefix,
                    'flag': flag_emoji
                }}
    
    return None

def get_country_name(airport_code: str) -> Optional[str]:
    """Get just the country name for an airport code"""
    country_info = get_country_from_code(airport_code)
    return country_info.get('country') if country_info else None
'''
    
    return detector_code

if __name__ == '__main__':
    code = generate_country_detector()
    output_path = Path(__file__).parent / 'country_detector.py'
    output_path.write_text(code, encoding='utf-8')
    print(f"Generated country_detector.py with {len(build_complete_mapping())} countries")

