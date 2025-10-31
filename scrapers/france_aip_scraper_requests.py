#!/usr/bin/env python3
"""
France AIP scraper using requests and BeautifulSoup
Handles the complex French eAIP structure
"""

import time
import re
import logging
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FranceAIPScraperRequests:
    def __init__(self):
        """Initialize the France AIP scraper with requests"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        logger.info("Requests session initialized for France AIP")
    
    def get_airport_info(self, airport_code: str) -> Dict:
        """
        Get airport information from French AIP
        
        Args:
            airport_code: 3-4 letter airport code (e.g., 'LFBA', 'LFPG')
            
        Returns:
            Dictionary containing airport information
        """
        airport_code = airport_code.upper().strip()
        
        logger.info(f"Fetching France AIP information for {airport_code}")
        
        try:
            # Step 1: Navigate to the main SIA website
            main_url = "https://www.sia.aviation-civile.gouv.fr"
            logger.info(f"Step 1: Navigating to main SIA website: {main_url}")
            
            response = self.session.get(main_url, timeout=30)
            response.raise_for_status()
            logger.info(f"Successfully loaded main page: {len(response.text)} characters")
            
            # Parse the main page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Step 2: Find AIP menu link
            logger.info("Step 2: Looking for AIP menu link")
            aip_link = None
            
            # Look for AIP links
            aip_links = soup.find_all('a', string=re.compile(r'AIP', re.IGNORECASE))
            if aip_links:
                aip_link = aip_links[0]
                logger.info(f"Found AIP link: {aip_link.get('href')}")
            
            if not aip_link:
                logger.error("Could not find AIP menu link")
                raise Exception("Could not find AIP menu link")
            
            # Step 3: Navigate to eAIP FRANCE
            logger.info("Step 3: Looking for eAIP FRANCE link")
            
            # Get the AIP page
            aip_url = urljoin(main_url, aip_link.get('href'))
            logger.info(f"Navigating to AIP page: {aip_url}")
            
            aip_response = self.session.get(aip_url, timeout=30)
            aip_response.raise_for_status()
            
            aip_soup = BeautifulSoup(aip_response.text, 'html.parser')
            
            # Look for eAIP FRANCE link
            eaip_links = aip_soup.find_all('a', string=re.compile(r'eAIP FRANCE', re.IGNORECASE))
            if not eaip_links:
                logger.error("Could not find eAIP FRANCE link")
                raise Exception("Could not find eAIP FRANCE link")
            
            eaip_url = urljoin(main_url, eaip_links[0].get('href'))
            logger.info(f"Navigating to eAIP FRANCE: {eaip_url}")
            
            # Step 4: Get the eAIP page
            eaip_response = self.session.get(eaip_url, timeout=30)
            eaip_response.raise_for_status()
            
            eaip_soup = BeautifulSoup(eaip_response.text, 'html.parser')
            logger.info(f"Successfully loaded eAIP page: {len(eaip_response.text)} characters")
            
            # Step 5: Find the "02 OCT 2025" link
            logger.info("Step 5: Looking for '02 OCT 2025' link with id='dateVig'")
            
            # Look for the dateVig element
            date_vig_element = eaip_soup.find('a', {'id': 'dateVig'})
            if not date_vig_element:
                logger.error("Could not find dateVig element")
                raise Exception("Could not find effective date link")
            
            href_value = date_vig_element.get('href')
            logger.info(f"Found dateVig element with href: {href_value}")
            
            # Step 6: Build the full URL
            base_url = "https://www.sia.aviation-civile.gouv.fr/media/dvd/eAIP_02_OCT_2025/FRANCE/"
            full_url = base_url + href_value
            logger.info(f"Step 6: Built full URL: {full_url}")
            
            # Step 7: Navigate to the full AIP URL
            logger.info("Step 7: Navigating to the full AIP URL")
            aip_response = self.session.get(full_url, timeout=30)
            aip_response.raise_for_status()
            
            aip_soup = BeautifulSoup(aip_response.text, 'html.parser')
            logger.info(f"Successfully loaded AIP page: {len(aip_response.text)} characters")
            
            # Extract airport information
            logger.info("Extracting airport information")
            
            # Get page content
            page_text = aip_soup.get_text()
            logger.info(f"Page content length: {len(page_text)}")
            logger.info(f"Content preview: {page_text[:500]}")
            
            airport_info = {
                'airportCode': airport_code,
                'airportName': self._extract_airport_name_from_text(page_text),
                'towerHours': self._extract_operational_hours_from_text(page_text),
                'contacts': self._extract_contacts_from_text(page_text)
            }
            
            logger.info(f"Successfully extracted information for {airport_code}")
            return airport_info
            
        except Exception as e:
            logger.error(f"Error fetching airport information for {airport_code}: {e}")
            raise Exception(f"Failed to fetch airport information: {str(e)}")
    
    def _extract_airport_name_from_text(self, text: str) -> str:
        """Extract airport name from text content"""
        try:
            # Look for airport code patterns like "LFBA - AGEN-LA GARENNE"
            lines = text.split('\n')
            for line in lines:
                if '-' in line and len(line) > 5:
                    parts = line.split('-')
                    if len(parts) >= 2:
                        return line.strip()
            
            # Look for patterns like "AD 2 LFBA" or "LFBA"
            for line in lines:
                if 'AD 2' in line or len(line) < 50:
                    continue
                if 'LF' in line and len(line) < 100:
                    return line.strip()
            
            return "Unknown Airport"
            
        except Exception as e:
            logger.warning(f"Could not extract airport name: {e}")
            return "Unknown Airport"
    
    def _extract_operational_hours_from_text(self, text: str) -> List[Dict]:
        """Extract operational hours from text content"""
        hours = []
        
        try:
            if not text or len(text) == 0:
                return hours
            lines = text.split('\n')
            in_operational_section = False
            
            for line in lines:
                line = line.strip()
                
                if 'OPERATIONAL HOURS' in line.upper() or 'HORAIRES' in line.upper():
                    in_operational_section = True
                    continue
                
                if in_operational_section:
                    time_patterns = [
                        r'(LUN-VEN|MON-FRI|SAM|SAT|DIM|SUN|H24|24H)\s*:?\s*(\d{4}-\d{4})',
                        r'(LUN-VEN|MON-FRI|SAM|SAT|DIM|SUN|H24|24H)\s*:?\s*(\d{1,2}:\d{2}-\d{1,2}:\d{2})',
                    ]
                    
                    for pattern in time_patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            day = match.group(1)
                            time_str = match.group(2)
                            hours.append({
                                'day': day,
                                'hours': time_str
                            })
            
            if not hours:
                if 'H24' in text or '24H' in text:
                    hours.append({
                        'day': 'General',
                        'hours': '24 Hours'
                    })
            
            if not hours:
                hours.append({
                    'day': 'General',
                    'hours': 'Hours information not available'
                })
            
        except Exception as e:
            logger.warning(f"Error extracting operational hours: {e}")
            hours.append({
                'day': 'General',
                'hours': 'Hours information not available'
            })
        
        return hours
    
    def _extract_contacts_from_text(self, text: str) -> List[Dict]:
        """Extract contact information from text content"""
        contacts = []
        
        try:
            if not text or len(text) == 0:
                return contacts
            
            phone_pattern = r'(\+33|0)?\s*[1-9](?:\s*\d{2}){4}'
            phone_matches = re.findall(phone_pattern, text)
            
            cleaned_phones = []
            for match in phone_matches:
                phone = ''.join(match.split()) if isinstance(match, tuple) else match.strip()
                if len(phone) >= 10:
                    cleaned_phones.append(phone)
            
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            email_matches = re.findall(email_pattern, text)
            
            if cleaned_phones:
                for i, phone in enumerate(cleaned_phones[:2]):
                    contacts.append({
                        'type': f'Contact {i+1}',
                        'phone': phone,
                        'name': '',
                        'email': email_matches[i] if i < len(email_matches) else '',
                        'notes': ''
                    })
            
            if not contacts:
                contacts.append({
                    'type': 'General Contact',
                    'phone': '',
                    'name': '',
                    'email': email_matches[0] if email_matches else '',
                    'notes': 'Contact information not available'
                })
            
        except Exception as e:
            logger.warning(f"Error extracting contacts: {e}")
            contacts.append({
                'type': 'Contact Information',
                'phone': '',
                'name': '',
                'email': '',
                'notes': 'Contact information not available'
            })
        
        return contacts

def main():
    """Test the France AIP scraper with requests"""
    scraper = FranceAIPScraperRequests()
    
    try:
        airport_info = scraper.get_airport_info("LFBA")
        
        print("\n=== RESULTS ===")
        print(f"Airport Code: {airport_info['airportCode']}")
        print(f"Airport Name: {airport_info['airportName']}")
        print(f"Tower Hours: {airport_info['towerHours']}")
        print(f"Contacts: {airport_info['contacts']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
