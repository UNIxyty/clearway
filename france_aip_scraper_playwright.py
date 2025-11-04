#!/usr/bin/env python3
"""
France AIP scraper using Playwright for better JavaScript handling
Handles the complex French eAIP structure
"""

import time
import re
import logging
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright, Browser, Page

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FranceAIPScraperPlaywright:
    def __init__(self):
        """Initialize the France AIP scraper with Playwright"""
        self.browser = None
        self.page = None
        self.playwright = None
        self.setup_browser()
    
    def setup_browser(self):
        """Setup Playwright browser with optimized settings"""
        self.playwright = sync_playwright().start()
        
        # Launch Firefox browser with visible window for debugging
        self.browser = self.playwright.firefox.launch(
            headless=False,  # Set to True for production
            args=[
                '--width=1920',
                '--height=1080'
            ]
        )
        
        # Create new page with JavaScript enabled
        self.page = self.browser.new_page()
        
        # Enable JavaScript explicitly
        self.page.add_init_script("""
            // Ensure JavaScript is enabled
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        # Set viewport and timeout
        self.page.set_viewport_size({"width": 1920, "height": 1080})
        self.page.set_default_timeout(30000)
        
        logger.info("Playwright browser initialized for France AIP")
    
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
            # Step 1: Navigate to publications page first
            publications_url = "https://www.sia.aviation-civile.gouv.fr/documents/htmlshow?f=dvd/eAIP_02_OCT_2025/FRANCE/publications.html"
            logger.info(f"Step 1: Navigating to publications page: {publications_url}")
            
            # Try different wait strategies
            try:
                self.page.goto(publications_url, wait_until="domcontentloaded")
                time.sleep(3)
                self.page.wait_for_load_state("networkidle", timeout=10000)
                logger.info("Publications page loaded successfully")
            except:
                logger.info("Publications page failed, trying home page")
                eaip_home_url = "https://www.sia.aviation-civile.gouv.fr/documents/htmlshow?f=dvd/eAIP_02_OCT_2025/FRANCE/home.html"
                self.page.goto(eaip_home_url, wait_until="domcontentloaded")
                time.sleep(3)
                self.page.wait_for_load_state("networkidle", timeout=10000)
                logger.info("Home page loaded successfully")
            
            # Accept cookies if present
            try:
                accept_button = self.page.locator("button:has-text('Tout accepter')")
                if accept_button.is_visible():
                    accept_button.click()
                    time.sleep(2)
                    logger.info("Accepted cookies")
            except:
                logger.info("No cookie banner found")
            
            # Step 2: Wait for content to load and find "02 OCT 2025" link
            logger.info("Step 2: Looking for '02 OCT 2025' effective date link")
            
            # Wait for the page to fully load
            self.page.wait_for_load_state("networkidle")
            time.sleep(5)
            
            # Wait for JavaScript to load content
            logger.info("Waiting for JavaScript content to load...")
            try:
                # Wait for any element that might contain the date
                self.page.wait_for_selector("text=02 OCT", timeout=10000)
                logger.info("Found '02 OCT' text on page")
            except:
                logger.info("'02 OCT' text not found, trying alternative approaches")
            
            # Try to wait for dynamic content
            try:
                # Wait for the page to have more content than just navigation
                self.page.wait_for_function(
                    "document.body.textContent.length > 1000",
                    timeout=15000
                )
                logger.info("Page content loaded successfully")
            except:
                logger.warning("Page content may not be fully loaded")
            
            # Manual pause for debugging
            logger.info("PAUSE: Check the browser window - can you see the '02 OCT 2025' links?")
            logger.info("Waiting 15 seconds for you to check the browser...")
            time.sleep(15)
            
            # Try multiple approaches to find the link
            oct_link = None
            
            # Method 1: Look for link with exact text
            try:
                oct_link = self.page.locator("a:has-text('02 OCT 2025')").first
                if oct_link.is_visible():
                    logger.info("Method 1 SUCCESS: Found '02 OCT 2025' link via exact text")
            except:
                logger.info("Method 1 failed: Link not found")
            
            # Method 2: Look for any element containing the text
            if not oct_link:
                try:
                    oct_link = self.page.locator("text=02 OCT 2025").first
                    if oct_link.is_visible():
                        logger.info("Method 2 SUCCESS: Found '02 OCT 2025' element via text locator")
                except:
                    logger.info("Method 2 failed: Element not found")
            
            # Method 3: Use XPath
            if not oct_link:
                try:
                    oct_link = self.page.locator("xpath=//a[contains(text(), '02 OCT 2025')]").first
                    if oct_link.is_visible():
                        logger.info("Method 3 SUCCESS: Found '02 OCT 2025' link via XPath")
                except:
                    logger.info("Method 3 failed: XPath not found")
            
            # Method 4: Search all links
            if not oct_link:
                try:
                    links = self.page.locator("a").all()
                    logger.info(f"Method 4: Found {len(links)} total links")
                    
                    for i, link in enumerate(links):
                        try:
                            text = link.text_content()
                            if text and '02 OCT 2025' in text:
                                oct_link = link
                                logger.info(f"Method 4 SUCCESS: Found link {i}: '{text.strip()}'")
                                break
                        except:
                            continue
                    
                    if not oct_link:
                        logger.info("Method 4: No '02 OCT 2025' links found")
                        
                except Exception as e:
                    logger.error(f"Method 4 failed: {e}")
            
            # Method 5: Check iframes
            if not oct_link:
                try:
                    logger.info("Method 5: Checking iframes for content")
                    frames = self.page.frames
                    logger.info(f"Found {len(frames)} frames")
                    
                    for i, frame in enumerate(frames):
                        try:
                            frame_text = frame.text_content("body")
                            logger.info(f"Frame {i} content length: {len(frame_text)}")
                            
                            if '02 OCT 2025' in frame_text:
                                logger.info(f"Method 5 SUCCESS: Found '02 OCT 2025' in frame {i}")
                                # Try to find and click the link in this frame
                                frame_link = frame.locator("text=02 OCT 2025").first
                                if frame_link.is_visible():
                                    frame_link.click()
                                    self.page.wait_for_load_state("networkidle")
                                    time.sleep(3)
                                    logger.info(f"Successfully clicked link in frame {i}")
                                    logger.info(f"Current URL: {self.page.url}")
                                    oct_link = "clicked"  # Mark as found
                                    break
                        except Exception as e:
                            logger.info(f"Error checking frame {i}: {e}")
                            
                except Exception as e:
                    logger.error(f"Method 5 failed: {e}")
            
            # Click the link if found
            if oct_link:
                try:
                    logger.info("Clicking '02 OCT 2025' link")
                    oct_link.click()
                    self.page.wait_for_load_state("networkidle")
                    time.sleep(3)
                    logger.info(f"Successfully clicked '02 OCT 2025' link")
                    logger.info(f"Current URL after click: {self.page.url}")
                except Exception as e:
                    logger.error(f"Error clicking link: {e}")
            else:
                logger.error("Could not find '02 OCT 2025' link")
                raise Exception("Could not find effective date link")
            
            # Step 3: Navigate to AD 2 AÉRODROMES
            logger.info("Step 3: Looking for 'AD 2 AÉRODROMES' link")
            try:
                ad2_link = self.page.locator("text=AD 2 AÉRODROMES").first
                if ad2_link.is_visible():
                    ad2_link.click()
                    self.page.wait_for_load_state("networkidle")
                    time.sleep(2)
                    logger.info("Successfully navigated to AD 2 AÉRODROMES")
                else:
                    logger.warning("AD 2 AÉRODROMES link not visible")
            except Exception as e:
                logger.warning(f"Could not click AD 2 AÉRODROMES: {e}")
            
            # Step 4: Click on specific airport
            logger.info(f"Step 4: Looking for airport {airport_code}")
            try:
                airport_link = self.page.locator(f"text={airport_code}").first
                if airport_link.is_visible():
                    airport_link.click()
                    self.page.wait_for_load_state("networkidle")
                    time.sleep(3)
                    logger.info(f"Successfully clicked airport {airport_code}")
                else:
                    logger.warning(f"Airport {airport_code} link not visible")
            except Exception as e:
                logger.warning(f"Could not click airport {airport_code}: {e}")
            
            # Step 5: Click on AD 2.2 section
            logger.info("Step 5: Looking for 'AD 2.2' section")
            try:
                ad22_link = self.page.locator("text=AD 2.2").first
                if ad22_link.is_visible():
                    ad22_link.click()
                    self.page.wait_for_load_state("networkidle")
                    time.sleep(2)
                    logger.info("Successfully navigated to AD 2.2")
                else:
                    logger.warning("AD 2.2 link not visible")
            except Exception as e:
                logger.warning(f"Could not click AD 2.2: {e}")
            
            # Extract airport information
            logger.info("Extracting airport information")
            
            # Get page content
            page_content = self.page.content()
            logger.info(f"Page content length: {len(page_content)}")
            
            # Get visible text
            body_text = self.page.locator("body").text_content()
            logger.info(f"Body text length: {len(body_text)}")
            logger.info(f"Content preview: {body_text[:500]}")
            
            airport_info = {
                'airportCode': airport_code,
                'airportName': self._extract_airport_name_from_text(body_text),
                'towerHours': self._extract_operational_hours_from_text(body_text),
                'contacts': self._extract_contacts_from_text(body_text)
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
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Playwright browser closed")

def main():
    """Test the France AIP scraper with Playwright"""
    scraper = FranceAIPScraperPlaywright()
    
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
