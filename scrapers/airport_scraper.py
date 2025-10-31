#!/usr/bin/env python3
"""
Fast headless scraper for USA AIP airport information
Scrapes tower hours and contact information from FAA database
"""

import time
import re
import logging
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AirportScraper:
    def __init__(self):
        """Initialize the airport scraper with optimized settings"""
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver with optimized settings for speed"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", chrome_prefs)
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        # Page load strategy for speed
        chrome_options.page_load_strategy = 'eager'
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(5)
        
        logger.info("WebDriver initialized with optimized settings")
    
    def get_airport_info(self, airport_code: str) -> Dict:
        """
        Get airport information from FAA database
        
        Args:
            airport_code: 3-4 letter airport code (e.g., 'KJFK', 'LAX')
            
        Returns:
            Dictionary containing airport information
        """
        # Ensure airport code is uppercase
        airport_code = airport_code.upper().strip()
        
        # Construct URL
        url = f"https://nfdc.faa.gov/nfdcApps/services/ajv5/airportDisplay.jsp?airportId={airport_code}"
        
        logger.info(f"Fetching airport information for {airport_code}")
        
        try:
            # Navigate to the airport page
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Debug: Log page content (commented out for production)
            # self._debug_page_content()
            
            # Extract airport information
            airport_info = {
                'airportCode': airport_code,
                'airportName': self._extract_airport_name(),
                'towerHours': self._extract_tower_hours(),
                'contacts': self._extract_contacts()
            }
            
            logger.info(f"Successfully extracted information for {airport_code}")
            return airport_info
            
        except TimeoutException:
            logger.error(f"Timeout loading page for {airport_code}")
            raise Exception(f"Timeout loading airport information for {airport_code}")
        except Exception as e:
            logger.error(f"Error fetching airport information for {airport_code}: {e}")
            raise Exception(f"Failed to fetch airport information: {str(e)}")
    
    def _extract_airport_name(self) -> str:
        """Extract airport name from the page"""
        try:
            # Get all text content
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Look for airport name pattern in the text
            lines = body_text.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                # Look for lines that contain airport names (usually after the code)
                if line and len(line) > 5 and any(word in line.upper() for word in ['INTL', 'AIRPORT', 'FIELD', 'MUNICIPAL']):
                    # Check if previous line contains airport code
                    if i > 0 and any(code in lines[i-1] for code in ['KJFK', 'KLAX', 'KORD', 'KDFW', 'KATL']):
                        logger.info(f"Found airport name: {line}")
                        return line
            
            # Try to get from page title
            title = self.driver.title
            if title and title != "Aeronautical Information Services":
                logger.info(f"Using page title as airport name: {title}")
                return title
            
            return "Unknown Airport"
            
        except Exception as e:
            logger.warning(f"Could not extract airport name: {e}")
            return "Unknown Airport"
    
    def _extract_tower_hours(self) -> List[Dict]:
        """Extract tower hours from Operations section"""
        tower_hours = []
        
        try:
            # Get all text content
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Look for Operations section in the text
            lines = body_text.split('\n')
            operations_start = -1
            
            for i, line in enumerate(lines):
                if "OPERATIONS" in line.upper():
                    operations_start = i
                    break
            
            if operations_start >= 0:
                # Extract text from Operations section until next major section
                operations_text = []
                for i in range(operations_start + 1, len(lines)):
                    line = lines[i].strip()
                    # Stop at next major section
                    if line and any(section in line.upper() for section in ['COMMUNICATIONS', 'NAVAIDS', 'WEATHER', 'CONTACTS']):
                        break
                    if line:
                        operations_text.append(line)
                
                if operations_text:
                    # Parse the operations text for hours
                    tower_hours = self._parse_hours_text('\n'.join(operations_text))
                    logger.info(f"Found operations text: {len(operations_text)} lines")
            
            if not tower_hours:
                # Fallback: look for any time patterns in the entire text
                tower_hours = self._parse_hours_text(body_text)
            
        except Exception as e:
            logger.warning(f"Error extracting tower hours: {e}")
        
        return tower_hours
    
    def _extract_contacts(self) -> List[Dict]:
        """Extract contact information from Contacts section"""
        contacts = []
        
        try:
            # Get all text content
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Look for Contacts section in the text
            lines = body_text.split('\n')
            contacts_start = -1
            
            for i, line in enumerate(lines):
                if "CONTACTS" in line.upper():
                    contacts_start = i
                    break
            
            if contacts_start >= 0:
                # Extract text from Contacts section until next major section or end
                contacts_text = []
                for i in range(contacts_start + 1, len(lines)):
                    line = lines[i].strip()
                    # Stop at next major section
                    if line and any(section in line.upper() for section in ['REMARKS', 'SUMMARY', 'OPERATIONS']):
                        break
                    if line:
                        contacts_text.append(line)
                
                if contacts_text:
                    # Parse the contacts text
                    contacts = self._parse_contacts_text('\n'.join(contacts_text))
                    logger.info(f"Found contacts text: {len(contacts_text)} lines")
            
            if not contacts:
                # Fallback: look for any contact patterns in the entire text
                contacts = self._parse_contacts_text(body_text)
            
        except Exception as e:
            logger.warning(f"Error extracting contacts: {e}")
        
        return contacts
    
    def _debug_page_content(self):
        """Debug method to log page content"""
        try:
            logger.info("=== DEBUG: Page Content ===")
            logger.info(f"Page title: {self.driver.title}")
            logger.info(f"Page URL: {self.driver.current_url}")
            
            # Get all text content
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"Body text length: {len(body_text)}")
            logger.info(f"First 500 chars: {body_text[:500]}")
            
            # Look for common elements
            try:
                headers = self.driver.find_elements(By.TAG_NAME, "h1")
                logger.info(f"Found {len(headers)} h1 elements")
                for i, h in enumerate(headers[:3]):
                    logger.info(f"  H1 {i}: {h.text[:100]}")
            except:
                pass
            
            try:
                headers2 = self.driver.find_elements(By.TAG_NAME, "h2")
                logger.info(f"Found {len(headers2)} h2 elements")
                for i, h in enumerate(headers2[:3]):
                    logger.info(f"  H2 {i}: {h.text[:100]}")
            except:
                pass
            
            logger.info("=== END DEBUG ===")
            
        except Exception as e:
            logger.warning(f"Debug failed: {e}")
    
    def _find_section(self, section_name: str) -> Optional[object]:
        """Find a section by name on the page"""
        try:
            # Look for section headers
            section_headers = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{section_name}')]")
            
            for header in section_headers:
                # Find the parent container
                parent = header.find_element(By.XPATH, "./..")
                return parent
                
        except Exception as e:
            logger.warning(f"Could not find section '{section_name}': {e}")
        
        return None
    
    def _extract_text_from_section(self, section, keywords: List[str]) -> str:
        """Extract relevant text from a section based on keywords"""
        try:
            # Get all text from the section
            section_text = section.text.lower()
            
            # Look for elements containing keywords
            for keyword in keywords:
                elements = section.find_elements(By.XPATH, f".//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
                if elements:
                    return elements[0].text
            
            # If no specific elements found, return section text
            return section.text
            
        except Exception as e:
            logger.warning(f"Error extracting text from section: {e}")
            return ""
    
    def _parse_hours_text(self, hours_text: str) -> List[Dict]:
        """Parse hours text into structured data"""
        hours = []
        
        try:
            lines = hours_text.split('\n')
            
            # Look for specific tower hours patterns
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for tower hours specifically
                if 'TOWER HOURS' in line.upper() or 'TOWER' in line.upper() and 'HOURS' in line.upper():
                    # Extract the hours from this line or the next line
                    time_match = re.search(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', line)
                    if time_match:
                        hours.append({
                            'day': 'Tower Hours',
                            'hours': f"{time_match.group(1)}-{time_match.group(2)}"
                        })
                    elif '24 HOURS' in line.upper() or 'CONTINUOUS' in line.upper():
                        hours.append({
                            'day': 'Tower Hours',
                            'hours': '24 Hours'
                        })
                    else:
                        # Look for hours in the next few lines
                        for i, next_line in enumerate(lines[lines.index(line)+1:lines.index(line)+3]):
                            if '24 HOURS' in next_line.upper() or 'CONTINUOUS' in next_line.upper():
                                hours.append({
                                    'day': 'Tower Hours',
                                    'hours': '24 Hours'
                                })
                                break
                            time_match = re.search(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', next_line)
                            if time_match:
                                hours.append({
                                    'day': 'Tower Hours',
                                    'hours': f"{time_match.group(1)}-{time_match.group(2)}"
                                })
                                break
                
                # Look for approach/departure hours
                elif 'APCH/DEP HOURS' in line.upper() or 'APPROACH' in line.upper() and 'HOURS' in line.upper():
                    if '24 HOURS' in line.upper() or 'CONTINUOUS' in line.upper():
                        hours.append({
                            'day': 'Approach/Departure',
                            'hours': '24 Hours'
                        })
                    else:
                        time_match = re.search(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', line)
                        if time_match:
                            hours.append({
                                'day': 'Approach/Departure',
                                'hours': f"{time_match.group(1)}-{time_match.group(2)}"
                            })
            
            # If no specific hours found, look for any 24 hours or continuous operations
            # Deduplicate entries
            if hours:
                unique = []
                seen = set()
                for h in hours:
                    key = (h.get('day'), h.get('hours'))
                    if key not in seen:
                        seen.add(key)
                        unique.append(h)
                hours = unique
            if not hours:
                for line in lines:
                    if '24 HOURS' in line.upper() or 'CONTINUOUS' in line.upper():
                        hours.append({
                            'day': 'Operations',
                            'hours': '24 Hours'
                        })
                        break
            
            # If still no hours found, return a general message
            if not hours:
                hours.append({
                    'day': 'General',
                    'hours': 'Hours information not available'
                })
            
        except Exception as e:
            logger.warning(f"Error parsing hours text: {e}")
            hours.append({
                'day': 'General',
                'hours': 'Hours information not available'
            })
        
        return hours
    
    def _parse_contacts_text(self, contacts_text: str) -> List[Dict]:
        """Parse contacts text into structured data"""
        contacts = []
        
        try:
            lines = contacts_text.split('\n')
            current_contact = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for specific contact headers
                if line.upper() in ['OWNER', 'MANAGER']:
                    # Save previous contact if exists
                    if current_contact:
                        contacts.append(current_contact)
                    
                    # Start new contact
                    current_contact = {
                        'type': line,
                        'phone': '',
                        'name': '',
                        'email': '',
                        'notes': ''
                    }
                elif current_contact:
                    # Look for phone numbers in the line
                    phone_pattern = r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})'
                    phone_match = re.search(phone_pattern, line)
                    
                    # Look for email addresses
                    email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
                    email_match = re.search(email_pattern, line)
                    
                    if phone_match:
                        # Clean up phone number formatting
                        phone = phone_match.group(1).strip()
                        current_contact['phone'] = phone
                    elif email_match:
                        current_contact['email'] = email_match.group(1)
                    elif not current_contact['name'] and len(line) > 3:
                        # This might be a name
                        current_contact['name'] = line
                    elif len(line) > 3:
                        # Additional info
                        current_contact['notes'] += line + ' '
            
            # Add the last contact
            if current_contact:
                contacts.append(current_contact)
            
            # If no structured contacts found, look for any phone numbers
            if not contacts:
                phone_pattern = r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})'
                phone_matches = re.findall(phone_pattern, contacts_text)
                
                for i, phone in enumerate(phone_matches[:3]):  # Limit to first 3 phone numbers
                    contacts.append({
                        'type': f'Contact {i+1}',
                        'phone': phone,
                        'name': '',
                        'email': '',
                        'notes': ''
                    })
            
            # If still no contacts, create a general one
            if not contacts:
                contacts.append({
                    'type': 'General Contact',
                    'phone': '',
                    'name': '',
                    'email': '',
                    'notes': 'Contact information not available'
                })
            
        except Exception as e:
            logger.warning(f"Error parsing contacts text: {e}")
            contacts.append({
                'type': 'Contact Information',
                'phone': '',
                'name': '',
                'email': '',
                'notes': 'Contact information not available'
            })
        
        return contacts
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

def main():
    """Test the scraper with a sample airport"""
    scraper = AirportScraper()
    
    try:
        # Test with JFK
        airport_info = scraper.get_airport_info("KJFK")
        
        print("Airport Information:")
        print(f"Code: {airport_info['airportCode']}")
        print(f"Name: {airport_info['airportName']}")
        print(f"Tower Hours: {airport_info['towerHours']}")
        print(f"Contacts: {airport_info['contacts']}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
