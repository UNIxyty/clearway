#!/usr/bin/env python3
"""
Dynamic scraper registry that automatically loads and maps country scrapers
"""

import importlib
import logging
import re
from pathlib import Path
from typing import Dict, Optional, Type

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ICAO airport code prefixes mapped to countries
# Format: prefix -> (country_name, module_name, class_name)
AIRPORT_CODE_PREFIXES = {
    # USA
    'K': ('USA', 'airport_scraper', 'AirportScraper'),
    
    # France
    'LF': ('FRANCE', 'france_aip_scraper', 'FranceAIPScraper'),
    
    # Estonia
    'EE': ('ESTONIA', 'estonia_aip_scraper_playwright', 'EstoniaAIPScraperPlaywright'),
    
    # Finland
    'EF': ('FINLAND', 'finland_aip_scraper_playwright', 'FinlandAIPScraperPlaywright'),
    
    # Latvia
    'EV': ('LATVIA', 'latvia_aip_scraper_playwright', 'LatviaAIPScraperPlaywright'),
    
    # Albania
    'LA': ('ALBANIA', 'albania_aip_scraper_playwright', 'AlbaniaAIPScraperPlaywright'),
    
    # Bahrain
    'OB': ('BAHRAIN', 'bahrain_aip_scraper_playwright', 'BahrainAIPScraperPlaywright'),
    
    # Bosnia and Herzegovina
    'LQ': ('BOSNIA_AND_HERZEGOVINA', 'bosnia_and_herzegovina_aip_scraper_playwright', 'BosniaAndHerzegovinaAIPScraperPlaywright'),
    
    # Cabo Verde
    'GV': ('CABO_VERDE', 'cabo_verde_aip_scraper_playwright', 'CaboVerdeAIPScraperPlaywright'),
    
    # Chile
    'SC': ('CHILE', 'chile_aip_scraper_playwright', 'ChileAIPScraperPlaywright'),
    
    # Costa Rica
    'MR': ('COSTA_RICA', 'costa_rica_aip_scraper_playwright', 'CostaRicaAIPScraperPlaywright'),
    
    # Croatia
    'LD': ('CROATIA', 'croatia_aip_scraper_playwright', 'CroatiaAIPScraperPlaywright'),
    
    # Ecuador
    'SE': ('ECUADOR', 'ecuador_aip_scraper_playwright', 'EcuadorAIPScraperPlaywright'),
    
    # El Salvador
    'MS': ('EL_SALVADOR', 'el_salvador_aip_scraper_playwright', 'ElSalvadorAIPScraperPlaywright'),
    
    # Georgia
    'UG': ('GEORGIA', 'georgia_aip_scraper_playwright', 'GeorgiaAIPScraperPlaywright'),
    
    # Guatemala
    'MG': ('GUATEMALA', 'guatemala_aip_scraper_playwright', 'GuatemalaAIPScraperPlaywright'),
    
    # Honduras
    'MH': ('HONDURAS', 'honduras_aip_scraper_playwright', 'HondurasAIPScraperPlaywright'),
    
    # Hong Kong
    'VH': ('HONG_KONG', 'hong_kong_aip_scraper_playwright', 'HongKongAIPScraperPlaywright'),
    
    # Hungary
    'LH': ('HUNGARY', 'hungary_aip_scraper_playwright', 'HungaryAIPScraperPlaywright'),
    
    # India
    'VI': ('INDIA', 'india_aip_scraper_playwright', 'IndiaAIPScraperPlaywright'),
    
    # Israel
    'LL': ('ISRAEL', 'israel_aip_scraper_playwright', 'IsraelAIPScraperPlaywright'),
    
    # Kazakhstan
    'UA': ('KAZAKHSTAN', 'kazakhstan_aip_scraper_playwright', 'KazakhstanAIPScraperPlaywright'),
    
    # Kosovo
    'BK': ('KOSOVO', 'kosovo_aip_scraper_playwright', 'KosovoAIPScraperPlaywright'),
    
    # Kyrgyzstan
    'UO': ('KYRGYZSTAN', 'kyrgyzstan_aip_scraper_playwright', 'KyrgyzstanAIPScraperPlaywright'),
    
    # Malaysia
    'WM': ('MALAYSIA', 'malaysia_aip_scraper_playwright', 'MalaysiaAIPScraperPlaywright'),
    
    # Mongolia
    'ZM': ('MONGOLIA', 'mongolia_aip_scraper_playwright', 'MongoliaAIPScraperPlaywright'),
    
    # Norway
    'EN': ('NORWAY', 'norway_aip_scraper_playwright', 'NorwayAIPScraperPlaywright'),
    
    # Oman
    'OO': ('OMAN', 'oman_aip_scraper_playwright', 'OmanAIPScraperPlaywright'),
    
    # Poland
    'EP': ('POLAND', 'poland_aip_scraper_playwright', 'PolandAIPScraperPlaywright'),
    
    # Portugal
    'LP': ('PORTUGAL', 'portugal_aip_scraper_playwright', 'PortugalAIPScraperPlaywright'),
    
    # Saudi Arabia
    'OE': ('SAUDI_ARABIA', 'saudi_arabia_aip_scraper_playwright', 'SaudiArabiaAIPScraperPlaywright'),
    
    # Singapore
    'WS': ('SINGAPORE', 'singapore_aip_scraper_playwright', 'SingaporeAIPScraperPlaywright'),
    
    # South Korea
    'RK': ('SOUTH_KOREA', 'south_korea_aip_scraper_playwright', 'SouthKoreaAIPScraperPlaywright'),
    
    # Sweden
    'ES': ('SWEDEN', 'sweden_aip_scraper_playwright', 'SwedenAIPScraperPlaywright'),
    
    # Taiwan
    'RC': ('TAIWAN', 'taiwan_aip_scraper_playwright', 'TaiwanAIPScraperPlaywright'),
    
    # Thailand
    'VT': ('THAILAND', 'thailand_aip_scraper_playwright', 'ThailandAIPScraperPlaywright'),
    
    # Ukraine
    'UK': ('UKRAINE', 'ukraine_aip_scraper_playwright', 'UkraineAIPScraperPlaywright'),
    
    # United Arab Emirates
    'OM': ('UNITED_ARAB_EMIRATES', 'united_arab_emirates_aip_scraper_playwright', 'UnitedArabEmiratesAIPScraperPlaywright'),
    
    # United Kingdom
    'EG': ('UNITED_KINGDOM', 'united_kingdom_aip_scraper_playwright', 'UnitedKingdomAIPScraperPlaywright'),
}

