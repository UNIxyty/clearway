#!/usr/bin/env python3
"""
Finland AIP scraper using Playwright for better JavaScript handling
Handles the Finnish AIP structure with table-based effective day links
"""

import time
import re
import logging
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright, Browser, Page

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinlandAIPScraperPlaywright:
    def __init__(self):
        """Initialize the Finland AIP scraper with Playwright"""
        self.browser = None
        self.page = None
        self.playwright = None
        self.setup_browser()
    
    def setup_browser(self):
        """Setup Playwright browser with configurable headless mode"""
        self.playwright = sync_playwright().start()
        
        # Always run headless - no browser window should ever open
        headless_mode = True
        
        # Launch Chromium browser instead of Firefox to avoid detection
        try:
            self.browser = self.playwright.chromium.launch(
                headless=headless_mode,  # Always headless - no browser window
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
        except Exception as e:
            logger.warning(f"Could not launch Chromium: {e}, trying Firefox...")
            # Fallback to Firefox if Chromium is not available
            self.browser = self.playwright.firefox.launch(
                headless=True,  # Always headless - no browser window
                args=[
                    '--width=1920',
                    '--height=1080',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
        
        # Create new page with JavaScript enabled
        self.page = self.browser.new_page()
        
        # Set realistic headers to avoid detection
        self.page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Enable JavaScript explicitly
        self.page.add_init_script("""
            // Ensure JavaScript is enabled and hide automation
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
        # Set viewport and timeout
        self.page.set_viewport_size({"width": 1920, "height": 1080})
        self.page.set_default_timeout(30000)
        
        logger.info("Playwright browser initialized for Finland AIP with anti-detection measures")
    
    def _discover_airports(self) -> List[str]:
        """Discover all available airports from the navigation menu"""
        try:
            logger.info("Discovering airports from navigation menu...")
            
            # Navigate to the effective day page
            effective_day_url = "https://www.ais.fi/eaip/005-2025_2025_10_02/index.html"
            logger.info(f"Navigating to effective day page: {effective_day_url}")
            self.page.goto(effective_day_url, wait_until="networkidle")
            
            # Wait for the page to load
            self.page.wait_for_timeout(3000)
            
            # Get all frames
            frames = self.page.frames
            logger.info(f"Found {len(frames)} frames on the effective day page")
            
            # Check all frames for the navigation div
            nav_frame = None
            nav_div = None
            
            for frame in frames:
                try:
                    # Check if this frame has the navigation div
                    nav_div_check = frame.query_selector('#eAISNav')
                    if nav_div_check:
                        nav_frame = frame
                        nav_div = nav_div_check
                        logger.info(f"Found navigation div in frame: {frame.name}")
                        break
                except Exception as e:
                    logger.debug(f"Could not check frame {frame.name} for navigation div: {e}")
                    continue
            
            # If navigation div found, use it to extract airports
            if nav_div and nav_frame:
                logger.info("Found navigation div with airport links")
                
                # Extract all airport links from the navigation div
                airport_links = nav_frame.query_selector_all('#eAISNav a[href*="EF"]')
                logger.info(f"Found {len(airport_links)} airport links in navigation")
                
                airports = []
                for link in airport_links:
                    try:
                        href = link.get_attribute('href')
                        if href and 'EF' in href:
                            # Extract airport code from href - handle multiple formats:
                            # - Simple: "EFHK.html" -> "EFHK"
                            # - Complex: "EF-AD%202%20EFHK%20-%20HELSINKI-VANTAA%201-fi-FI.html" -> "EFHK"
                            # - With path: "eAIP/EF-AD%202%20EFHK..." -> "EFHK"
                            
                            # Try to find EF followed by 2 letters (airport code pattern)
                            match = re.search(r'EF[A-Z]{2}', href.upper())
                            if match:
                                airport_code = match.group(0)
                                if len(airport_code) == 4:
                                    airports.append(airport_code)
                    except Exception as e:
                        logger.debug(f"Error extracting airport from link: {e}")
                        continue
                
                if airports:
                    airports = sorted(list(set(airports)))
                    logger.info(f"Discovered {len(airports)} airports from navigation: {airports[:10]}...")
                    return airports
            
            # Fallback: search for airport links in the content
            logger.info("Navigation div not found, searching for airport links in content...")
            
            # Find content frame for fallback
            content_frame = None
            for frame in frames:
                try:
                    frame_text = frame.content()
                    if len(frame_text) > 100000:  # Look for frame with substantial content
                        content_frame = frame
                        logger.info(f"Found content frame for fallback: {frame.name}")
                        break
                except Exception as e:
                    logger.debug(f"Could not get content from frame {frame.name}: {e}")
                    continue
            
            if not content_frame:
                logger.warning("No content frame found, using main page")
                content_frame = self.page
            
            airport_links = content_frame.query_selector_all('a[href*="EF"]')
            logger.info(f"Found {len(airport_links)} airport links in content")
            
            airports = []
            for link in airport_links[:1000]:  # Limit to first 1000 links for speed
                try:
                    href = link.get_attribute('href')
                    if href and 'EF' in href:
                        # Extract airport code from href using regex pattern
                        match = re.search(r'EF[A-Z]{2}', href.upper())
                        if match:
                            airport_code = match.group(0)
                            if len(airport_code) == 4:
                                airports.append(airport_code)
                except Exception as e:
                    logger.debug(f"Error extracting airport from link: {e}")
                    continue
            
            airports = sorted(list(set(airports)))
            logger.info(f"Discovered {len(airports)} airports: {airports[:10]}...")
            return airports
            
        except Exception as e:
            logger.error(f"Error discovering airports: {e}")
            return []

    def get_all_airports(self) -> List[str]:
        """Get all available airports"""
        return self._discover_airports()

    def get_airport_info(self, airport_code: str) -> Dict:
        """
        Get airport information from Finnish AIP
        
        Args:
            airport_code: 4 letter airport code (e.g., 'EFHK', 'EFTU')
            
        Returns:
            Dictionary containing airport information
        """
        airport_code = airport_code.upper().strip()
        
        logger.info(f"Fetching Finland AIP information for {airport_code}")
        
        try:
            # Step 1: Navigate to the base AIP directory
            logger.info(f"Step 1: Navigating to base AIP directory")
            main_url = "https://www.ais.fi/eaip/"
            self.page.goto(main_url, wait_until="networkidle")
            time.sleep(3)
            logger.info(f"Main page loaded. Current URL: {self.page.url}")
            
            if "0.0.7.128" in self.page.url:
                logger.error(f"Main page redirected to IP: {self.page.url}")
                raise Exception(f"Main page redirected to IP address")
            
            # Step 2: Click effective day link
            logger.info(f"Step 2: Clicking effective day link")
            effective_day_link = self.page.locator("a:has-text('02 Oct 2025')").first
            if effective_day_link.is_visible():
                effective_day_link.click()
                self.page.wait_for_load_state("networkidle")
                time.sleep(3)
                logger.info(f"Effective day page loaded. Current URL: {self.page.url}")
                
                if "0.0.7.128" in self.page.url:
                    logger.error(f"Effective day page redirected to IP: {self.page.url}")
                    raise Exception(f"Effective day page redirected to IP address")
            else:
                raise Exception("Could not find effective day link")
            
            # Step 3: Find airport link in navigation frame
            logger.info(f"Step 3: Looking for {airport_code} link in navigation frame")
            
            # Look for links containing the airport code
            # Find navigation frame
            frames = self.page.frames
            nav_frame = None
            for frame in frames:
                if frame.name == 'eAISNavigation':
                    nav_frame = frame
                    logger.info(f"Found navigation frame: {frame.name}")
                    break
            
            if not nav_frame:
                raise Exception("Could not find eAISNavigation frame")
            
            # Find airport links in navigation frame
            airport_links = nav_frame.query_selector_all(f'a[href*="{airport_code}"][href*="eAIP"]')
            if not airport_links:
                airport_links = nav_frame.query_selector_all(f'a[href*="{airport_code}"]')
            logger.info(f"Found {len(airport_links)} links containing {airport_code}")
            
            if airport_links:
                # Get the first link (all point to the same AIP page)
                href = airport_links[0].get_attribute('href')
                logger.info(f"Found {airport_code} AIP URL: {href}")
                
                # Make absolute URL
                if not href.startswith('http'):
                    base_url = "https://www.ais.fi/eaip/005-2025_2025_10_02/eAIP/"
                    if href.startswith('/'):
                        href = f"https://www.ais.fi{href}"
                    else:
                        href = base_url + href.lstrip('/')
                
                logger.info(f"Absolute AIP URL: {href}")
                
                # Step 4: Navigate to AIP page
                logger.info(f"Step 4: Navigating to AIP page")
                self.page.goto(href, wait_until="networkidle")
                time.sleep(3)
                logger.info(f"AIP page loaded. Current URL: {self.page.url}")
                
                if "0.0.7.128" in self.page.url:
                    logger.error(f"AIP page redirected to IP: {self.page.url}")
                    raise Exception(f"AIP page redirected to IP address")
            else:
                raise Exception(f"Could not find airport link for {airport_code} in navigation frame")
            
            # Accept cookies if present
            try:
                accept_button = self.page.locator("button:has-text('Accept')")
                if accept_button.is_visible():
                    accept_button.click()
                    time.sleep(2)
                    logger.info("Accepted cookies")
            except:
                logger.info("No cookie banner found")
            
            # Step 3: Extract content from AIP page (contains both Finnish and English)
            logger.info("Step 3: Extracting content from AIP page")
            
            # Wait for the AIP page to load completely
            self.page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            # Get content from the main page (AIP pages are usually single page, not frameset)
            try:
                body_text = self.page.text_content("body")
                page_content = self.page.content()
                logger.info(f"Extracted content from AIP page: {len(body_text)} characters")
            except Exception as e:
                logger.warning(f"Could not get content from AIP page: {e}")
                # Fallback: try to get content from frames if any
                frames = self.page.frames
                content_frame = None
                max_content_length = 0
                
                for frame in frames:
                    try:
                        frame_text = frame.content()
                        if len(frame_text) > max_content_length:
                            max_content_length = len(frame_text)
                            content_frame = frame
                    except Exception as e:
                        logger.debug(f"Could not get content from frame {frame.name}: {e}")
                        continue
                
                if content_frame:
                    body_text = content_frame.text_content("body")
                    page_content = content_frame.content()
                    logger.info(f"Extracted content from frame: {len(body_text)} characters")
                else:
                    body_text = "Content extraction failed"
                    page_content = ""
            
            airport_info = {
                'airportCode': airport_code,
                'airportName': self._extract_airport_name_from_text(body_text, airport_code),
                'towerHours': self._extract_operational_hours_from_text(body_text),
                'contacts': self._extract_contacts_from_text(body_text)
            }
            
            logger.info(f"Successfully extracted information for {airport_code}")
            return airport_info
            
        except Exception as e:
            logger.error(f"Error fetching airport information for {airport_code}: {e}")
            raise Exception(f"Failed to fetch airport information: {str(e)}")
    
    def _extract_airport_name_from_text(self, text: str, airport_code: str) -> str:
        """Extract airport name from text content (Estonia-style)"""
        try:
            # Look for the "AERODROME LOCATION INDICATOR AND NAME" section
            upper = text.upper()
            start_idx = upper.find('AERODROME LOCATION INDICATOR AND NAME')
            if start_idx == -1:
                start_idx = upper.find('AD 2.1')
            
            if start_idx != -1:
                # Find the end of this section
                end_idx = upper.find('AD 2.2', start_idx)
                if end_idx == -1:
                    end_idx = start_idx + 500  # Fallback
                
                name_section = text[start_idx:end_idx]
                
                # Look for pattern like "EFHK — HELSINKI-VANTAA"
                code_upper = airport_code.upper()
                
                # Pattern: CODE — NAME (with optional additional info)
                name_pattern = rf'{re.escape(code_upper)}\s*[—–-]\s*(.+?)(?=\s*{re.escape(code_upper)})'
                name_match = re.search(name_pattern, name_section, re.IGNORECASE)
                
                if name_match:
                    airport_name = name_match.group(1).strip()
                    # Clean up the name - remove extra whitespace and common suffixes
                    airport_name = re.sub(r'\s+', ' ', airport_name)
                    airport_name = re.sub(r'\s*(lentokenttä|Airport|Aerodrome)$', '', airport_name, flags=re.IGNORECASE)
                    # Remove any remaining AD 2.2 or similar text
                    airport_name = re.sub(r'\s*AD\s*2\.\d+.*$', '', airport_name, flags=re.IGNORECASE)
                    # Remove any remaining airport code duplicates
                    airport_name = re.sub(rf'\s*{re.escape(code_upper)}.*$', '', airport_name, flags=re.IGNORECASE)
                    # Remove trailing slash and clean up
                    airport_name = airport_name.rstrip(' /').strip()
                    return f"{code_upper} — {airport_name}"
            
            # Fallback: try to find any line with the airport code
            lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
            code_upper = airport_code.upper()
            
            for line in lines[:50]:  # Check first 50 lines
                if code_upper in line and len(line) <= 150:
                    # Look for dash or em dash pattern
                    if '—' in line or '–' in line or '-' in line:
                        return line.strip()
                    # If no dash, return the line if it looks like a name
                    elif any(ch.isalpha() for ch in line.replace(code_upper, '')):
                        return line.strip()
            
            # Final fallback
            return airport_code.upper()
            
        except Exception as e:
            logger.warning(f"Error extracting airport name: {e}")
            return airport_code.upper()
    
    def _extract_operational_hours_from_text(self, text: str) -> List[Dict]:
        """Extract operational hours from AD 2.3 TOIMINTA-AJAT section"""
        results: List[Dict] = []
        # Look specifically for the Finnish section "AD 2.3 TOIMINTA-AJAT"
        upper = text.upper()
        start_idx = upper.find('AD 2.3 TOIMINTA-AJAT')
        if start_idx == -1:
            # Fallback to English section
            start_idx = upper.find('AD 2.3 OPERATIONAL HOURS')
        if start_idx == -1:
            # Additional fallbacks
            start_idx = upper.find('TOIMINTA-AJAT')
        if start_idx == -1:
            start_idx = upper.find('KÄYTTÖAJAT')
        if start_idx == -1:
            start_idx = upper.find('OPERATIONAL HOURS')
        
        # Find the end of this section (next AD 2.4 section)
        end_idx = upper.find('AD 2.4', start_idx) if start_idx != -1 else -1
        if end_idx == -1:
            end_idx = upper.find('AD 2.5', start_idx) if start_idx != -1 else -1
        if end_idx == -1:
            end_idx = start_idx + 2000 if start_idx != -1 else -1  # Fallback: take next 2000 chars
        
        segment = text[start_idx:end_idx] if start_idx != -1 and end_idx != -1 else text

        # Parse the structured table format
        lines = [ln.strip() for ln in segment.split('\n') if ln.strip()]
        
        # Comprehensive bilingual service scan to extract all rows like in the table
        # This complements the structured parsing below and ensures captions are always present
        try:
            service_synonyms = {
                "Aerodrome operator": [r"^Lentopaikan\s+pitäjä", r"^Aerodrome\s+operator", r"^AD\s+operator"],
                "Customs and immigration": [r"^CUST,?\s*IMG", r"^Customs\s+and\s+immigration"],
                "Health and sanitation": [r"^Terveystarkastus", r"^Health\s+and\s+sanitation"],
                "AIS": [r"^AIS\s*$", r"^AIS\b"],
                "AIS Briefing Office": [r"^AIS\s+Briefing\s+Office"],
                "ATS Reporting Office (ARO)": [r"^ARO\b", r"^ATS\s+Reporting\s+Office"],
                "MET": [r"^MET\s*$", r"^MET\b"],
                "MET Briefing Office": [r"^MET\s+Briefing\s+Office"],
                "ATS": [r"^ATS\s*$", r"^ATS\b"],
                "Fuelling": [r"^Polttoaineiden\s+jakelu", r"^Tankkauspyynnöt", r"^Fuelling", r"^Refuelling\s+requests"],
                "Handling": [r"^Tavaran\s+käsittely", r"^Handling"],
                "Security": [r"^Turvatarkastus", r"^Security"],
                "De-icing": [r"^Jäänpoisto", r"^De-icing"],
                "RMK": [r"^RMK\b"]
            }

            # Helper to detect if a line looks like the start of a new numbered row
            def is_row_break(text_line: str) -> bool:
                return bool(re.match(r"^\d{1,2}\s", text_line))

            # Build a quick index of line positions for synonym matches
            line_count = len(lines)
            found_blocks = {}
            for idx, line in enumerate(lines):
                for caption, patterns in service_synonyms.items():
                    for pat in patterns:
                        if re.search(pat, line, re.IGNORECASE):
                            # Record the earliest index for this caption
                            if caption not in found_blocks:
                                found_blocks[caption] = idx
                            break

            # Extract content for each found caption window
            for caption, start_idx in found_blocks.items():
                # Collect a window of subsequent lines until next service or numbered row
                window_lines = []
                j = start_idx + 1
                while j < line_count:
                    next_line = lines[j]
                    # Stop if we hit another service caption or a numbered row
                    other_service = False
                    for other_caption, patterns in service_synonyms.items():
                        if other_caption == caption:
                            continue
                        for pat in patterns:
                            if re.search(pat, next_line, re.IGNORECASE):
                                other_service = True
                                break
                        if other_service:
                            break
                    if other_service or is_row_break(next_line):
                        break
                    window_lines.append(next_line)
                    # Limit window to avoid runaway
                    if len(window_lines) >= 8:
                        break
                    j += 1

                # Parse hours and notes from window
                window_text = " \n".join(window_lines)
                hours_text = None

                # Specific patterns first
                twr_match = re.search(r"TWR\s*:\s*(H24|24H)", window_text, re.IGNORECASE)
                if caption == "ATS" and twr_match:
                    hours_text = f"TWR: {twr_match.group(1).upper()}"

                if hours_text is None:
                    if re.search(r"\bNIL\b", window_text, re.IGNORECASE):
                        hours_text = "NIL"
                    elif re.search(r"\b(H24|24H|24\s*HR)\b", window_text, re.IGNORECASE):
                        hours_text = "H24"
                    else:
                        # Day range with times
                        dtm = re.search(r"(MON|TUE|WED|THU|FRI|SAT|SUN)(?:[-–](MON|TUE|WED|THU|FRI|SAT|SUN))?\s*:?\s*(\d{2}[:.]?\d{2})\s*[-–]\s*(\d{2}[:.]?\d{2})", window_text, re.IGNORECASE)
                        if dtm:
                            day_start = dtm.group(1).upper()
                            day_end = dtm.group(2)
                            t1 = dtm.group(3).replace('.', ':')
                            t2 = dtm.group(4).replace('.', ':')
                            day_range = f"{day_start}-{day_end.upper()}" if day_end else day_start
                            hours_text = f"{day_range} {t1}-{t2}"

                # Only output hours; do not append phones, emails, URLs
                final_hours = hours_text if hours_text else ("Hours information not available")

                results.append({
                    "day": caption,
                    "hours": final_hours
                })
        except Exception as _e:
            # Do not fail overall parsing if the comprehensive scan has issues
            pass

        # Look for the specific service patterns with their hours
        service_patterns = [
            (r'AD\s+operator[:\s]*', r'(MON|TUE|WED|THU|FRI|SAT|SUN)(?:[-–](MON|TUE|WED|THU|FRI|SAT|SUN))?\s*[:\-]?\s*(\d{2}[:.]?\d{2})\s*[-–]\s*(\d{2}[:.]?\d{2})'),
            (r'AD\s+Operational\s+hours[:\s]*', r'(H24|24H|24\s*HR)'),
            (r'Customs\s+and\s+immigration[:\s]*', r'(H24|24H|24\s*HR)'),
            (r'Health\s+and\s+sanitation[:\s]*', r'(H24|24H|24\s*HR)'),
            (r'AIS\s+Briefing\s+Office[:\s]*', r'(H24|24H|24\s*HR)'),
            (r'ATS\s+Reporting\s+Office[:\s]*', r'(H24|24H|24\s*HR)'),
            (r'MET\s+Briefing\s+Office[:\s]*', r'(H24|24H|24\s*HR|NIL)'),
            (r'ATS[:\s]*', r'(H24|24H|24\s*HR)'),
            (r'Fuelling[:\s]*', r'(H24|24H|24\s*HR)'),
            (r'Handling[:\s]*', r'(H24|24H|24\s*HR)'),
            (r'Security[:\s]*', r'(H24|24H|24\s*HR)'),
            (r'De-icing[:\s]*', r'(H24|24H|24\s*HR)')
        ]
        
        # First, look for the main operational hours line that contains all services
        operational_hours_line = None
        for line in lines:
            if 'OPERATIONAL HOURS' in line.upper() and ('AD OPERATOR' in line.upper() or 'MON-THU' in line.upper() or 'FRI:' in line.upper() or 'MON-FRI' in line.upper()):
                operational_hours_line = line
                break
        
        if operational_hours_line:
            # Extract MON-FRI hours (single range like EETN)
            mon_fri_match = re.search(r'MON-FRI\s*:\s*(\d{2}[:.]?\d{2})\s*[-–]\s*(\d{2}[:.]?\d{2})', operational_hours_line, re.IGNORECASE)
            if mon_fri_match:
                time_start = mon_fri_match.group(1).replace('.', ':')
                time_end = mon_fri_match.group(2).replace('.', ':')
                results.append({
                    "day": "AD Operator Hours (MON-FRI)",
                    "hours": f"{time_start}-{time_end}"
                })
            
            # Extract MON-THU hours (separate range like EEEI)
            mon_thu_match = re.search(r'MON-THU:\s*(\d{2}[:.]?\d{2})\s*[-–]\s*(\d{2}[:.]?\d{2})', operational_hours_line, re.IGNORECASE)
            if mon_thu_match:
                time_start = mon_thu_match.group(1).replace('.', ':')
                time_end = mon_thu_match.group(2).replace('.', ':')
                results.append({
                    "day": "AD Operator Hours (MON-THU)",
                    "hours": f"{time_start}-{time_end}"
                })
            
            # Extract FRI hours (separate range like EEEI)
            fri_match = re.search(r'FRI:\s*(\d{2}[:.]?\d{2})\s*[-–]\s*(\d{2}[:.]?\d{2})', operational_hours_line, re.IGNORECASE)
            if fri_match:
                time_start = fri_match.group(1).replace('.', ':')
                time_end = fri_match.group(2).replace('.', ':')
                results.append({
                    "day": "AD Operator Hours (FRI)",
                    "hours": f"{time_start}-{time_end}"
                })
            
            # Extract individual services that are actually present in the document
            # Parse each service individually based on the actual document structure
            
            # 2Customs and immigration - May be requested with PPR
            customs_match = re.search(r'2Customs and immigration.*?(H24|NIL|May be requested)', operational_hours_line, re.IGNORECASE | re.DOTALL)
            if customs_match:
                hours_text = customs_match.group(1)
                if 'May be requested' in hours_text:
                    results.append({
                        "day": "Customs and immigration",
                        "hours": "On request"
                    })
                elif 'H24' in hours_text.upper():
                    results.append({
                        "day": "Customs and immigration",
                        "hours": "H24"
                    })
                elif 'NIL' in hours_text.upper():
                    results.append({
                        "day": "Customs and immigration",
                        "hours": "NIL"
                    })
            
            # 3Health and sanitation - H24
            health_match = re.search(r'3Health and sanitation.*?(H24|NIL)', operational_hours_line, re.IGNORECASE | re.DOTALL)
            if health_match and 'H24' in health_match.group(1).upper():
                results.append({
                    "day": "Health and sanitation",
                    "hours": "H24"
                })
            
            # 4AIS Briefing Office - H24 (MIL)
            ais_match = re.search(r'4AIS Briefing Office.*?(H24|NIL)', operational_hours_line, re.IGNORECASE | re.DOTALL)
            if ais_match and 'H24' in ais_match.group(1).upper():
                results.append({
                    "day": "AIS Briefing Office",
                    "hours": "H24"
                })
            
            # 5ATS Reporting Office (ARO) - NIL
            aro_match = re.search(r'5ATS Reporting Office \(ARO\).*?(H24|NIL)', operational_hours_line, re.IGNORECASE | re.DOTALL)
            if aro_match:
                hours_text = aro_match.group(1)
                if 'NIL' in hours_text.upper():
                    results.append({
                        "day": "ATS Reporting Office (ARO)",
                        "hours": "NIL"
                    })
                elif 'H24' in hours_text.upper():
                    results.append({
                        "day": "ATS Reporting Office (ARO)",
                        "hours": "H24"
                    })
            
            # 6MET Briefing Office - H24
            met_match = re.search(r'6MET Briefing Office.*?(H24|NIL)', operational_hours_line, re.IGNORECASE | re.DOTALL)
            if met_match and 'H24' in met_match.group(1).upper():
                results.append({
                    "day": "MET Briefing Office",
                    "hours": "H24"
                })
            
            # 7ATS - H24
            ats_match = re.search(r'7ATS.*?(H24|NIL)', operational_hours_line, re.IGNORECASE | re.DOTALL)
            if ats_match and 'H24' in ats_match.group(1).upper():
                results.append({
                    "day": "ATS",
                    "hours": "H24"
                })
            
            # 8Fuelling - H24
            fuelling_match = re.search(r'8Fuelling.*?(H24|NIL)', operational_hours_line, re.IGNORECASE | re.DOTALL)
            if fuelling_match and 'H24' in fuelling_match.group(1).upper():
                results.append({
                    "day": "Fuelling",
                    "hours": "H24"
                })
            
            # 9Handling - H24
            handling_match = re.search(r'9Handling.*?(H24|NIL)', operational_hours_line, re.IGNORECASE | re.DOTALL)
            if handling_match and 'H24' in handling_match.group(1).upper():
                results.append({
                    "day": "Handling",
                    "hours": "H24"
                })
            
            # 10Security - H24
            security_match = re.search(r'10Security.*?(H24|NIL)', operational_hours_line, re.IGNORECASE | re.DOTALL)
            if security_match and 'H24' in security_match.group(1).upper():
                results.append({
                    "day": "Security",
                    "hours": "H24"
                })
            
            # 11De-icing - H24
            deicing_match = re.search(r'11De-icing.*?(H24|NIL)', operational_hours_line, re.IGNORECASE | re.DOTALL)
            if deicing_match and 'H24' in deicing_match.group(1).upper():
                results.append({
                    "day": "De-icing",
                    "hours": "H24"
                })
        
        # Fallback: parse line by line if no structured line found
        if not results:
            for line in lines:
                line_upper = line.upper()
                
                # Check each service pattern
                for service_regex, hours_regex in service_patterns:
                    service_match = re.search(service_regex, line_upper)
                    if service_match:
                        # Extract the service name
                        service_name = service_match.group(0).strip().rstrip(':').strip()
                        
                        # Look for hours pattern after the service name
                        hours_match = re.search(hours_regex, line, re.IGNORECASE)
                        if hours_match:
                            if 'H24' in hours_match.group(1).upper() or '24H' in hours_match.group(1).upper():
                                results.append({
                                    "day": service_name,
                                    "hours": "H24"
                                })
                            elif 'NIL' in hours_match.group(1).upper():
                                results.append({
                                    "day": service_name,
                                    "hours": "NIL"
                                })
                            elif len(hours_match.groups()) >= 4:  # Day range with times
                                day_start = hours_match.group(1).upper()
                                day_end = hours_match.group(2)
                                time_start = hours_match.group(3).replace('.', ':')
                                time_end = hours_match.group(4).replace('.', ':')
                                
                                if day_end:
                                    day_range = f"{day_start}-{day_end.upper()}"
                                else:
                                    day_range = day_start
                                
                                results.append({
                                    "day": f"{service_name} ({day_range})",
                                    "hours": f"{time_start}-{time_end}"
                                })
                        break  # Found a match, move to next line
        
        # If no structured data found, fallback to simple patterns
        if not results:
            # Look for any day ranges with times
            day_time_pattern = r'(MON|TUE|WED|THU|FRI|SAT|SUN)(?:[-–](MON|TUE|WED|THU|FRI|SAT|SUN))?\s*[:\-]?\s*(\d{2}[:.]?\d{2})\s*[-–]\s*(\d{2}[:.]?\d{2})'
            for line in lines:
                match = re.search(day_time_pattern, line, re.IGNORECASE)
                if match:
                    day_start = match.group(1).upper()
                    day_end = match.group(2)
                    time_start = match.group(3).replace('.', ':')
                    time_end = match.group(4).replace('.', ':')
                    
                    if day_end:
                        day_range = f"{day_start}-{day_end.upper()}"
                    else:
                        day_range = day_start
                    
                    results.append({
                        "day": day_range,
                        "hours": f"{time_start}-{time_end}"
                    })
            
            # Look for H24 patterns
            if not results:
                h24_pattern = r'\b(H24|24H|24\s*HR)\b'
                for line in lines:
                    if re.search(h24_pattern, line, re.IGNORECASE):
                        # Use a descriptive caption rather than repeating H24
                        results.append({"day": "AD Operational Hours", "hours": "H24"})
                        break
        
        # Deduplicate while preserving order
        unique: List[Dict] = []
        seen = set()
        for r in results:
            key = (r.get('day'), r.get('hours'))
            if key not in seen:
                seen.add(key)
                unique.append(r)
        
        if not unique:
            unique.append({"day": "General", "hours": "Hours information not available"})
        
        return unique
    
    def _extract_contacts_from_text(self, text: str) -> List[Dict]:
        """Extract contact information from AD 2.2 LENTOPAIKAN SIJAINTI JA HALLINTO section"""
        contacts: List[Dict] = []
        
        # Look for the Finnish section "AD 2.2 LENTOPAIKAN SIJAINTI JA HALLINTO"
        upper = text.upper()
        start_idx = upper.find('AD 2.2 LENTOPAIKAN SIJAINTI JA HALLINTO')
        if start_idx == -1:
            # Fallback to English section
            start_idx = upper.find('AD 2.2 AERODROME LOCATION AND ADMINISTRATION')
        
        if start_idx != -1:
            # Find the end of this section (next AD 2.3 section)
            end_idx = upper.find('AD 2.3 TOIMINTA-AJAT', start_idx)
            if end_idx == -1:
                end_idx = upper.find('AD 2.3 OPERATIONAL HOURS', start_idx)
            if end_idx == -1:
                end_idx = start_idx + 3000  # Fallback: take next 3000 chars
            
            ad_section = text[start_idx:end_idx]
            
            # Extract phone numbers from this section
            # Pattern for Finnish phone numbers: +358 followed by digits
            phone_regex = r'(\+358[0-9\s\-]+)'
            phones = re.findall(phone_regex, ad_section)
            
            # Also look for other phone patterns
            phone_regex2 = r'(\+358\s*\d{2,3}\s*\d{3,4}\s*\d{3,4})'
            phones2 = re.findall(phone_regex2, ad_section)
            phones.extend(phones2)
            
            # Clean up phone numbers - remove extra spaces and limit length
            phones = [re.sub(r'\s+', ' ', p.strip()) for p in phones if len(p.strip()) <= 25]
            phones = list(set(phones))  # Remove duplicates
            
            # Extract emails from this section
            email_regex = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            emails = re.findall(email_regex, ad_section)
            
            # Clean up emails - remove any concatenated text after the email
            emails = [re.sub(r'[A-Z]{2,}.*$', '', email) for email in emails]
            emails = list(set(emails))  # Remove duplicates
            
            # Extract organization names (look for patterns like "Finavia Oyj" or similar)
            org_regex = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Oyj|Oy|Ltd|Ltd\.|Inc\.?|Corp\.?|Corporation))'
            orgs = re.findall(org_regex, ad_section)
            orgs = list(set(orgs))  # Remove duplicates
            
            # Create contacts from the AD 2.2 section (using same caption structure as Estonia)
            for i, phone in enumerate(phones[:3]):  # Limit to 3 phone numbers
                contacts.append({
                    "type": f"AD Operator Contact {i+1}",
                    "phone": phone.strip(),
                    "name": orgs[i] if i < len(orgs) else "",
                    "email": emails[i] if i < len(emails) else "",
                    "notes": "From AD operator section"
                })
            
            # Add organization contacts without phone numbers
            for i, org in enumerate(orgs[len(phones):3]):  # Add remaining orgs
                contacts.append({
                    "type": f"AD Operator Contact {len(phones) + i + 1}",
                    "phone": "",
                    "name": org.strip(),
                    "email": emails[len(phones) + i] if len(phones) + i < len(emails) else "",
                    "notes": "From AD operator section"
                })
        
        # If no contacts found in AD 2.2 section, add a placeholder
        if not contacts:
            contacts.append({
                "type": "AD Operator Contact",
                "phone": "",
                "name": "",
                "email": "",
                "notes": "Contact information not available in AD operator section"
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
    """Test the Finland AIP scraper with Playwright"""
    scraper = FinlandAIPScraperPlaywright()
    
    try:
        airport_info = scraper.get_airport_info("EFHK")
        
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
