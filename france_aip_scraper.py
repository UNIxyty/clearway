#!/usr/bin/env python3
"""
France AIP scraper for French aviation information
Handles the complex French eAIP structure
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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FranceAIPScraper:
    def __init__(self):
        """Initialize the France AIP scraper"""
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver with optimized settings"""
        chrome_options = Options()
        # Remove --headless to see the browser window
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.page_load_strategy = 'eager'
        
        # Add user agent to look more like a real browser
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(10)
        
        # Execute script to remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("WebDriver initialized for France AIP (visible browser window)")
    
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
            
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)  # Wait longer for dynamic content
            
            # Try scrolling to trigger any lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Wait much longer for JavaScript to load content
            logger.info("Waiting 15 seconds for JavaScript to load content...")
            time.sleep(15)
            
            # Try JavaScript execution to find and click the element
            logger.info("Trying JavaScript execution to find '02 OCT 2025' link...")
            try:
                # Use JavaScript to find elements containing the text
                js_code = """
                var elements = document.querySelectorAll('*');
                for (var i = 0; i < elements.length; i++) {
                    if (elements[i].textContent && elements[i].textContent.includes('02 OCT 2025')) {
                        console.log('Found element:', elements[i].tagName, elements[i].textContent.trim());
                        if (elements[i].tagName === 'A' || elements[i].onclick) {
                            elements[i].click();
                            return 'clicked';
                        }
                    }
                }
                return 'not found';
                """
                result = self.driver.execute_script(js_code)
                logger.info(f"JavaScript execution result: {result}")
                
                if result == 'clicked':
                    time.sleep(3)
                    logger.info(f"Successfully clicked via JavaScript, URL: {self.driver.current_url}")
                
            except Exception as e:
                logger.error(f"JavaScript execution failed: {e}")
            
            # Accept cookies if present
            try:
                accept_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Tout accepter')]")
                accept_button.click()
                time.sleep(2)
                logger.info("Accepted cookies")
            except:
                logger.info("No cookie banner found")
            
            # Step 2: Click on the "02 OCT 2025" effective date link
            logger.info("Step 2: Looking for '02 OCT 2025' effective date link")
            logger.info("PAUSE: Check the browser window - can you see the '02 OCT 2025' links?")
            logger.info("Waiting 10 seconds for you to check the browser...")
            time.sleep(10)
            
            # Debug: Check page source for any clues
            page_source = self.driver.page_source
            logger.info(f"Page source length: {len(page_source)}")
            
            # Look for any references to "02 OCT" or "2025" in the page source
            if '02 OCT' in page_source:
                logger.info("Found '02 OCT' in page source!")
            if '2025' in page_source:
                logger.info("Found '2025' in page source!")
            if 'Effective' in page_source:
                logger.info("Found 'Effective' in page source!")
            if 'eAIP' in page_source:
                logger.info("Found 'eAIP' in page source!")
            
            # Check if there are any JavaScript errors
            logs = self.driver.get_log('browser')
            if logs:
                logger.info(f"Found {len(logs)} browser logs")
                for log in logs[:3]:  # Show first 3 logs
                    logger.info(f"Browser log: {log}")
            
            # Try to wait for any dynamic content
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: len(driver.find_element(By.TAG_NAME, 'body').text) > 1000
                )
                logger.info("Dynamic content loaded!")
            except:
                logger.info("No dynamic content loaded")
            
            # Check for iframes
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            logger.info(f"Found {len(iframes)} iframes")
            
            for i, iframe in enumerate(iframes):
                src = iframe.get_attribute('src') or ''
                name = iframe.get_attribute('name') or ''
                logger.info(f"Iframe {i}: name='{name}', src='{src[:100] if src else 'No src'}'")
                
                # Try to access iframe content
                if not src:
                    try:
                        self.driver.switch_to.frame(iframe)
                        iframe_text = self.driver.find_element(By.TAG_NAME, 'body').text
                        logger.info(f"Iframe {i} content length: {len(iframe_text)}")
                        logger.info(f"Iframe {i} content preview: {iframe_text[:300]}")
                        
                        # Look for "02 OCT 2025" in iframe
                        if '02 OCT 2025' in iframe_text:
                            logger.info("Found '02 OCT 2025' in iframe content!")
                            # Look for the link in this iframe
                            iframe_links = self.driver.find_elements(By.TAG_NAME, 'a')
                            for link in iframe_links:
                                text = link.text.strip()
                                if '02 OCT 2025' in text:
                                    logger.info(f"Found '02 OCT 2025' link in iframe: '{text}'")
                                    link.click()
                                    time.sleep(3)
                                    logger.info(f"Clicked iframe link, URL: {self.driver.current_url}")
                                    break
                        
                        self.driver.switch_to.default_content()
                    except Exception as e:
                        logger.info(f"Error accessing iframe {i}: {e}")
                        self.driver.switch_to.default_content()
            
            # Step 4: Find the "02 OCT 2025" link and extract href
            logger.info("Step 4: Looking for '02 OCT 2025' link with id='dateVig'")
            
            # Debug: Check if content is in iframe
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
                    
                    # Try to access any iframe that might contain content
                    if src or name:
                        logger.info(f"Trying to access iframe {i}")
                        self.driver.switch_to.frame(iframe)
                        
                        # Wait for content to load in iframe
                        time.sleep(3)
                        
                        # Check iframe content
                        try:
                            iframe_body = self.driver.find_element(By.TAG_NAME, 'body')
                            iframe_text = iframe_body.text
                            logger.info(f"Iframe {i} content length: {len(iframe_text)}")
                            logger.info(f"Iframe {i} content preview: {iframe_text[:300]}")
                            
                            # Look for the dateVig element in this iframe
                            try:
                                oct_link = WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located((By.ID, "dateVig"))
                                )
                                href_value = oct_link.get_attribute('href')
                                logger.info(f"SUCCESS: Found '02 OCT 2025' link in iframe {i} via ID 'dateVig'")
                                logger.info(f"Extracted href: {href_value}")
                                break
                            except Exception as e:
                                logger.info(f"dateVig not found in iframe {i}: {e}")
                                
                                # Try alternative selectors in iframe
                                try:
                                    oct_link = self.driver.find_element(By.CSS_SELECTOR, "a[href*='AIRAC-2025-10-02']")
                                    href_value = oct_link.get_attribute('href')
                                    logger.info(f"SUCCESS: Found '02 OCT 2025' link in iframe {i} via href")
                                    logger.info(f"Extracted href: {href_value}")
                                    break
                                except Exception as e2:
                                    logger.info(f"Alternative selector failed in iframe {i}: {e2}")
                                    
                        except Exception as e:
                            logger.info(f"Error accessing iframe {i} content: {e}")
                        
                        self.driver.switch_to.default_content()
                        
                except Exception as e:
                    logger.info(f"Error checking iframe {i}: {e}")
                    self.driver.switch_to.default_content()
            
            # If not found in iframe, try main page
            if not oct_link:
                logger.info("Trying main page for '02 OCT 2025' link...")
                
                # Method 1: By ID (most reliable)
                try:
                    oct_link = WebDriverWait(self.driver, 5).until(
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
                        oct_link = WebDriverWait(self.driver, 5).until(
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
                        oct_link = WebDriverWait(self.driver, 5).until(
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
            
            # Now we should be on the actual AIP page - let's see what we have
            logger.info(f"Final URL: {self.driver.current_url}")
            logger.info(f"Page title: {self.driver.title}")
            
            # Check if we have meaningful content now
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text
            logger.info(f"Page content length: {len(body_text)}")
            logger.info(f"Content preview: {body_text[:500]}")
            
            if len(body_text) > 2000:
                logger.info("Successfully loaded AIP content!")
            else:
                logger.warning("Still only getting navigation content")
            
            # Wait for page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)  # Extra time for dynamic content
            
            # The content should now be in the main window
            logger.info(f"Final URL: {self.driver.current_url}")
            logger.info(f"Page title: {self.driver.title}")
            
            # Get the page content
            body_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get all text content
            all_content = body_element.text
            logger.info(f"Page content length: {len(all_content)}")
            logger.info(f"Content preview: {all_content[:500]}")
            
            # Debug: Check for iframes that might contain the actual content
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            logger.info(f"Found {len(iframes)} iframes on the page")
            
            for i, iframe in enumerate(iframes):
                src = iframe.get_attribute('src') or ''
                name = iframe.get_attribute('name') or ''
                logger.info(f"Iframe {i}: name='{name}', src='{src[:100] if src else 'No src'}'")
                
                # Try to switch to iframe and get content
                try:
                    self.driver.switch_to.frame(iframe)
                    iframe_content = self.driver.find_element(By.TAG_NAME, 'body').text
                    logger.info(f"Iframe {i} content length: {len(iframe_content)}")
                    if len(iframe_content) > len(all_content):
                        all_content = iframe_content
                        logger.info(f"Iframe {i} has more content, using it")
                    self.driver.switch_to.default_content()
                except Exception as e:
                    logger.info(f"Error accessing iframe {i}: {e}")
                    self.driver.switch_to.default_content()
            
            # Debug: Check page source for clues
            page_source = self.driver.page_source
            logger.info(f"Page source length: {len(page_source)}")
            
            # Look for specific patterns that might indicate content loading
            if 'AD_2' in page_source:
                logger.info("Found 'AD_2' in page source")
            if 'LFBA' in page_source:
                logger.info("Found airport code in page source")
            if 'Operational' in page_source or 'Horaire' in page_source:
                logger.info("Found operational/hours keywords in page source")
            
            # Extract airport information
            logger.info("Extracting airport information")
            
            # Store the collected content in a way that extraction methods can use
            # We'll need to pass it to the extraction methods
            
            # For now, extract from all_content if we have it
            # Store it temporarily in the driver element
            # If no content was found, return a helpful error message
            if len(all_content) == 0:
                logger.error("No content found on France AIP page")
                logger.error("The France AIP site may require manual navigation or authentication")
                raise Exception(
                    f"Could not access France AIP data for {airport_code}. "
                    "The site may require authentication or use a different navigation method. "
                    "Please verify access to the France eAIP system."
                )
            
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
    
    def _click_effective_date_link(self) -> bool:
        """Click on the effective date link in the currently effective eAIP table"""
        try:
            # Debug: Get page info
            logger.info(f"Current URL: {self.driver.current_url}")
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text
            logger.info(f"Page text length: {len(body_text)}")
            logger.info(f"First 500 chars: {body_text[:500]}")
            
            # Look for the effective date link (format: "02 OCT 2025")
            date_pattern = r'\d{2}\s+\w{3}\s+\d{4}'
            
            # Try to find the link in the "Currently Effective eAIP" table
            links = self.driver.find_elements(By.TAG_NAME, 'a')
            logger.info(f"Found {len(links)} links on page")
            
            for i, link in enumerate(links):
                text = link.text.strip()
                if text:
                    logger.info(f"Link {i}: {text}")
                if re.match(date_pattern, text):
                    logger.info(f"Found effective date link: {text}")
                    link.click()
                    time.sleep(2)
                    return True
            
            logger.error("Could not find effective date link")
            return False
            
        except Exception as e:
            logger.error(f"Error clicking effective date link: {e}")
            return False
    
    def _navigate_to_ad2_aerodromes(self) -> bool:
        """Navigate to AD 2 AÉRODROMES in the left menu"""
        try:
            time.sleep(2)
            
            # Look for "AD 2 AÉRODROMES" link
            all_links = self.driver.find_elements(By.TAG_NAME, 'a')
            for link in all_links:
                text = link.text.strip()
                if 'AD 2 AÉRODROMES' in text or 'AD_2' in link.get_attribute('href'):
                    logger.info(f"Found AD 2 AÉRODROMES link: {text}")
                    link.click()
                    time.sleep(2)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error navigating to AD 2 AÉRODROMES: {e}")
            return False
    
    def _click_airport_link(self, airport_code: str) -> bool:
        """Click on the specific airport link"""
        try:
            time.sleep(2)
            
            links = self.driver.find_elements(By.TAG_NAME, 'a')
            for link in links:
                href = link.get_attribute('href') or ''
                text = link.text.strip()
                
                if airport_code in href or airport_code in text:
                    logger.info(f"Found airport link: {text}")
                    link.click()
                    time.sleep(3)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error clicking airport link: {e}")
            return False
    
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
    
    def _navigate_to_airport(self, airport_code: str):
        """Navigate to airport using the step-by-step approach from screenshots"""
        try:
            # Step 1: Go to eAIP Issues page
            issues_url = "https://www.sia.aviation-civile.gouv.fr/en/aip/html/publications.html"
            logger.info("Step 1: Navigating to eAIP Issues page")
            self.driver.get(issues_url)
            time.sleep(3)
            
            # Step 2: Click on effective date (02 OCT 2025)
            logger.info("Step 2: Clicking effective date link")
            try:
                date_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "02 OCT 2025"))
                )
                date_link.click()
                time.sleep(3)
            except Exception as e:
                logger.warning(f"Could not click effective date: {e}")
            
            # Step 3: Navigate to AD 2 AÉRODROMES
            logger.info("Step 3: Navigating to AD 2 AÉRODROMES")
            try:
                ad2_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "AD 2 AÉRODROMES"))
                )
                ad2_link.click()
                time.sleep(3)
            except Exception as e:
                logger.warning(f"Could not click AD 2 AÉRODROMES: {e}")
            
            # Step 4: Click on specific airport
            logger.info(f"Step 4: Clicking airport {airport_code}")
            try:
                airport_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, airport_code))
                )
                airport_link.click()
                time.sleep(3)
            except Exception as e:
                logger.warning(f"Could not click airport {airport_code}: {e}")
            
            # Step 5: Click on AD 2.2 section
            logger.info("Step 5: Navigating to AD 2.2 section")
            try:
                ad22_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "AD 2.2"))
                )
                ad22_link.click()
                time.sleep(3)
            except Exception as e:
                logger.warning(f"Could not click AD 2.2: {e}")
                
        except Exception as e:
            logger.error(f"Navigation approach failed: {e}")

    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

def main():
    """Test the France AIP scraper"""
    scraper = FranceAIPScraper()
    
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
