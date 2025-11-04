#!/usr/bin/env python3
"""
Debug test script to check what's happening with the FAA website
"""

import logging
from airport_scraper import AirportScraper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    scraper = AirportScraper()
    
    try:
        # Test with JFK
        logger.info("Testing with KJFK...")
        airport_info = scraper.get_airport_info("KJFK")
        
        print("\n=== RESULTS ===")
        print(f"Airport Code: {airport_info['airportCode']}")
        print(f"Airport Name: {airport_info['airportName']}")
        print(f"Tower Hours: {airport_info['towerHours']}")
        print(f"Contacts: {airport_info['contacts']}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()

