#!/usr/bin/env python3
"""
Country detector based on aip_countries_full.json
Maps ICAO airport code prefixes to country names from the JSON file
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Standard ICAO airport code prefixes mapped to country names
# This is a comprehensive mapping based on ICAO location indicators
STANDARD_PREFIXES = {
    # North America
    'K': 'United States of America',
    'C': 'Canada',
    'M': 'Mexico',
    'TI': 'Costa Rica',
    'MS': 'El Salvador',
    'MG': 'Guatemala',
    'MH': 'Honduras',
    'MP': 'Panama',
    
    # Europe
    'E': 'Norway',  # EN, ES, etc.
    'EN': 'Norway',
    'ES': 'Sweden',
    'EF': 'Finland',
    'EK': 'Denmark',
    'BI': 'Iceland',
    'EG': 'United Kingdom',
    'EI': 'Ireland',
    'LF': 'France',
    'ED': 'Germany',
    'LS': 'Switzerland',
    'LO': 'Austria',
    'LOWW': 'Austria',
    'L': 'Spain',  # LE, etc.
    'LE': 'Spain',
    'LJ': 'Slovenia',
    'LD': 'Croatia',
    'LY': 'Serbia',
    'LZ': 'Bulgaria',
    'LH': 'Hungary',
    'LR': 'Romania',
    'LK': 'Czech Republic',
    'EP': 'Poland',
    'LKPR': 'Czech Republic',
    'LI': 'Italy',
    'LG': 'Greece',
    'LT': 'Turkey',
    'LP': 'Portugal',
    'EV': 'Latvia',
    'EE': 'Estonia',
    'EY': 'Lithuania',
    'LA': 'Albania',
    'LQ': 'Bosnia and Herzegovina',
    'LZBB': 'Bulgaria',
    'BK': 'Kosovo',
    'LJ': 'Slovenia',
    'LJLJ': 'Slovenia',
    'LZ': 'Slovakia',
    
    # Asia
    'VH': 'Hong Kong',
    'RC': 'Taiwan',
    'RJ': 'Japan',
    'RK': 'South Korea',
    'VT': 'Thailand',
    'WM': 'Malaysia',
    'WS': 'Singapore',
    'W': 'Indonesia',  # WIII, etc.
    'VI': 'India',
    'OP': 'Pakistan',
    'VG': 'Bangladesh',
    'VN': 'Nepal',
    'V': 'Sri Lanka',  # VCBI, etc.
    'OB': 'Bahrain',
    'OE': 'Saudi Arabia',
    'OM': 'United Arab Emirates',
    'OO': 'Oman',
    'OK': 'Kuwait',
    'LL': 'Israel',
    'OJ': 'Jordan',
    'OL': 'Lebanon',
    'OS': 'Syria',
    'OR': 'Iraq',
    'OI': 'Iran',
    'UG': 'Georgia',
    'UA': 'Kazakhstan',
    'UO': 'Kyrgyzstan',
    'UT': 'Tajikistan',
    'UT': 'Turkmenistan',
    'UZ': 'Uzbekistan',
    'ZM': 'Mongolia',
    
    # Africa
    'DA': 'Algeria',
    'DT': 'Tunisia',
    'HL': 'Libya',
    'HE': 'Egypt',
    'H': 'Ethiopia',  # HAAA, etc.
    'HA': 'Ethiopia',
    'HB': 'Switzerland',  # (conflict, but HB is Switzerland)
    'HC': 'Somalia',
    'HD': 'Djibouti',
    'F': 'South Africa',  # FAOR, etc.
    'FA': 'South Africa',
    'FB': 'Botswana',
    'FC': 'Republic of the Congo',
    'FD': 'Eswatini',
    'FE': 'Central African Republic',
    'FG': 'Equatorial Guinea',
    'FH': 'Saint Helena',
    'FI': 'Mauritius',
    'FK': 'Cameroon',
    'FL': 'Zambia',
    'FM': 'Comoros',
    'FN': 'Angola',
    'FO': 'Gabon',
    'FP': 'São Tomé and Príncipe',
    'FQ': 'Mozambique',
    'FS': 'Seychelles',
    'FT': 'Chad',
    'FV': 'Zimbabwe',
    'FW': 'Malawi',
    'FX': 'Lesotho',
    'FY': 'Namibia',
    'FZ': 'Democratic Republic of the Congo',
    'G': 'Senegal',  # GOOY, etc.
    'GO': 'Senegal',
    'GQ': 'Mauritania',
    'GS': 'Western Sahara',
    'GV': 'Cabo Verde',
    'HR': 'Rwanda',
    'HS': 'Sudan',
    'HT': 'Tanzania',
    'HU': 'Uganda',
    'FV': 'Zimbabwe',
    'DN': 'Nigeria',
    'DF': 'Burkina Faso',
    'DFOO': 'Burkina Faso',
    'DI': "Ivory Coast (Côte d'Ivoire)",
    'DXXX': "Ivory Coast (Côte d'Ivoire)",
    'DX': 'Togo',
    'DG': 'Ghana',
    'DFOO': 'Ghana',
    
    # South America
    'SA': 'Argentina',
    'SB': 'Brazil',
    'SC': 'Chile',
    'SE': 'Ecuador',
    'SK': 'Colombia',
    'SL': 'Bolivia',
    'SM': 'Suriname',
    'SO': 'French Guiana',
    'SP': 'Peru',
    'SU': 'Uruguay',
    'SV': 'Venezuela',
    'SY': 'Guyana',
    'S': 'Paraguay',  # SGAS, etc.
    
    # Australia and Oceania
    'Y': 'Australia',  # YSSY, etc.
    'YB': 'Australia',
    'YC': 'Australia',
    'YD': 'Australia',
    'YF': 'Australia',
    'YG': 'Australia',
    'YH': 'Australia',
    'YJ': 'Australia',
    'YK': 'Australia',
    'YL': 'Australia',
    'YM': 'Australia',
    'YN': 'Australia',
    'YO': 'Australia',
    'YP': 'Australia',
    'YQ': 'Australia',
    'YR': 'Australia',
    'YS': 'Australia',
    'YT': 'Australia',
    'YU': 'Australia',
    'YV': 'Australia',
    'YW': 'Australia',
    'YX': 'Australia',
    'YY': 'Australia',
    'YZ': 'Australia',
    'NZ': 'New Zealand',
    'AG': 'Solomon Islands',
    'AN': 'Nauru',
    'AY': 'Papua New Guinea',
    'NF': 'Fiji',
    'NG': 'Kiribati',
    'NI': 'Vanuatu',
    'NL': 'Wallis and Futuna',
    'NS': 'Samoa',
    'NT': 'French Polynesia',
    'NV': 'New Caledonia',
    'NW': 'New Caledonia',
    'NX': 'Tonga',
    'NZ': 'New Zealand',
}

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
            logger.info(f"Loaded {len(_countries_data)} countries from JSON file")
        except Exception as e:
            logger.error(f"Failed to load countries JSON: {e}")
            _countries_data = []
    return _countries_data

def get_country_from_code(airport_code: str) -> Optional[Dict[str, str]]:
    """
    Detect country from airport code using ICAO prefixes
    
    Args:
        airport_code: Airport code (e.g., KJFK, LFBA, EETN, EVRA)
        
    Returns:
        Dictionary with country info or None if not found
        Format: {'country': 'Country Name', 'region': 'REGION', 'code': 'PREFIX'}
    """
    airport_code = airport_code.upper().strip()
    
    if not airport_code or len(airport_code) < 3:
        return None
    
    # First, try to match against countries in the JSON file
    # by checking if any country has a matching airport code pattern
    countries_data = load_countries_data()
    
    # Check two-letter prefixes first (longer matches take precedence)
    for prefix_len in [3, 2, 1]:
        if len(airport_code) >= prefix_len:
            prefix = airport_code[:prefix_len]
            
            # Try standard prefixes first
            if prefix in STANDARD_PREFIXES:
                country_name = STANDARD_PREFIXES[prefix]
                
                # Try to find this country in the JSON file for more details
                for country_data in countries_data:
                    if country_data.get('country', '').upper() == country_name.upper():
                        return {
                            'country': country_data.get('country', country_name),
                            'region': country_data.get('region', 'UNKNOWN'),
                            'code': prefix,
                            'type': country_data.get('type', 'Unknown'),
                            'link': country_data.get('link', '')
                        }
                
                # If not found in JSON, return basic info
                return {
                    'country': country_name,
                    'region': 'UNKNOWN',
                    'code': prefix
                }
    
    return None

def get_country_name(airport_code: str) -> Optional[str]:
    """Get just the country name for an airport code"""
    country_info = get_country_from_code(airport_code)
    return country_info.get('country') if country_info else None

