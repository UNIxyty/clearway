"""
Scraper Registry - Maps countries to their scrapers
"""

import logging

logger = logging.getLogger(__name__)

# Stub scraper registry - returns None for all scrapers
# This allows the app to work with just extracted AIP data

def get_country_from_code(airport_code: str) -> str:
    """Detect country from airport code prefix"""
    if not airport_code or len(airport_code) < 2:
        return None
    
    # Map of ICAO prefixes to countries
    PREFIX_MAP = {
        'K': 'USA',
        'LO': 'Austria',
        'LK': 'Czech Republic',
        'EK': 'Denmark',
        'EI': 'Ireland',
        'LI': 'Italy',
        'LM': 'Malta',
        'LG': 'Greece',
        'LB': 'Bulgaria',
        'OA': 'Afghanistan',
        'UB': 'Azerbaijan',
        'VQ': 'Bhutan',
        'MU': 'Cuba',
        'HD': 'Djibouti',
        'HA': 'Ethiopia',
        'OI': 'Iran',
        'HL': 'Libya',
        'VR': 'Maldives',
        'VN': 'Nepal',
        'FS': 'Seychelles',
        'FA': 'South Africa',
        'HS': 'Sudan',
        'WP': 'Timor',
        'TT': 'Trinidad and Tobago',
        'WB': 'Brunei',
        'TV': 'Saint Vincent and the Grenadines',
        'MT': 'Haiti',
        'LE': 'Andorra',
        'FN': 'Angola',
        'TAPA': 'Antigua and Barbuda',
        'VM': 'Macao',
    }
    
    # Try 4-letter prefix first
    if len(airport_code) >= 4:
        prefix_4 = airport_code[:4].upper()
        if prefix_4 in PREFIX_MAP:
            return PREFIX_MAP[prefix_4]
    
    # Try 2-letter prefix
    prefix_2 = airport_code[:2].upper()
    if prefix_2 in PREFIX_MAP:
        return PREFIX_MAP[prefix_2]
    
    # Try 1-letter prefix
    prefix_1 = airport_code[:1].upper()
    if prefix_1 in PREFIX_MAP:
        return PREFIX_MAP[prefix_1]
    
    return None

def get_scraper_instance(country: str):
    """Get scraper instance for a country - returns None (no scrapers available)"""
    logger.info(f"No scraper available for {country}, using extracted AIP data only")
    return None

def get_available_countries():
    """Get list of available countries - returns empty list (no scrapers)"""
    return []