# Cache for loaded scraper classes
_scraper_cache: Dict[str, Type] = {}


def slugify_country(country: str) -> str:
    """Convert country name to module slug"""
    return re.sub(r"[^a-z0-9]+", "_", country.lower()).strip("_")


def get_country_from_code(airport_code: str) -> Optional[str]:
    """
    Detect country from airport code using ICAO prefixes
    
    Args:
        airport_code: Airport code (e.g., KJFK, LFBA, EETN)
        
    Returns:
        Country name or None if not found
    """
    airport_code = airport_code.upper().strip()
    
    # Check two-letter prefixes first (longer matches take precedence)
    for prefix_len in [2, 1]:
        prefix = airport_code[:prefix_len]
        if prefix in AIRPORT_CODE_PREFIXES:
            country_name, _, _ = AIRPORT_CODE_PREFIXES[prefix]
            return country_name
    
    return None


def load_scraper_class(country: str):
    """
    Dynamically load a scraper class for a given country
    
    Args:
        country: Country name (e.g., 'USA', 'FRANCE', 'ESTONIA')
        
    Returns:
        Scraper class or None if not found
    """
    if country in _scraper_cache:
        return _scraper_cache[country]
    
    # Find the country in the prefix mapping
    for prefix, (country_name, module_name, class_name) in AIRPORT_CODE_PREFIXES.items():
        if country_name == country:
            try:
                # Try importing from scrapers package first (for generated scrapers)
                try:
                    module = importlib.import_module(f"scrapers.{module_name}")
                except ImportError:
                    # Fall back to root level imports (for USA, France)
                    module = importlib.import_module(module_name)
                
                scraper_class = getattr(module, class_name)
                _scraper_cache[country] = scraper_class
                logger.info(f"Loaded scraper class {class_name} for {country}")
                return scraper_class
            except (ImportError, AttributeError) as e:
                logger.warning(f"Failed to load scraper for {country}: {e}")
                return None
    
    logger.warning(f"No scraper mapping found for country: {country}")
    return None


def get_scraper_instance(country: str):
    """
    Get or create a scraper instance for a given country
    
    Args:
        country: Country name (e.g., 'USA', 'FRANCE', 'ESTONIA')
        
    Returns:
        Scraper instance or None if not found
    """
    scraper_class = load_scraper_class(country)
    if scraper_class:
        try:
            return scraper_class()
        except Exception as e:
            logger.error(f"Failed to instantiate scraper for {country}: {e}")
            return None
    return None


def get_available_countries() -> list:
    """Get list of all available countries with scrapers"""
    return list(set(country for _, (country, _, _) in AIRPORT_CODE_PREFIXES.items()))

