#!/usr/bin/env python3
"""
France AIP scraper using undetected-chromedriver for better anti-bot bypass
Handles the complex French eAIP structure
"""

import time
import re
import logging
from typing import Dict, List, Optional
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FranceAIPScraperUndetected:
    def __init__(self):
        """Initialize the France AIP scraper with undetected Chrome"""
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup undetected Chrome WebDriver"""
        try:
            # Use undetected-chromedriver to bypass anti-bot detection
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            
            # Create undetected Chrome driver
            self.driver = uc.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            logger.info("Undetected Chrome WebDriver initialized for France AIP")
            
        except Exception as e:
            logger.error(f"Failed to initialize undetected Chrome driver: {e}")
            raise
    
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
            self.driver.get(main_url)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)
            
            # Accept cookies if present
            try:
                accept_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Tout accepter')]")
                accept_button.click()
                time.sleep(2)
                logger.info("Accepted cookies")
            except:
                logger.info("No cookie banner found")
            
            # Step 2: Navigate to AIP menu
            logger.info("Step 2: Looking for AIP menu")
            
            # Debug: Check what's on the page
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text
            logger.info(f"Page content length: {len(body_text)}")
            logger.info(f"Content preview: {body_text[:500]}")
            
            # Try different selectors for AIP menu
            aip_menu = None
            
            # Method 1: Look for AIP text
            try:
                aip_menu = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'AIP')]"))
                )
                logger.info("Method 1 SUCCESS: Found AIP menu via text")
            except Exception as e:
                logger.info(f"Method 1 failed: {e}")
            
            # Method 2: Look for AIP in any element
            if not aip_menu:
                try:
                    aip_menu = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'AIP')]"))
                    )
                    logger.info("Method 2 SUCCESS: Found AIP element via text")
                except Exception as e:
                    logger.info(f"Method 2 failed: {e}")
            
            # Method 3: Look for navigation elements
            if not aip_menu:
                try:
                    nav_elements = self.driver.find_elements(By.TAG_NAME, 'a')
                    logger.info(f"Found {len(nav_elements)} links on page")
                    for i, link in enumerate(nav_elements[:10]):
                        text = link.text.strip()
                        logger.info(f"Link {i}: '{text}'")
                        if 'AIP' in text:
                            aip_menu = link
                            logger.info(f"Method 3 SUCCESS: Found AIP link {i}: '{text}'")
                            break
                except Exception as e:
                    logger.info(f"Method 3 failed: {e}")
            
            if aip_menu:
                try:
                    aip_menu.click()
                    time.sleep(2)
                    logger.info("Clicked AIP menu")
                except Exception as e:
                    logger.error(f"Error clicking AIP menu: {e}")
                    raise Exception("Could not click AIP menu")
            else:
                logger.error("Could not find AIP menu with any method")
                raise Exception("Could not find AIP menu")
            
            # Step 3: Click on "eAIP FRANCE" from dropdown
            logger.info("Step 3: Looking for 'eAIP FRANCE' link")
            try:
                eaip_france_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'eAIP FRANCE')]"))
                )
                eaip_france_link.click()
                time.sleep(3)
                logger.info("Clicked eAIP FRANCE link")
                logger.info(f"Current URL after clicking eAIP FRANCE: {self.driver.current_url}")
            except Exception as e:
                logger.error(f"Could not find eAIP FRANCE link: {e}")
                raise Exception("Could not find eAIP FRANCE link")
            
            # Step 4: Wait for content to load and find the table
            logger.info("Step 4: Waiting for content to load...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)
            
            # Wait longer for dynamic content
            logger.info("Waiting 10 seconds for dynamic content to load...")
            time.sleep(10)
            
            # Check if content is in iframe
            logger.info("Checking if content is in iframe...")
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            logger.info(f"Found {len(iframes)} iframes")
            
            oct_link = None
            href_value = None
            
            # Check iframes for the content
            for i, iframe in enumerate(iframes):
                try:
                    src = iframe.get_attribute('src') or ''
                    name = iframe.get_attribute('name') or ''
                    logger.info(f"Iframe {i}: name='{name}', src='{src[:100] if src else 'No src'}'")
                    
                    if src and ('vaipEx' in src or 'eAIP' in src):
                        logger.info(f"Found relevant iframe {i}, switching to it")
                        self.driver.switch_to.frame(iframe)
                        
                        # Wait for content in iframe
                        time.sleep(3)
                        
                        # Look for the dateVig element in this iframe
                        try:
                            oct_link = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.ID, "dateVig"))
                            )
                            href_value = oct_link.get_attribute('href')
                            logger.info(f"SUCCESS: Found '02 OCT 2025' link in iframe {i} via ID 'dateVig'")
                            logger.info(f"Extracted href: {href_value}")
                            break
                        except Exception as e:
                            logger.info(f"dateVig not found in iframe {i}: {e}")
                        
                        self.driver.switch_to.default_content()
                        
                except Exception as e:
                    logger.info(f"Error checking iframe {i}: {e}")
                    self.driver.switch_to.default_content()
            
            # If not found in iframe, try main page
            if not oct_link:
                logger.info("Trying main page for '02 OCT 2025' link...")
                
                # Method 1: By ID (most reliable)
                try:
                    oct_link = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "dateVig"))
                    )
                    href_value = oct_link.get_attribute('href')
                    logger.info(f"Method 1 SUCCESS: Found '02 OCT 2025' link via ID 'dateVig'")
                    logger.info(f"Extracted href: {href_value}")
                except Exception as e:
                    logger.info(f"Method 1 failed: {e}")
                
                # Method 2: By href attribute
                if not oct_link:
                    try:
                        oct_link = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='AIRAC-2025-10-02']"))
                        )
                        href_value = oct_link.get_attribute('href')
                        logger.info(f"Method 2 SUCCESS: Found '02 OCT 2025' link via href")
                        logger.info(f"Extracted href: {href_value}")
                    except Exception as e:
                        logger.info(f"Method 2 failed: {e}")
                
                # Method 3: By parent class
                if not oct_link:
                    try:
                        oct_link = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "td.green.dateUpper a"))
                        )
                        href_value = oct_link.get_attribute('href')
                        logger.info(f"Method 3 SUCCESS: Found '02 OCT 2025' link via parent class")
                        logger.info(f"Extracted href: {href_value}")
                    except Exception as e:
                        logger.info(f"Method 3 failed: {e}")
            
            if not oct_link or not href_value:
                logger.error("Could not find '02 OCT 2025' link or extract href")
                raise Exception("Could not find effective date link")
            
            # Step 5: Build the full URL
            base_url = "https://www.sia.aviation-civile.gouv.fr/media/dvd/eAIP_02_OCT_2025/FRANCE/"
            full_url = base_url + href_value
            logger.info(f"Step 5: Built full URL: {full_url}")
            
            # Step 6: Navigate to the full URL
            logger.info("Step 6: Navigating to the full AIP URL")
            self.driver.get(full_url)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)
            logger.info(f"Successfully navigated to AIP page: {self.driver.current_url}")
            
            # Extract airport information
            logger.info("Extracting airport information")
            
            # Get page content
            body_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            all_content = body_element.text
            logger.info(f"Page content length: {len(all_content)}")
            logger.info(f"Content preview: {all_content[:500]}")
            
            airport_info = {
                'airportCode': airport_code,
                'airportName': self._extract_airport_name_from_text(all_content),
                'towerHours': self._extract_operational_hours_from_text(all_content),
                'contacts': self._extract_contacts_from_text(all_content)
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
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
        logger.info("Undetected Chrome WebDriver closed")

def main():
    """Test the France AIP scraper with undetected Chrome"""
    scraper = FranceAIPScraperUndetected()
    
    try:
        airport_info = scraper.get_airport_info("LFBA")
        
        print("\n=== RESULTS ===")
        print(f"Airport Code: {airport_info['airportCode']}")
        print(f"Airport Name: {airport_info['airportName']}")
        print(f"Tower Hours: {airport_info['towerHours']}")
        print(f"Contacts: {airport_info['contacts']}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
