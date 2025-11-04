#!/usr/bin/env python3
"""
Unified airport scraper that automatically detects country and uses appropriate scraper
Supports USA and France AIP systems
"""

import logging
from typing import Dict
from airport_scraper import AirportScraper as USAScraper
from france_aip_scraper import FranceAIPScraper
from estonia_aip_scraper_playwright import EstoniaAIPScraperPlaywright

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedScraper:
    def __init__(self):
        """Initialize the unified scraper"""
        self.usa_scraper = None
        self.france_scraper = None
        self.estonia_scraper = None
        
    def get_country_from_code(self, airport_code: str) -> str:
        """
        Determine country from airport code
        
        Args:
            airport_code: Airport code (e.g., KJFK, LFBA)
            
        Returns:
            Country code ('USA', 'FRANCE', or 'UNKNOWN')
        """
        airport_code = airport_code.upper().strip()
        
        # USA airports typically start with 'K' (e.g., KJFK, KLAX)
        if airport_code.startswith('K'):
            return 'USA'
        
        # France airports typically start with 'LF' (e.g., LFBA, LFPG)
        elif airport_code.startswith('LF'):
            return 'FRANCE'
        # Estonia airports start with 'EE' (e.g., EETN)
        elif airport_code.startswith('EE'):
            return 'ESTONIA'
        
        # Canada airports start with 'C' (e.g., CYYZ)
        elif airport_code.startswith('C'):
            return 'CANADA'
        
        # UK airports start with 'EG' (e.g., EGLL)
        elif airport_code.startswith('EG'):
            return 'UK'
        
        # Germany airports start with 'ED' (e.g., EDDF)
        elif airport_code.startswith('ED'):
            return 'GERMANY'
        
        else:
            return 'UNKNOWN'
    
    def get_airport_info(self, airport_code: str) -> Dict:
        """
        Get airport information using the appropriate scraper
        
        Args:
            airport_code: Airport code (e.g., KJFK, LFBA)
            
        Returns:
            Dictionary containing airport information
        """
        airport_code = airport_code.upper().strip()
        country = self.get_country_from_code(airport_code)
        
        logger.info(f"Detected country: {country} for airport {airport_code}")
        
        if country == 'USA':
            if not self.usa_scraper:
                self.usa_scraper = USAScraper()
            return self.usa_scraper.get_airport_info(airport_code)
        
        elif country == 'FRANCE':
            if not self.france_scraper:
                self.france_scraper = FranceAIPScraper()
            return self.france_scraper.get_airport_info(airport_code)
        
        elif country == 'ESTONIA':
            if not self.estonia_scraper:
                self.estonia_scraper = EstoniaAIPScraperPlaywright()
            return self.estonia_scraper.get_airport_info(airport_code)
        
        else:
            raise Exception(f"Unsupported airport code: {airport_code} (country: {country})")
    
    def close(self):
        """Close all scrapers"""
        if self.usa_scraper:
            self.usa_scraper.close()
        if self.france_scraper:
            self.france_scraper.close()
        if self.estonia_scraper:
            self.estonia_scraper.close()

def main():
    """Test the unified scraper"""
    scraper = UnifiedScraper()
    
    try:
        # Test with USA airport
        print("Testing USA airport (KJFK)...")
        usa_info = scraper.get_airport_info("KJFK")
        print(f"USA Airport: {usa_info['airportName']}")
        print(f"Hours: {usa_info['towerHours']}")
        print(f"Contacts: {usa_info['contacts']}")
        
        print("\n" + "="*50 + "\n")
        
        # Test with France airport
        print("Testing France airport (LFBA)...")
        france_info = scraper.get_airport_info("LFBA")
        print(f"France Airport: {france_info['airportName']}")
        print(f"Hours: {france_info['towerHours']}")
        print(f"Contacts: {france_info['contacts']}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()

