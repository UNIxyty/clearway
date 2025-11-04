#!/usr/bin/env python3
import re
import time
import logging
from typing import Dict, List

from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EstoniaAIPScraperPlaywright:
	def __init__(self, base_url: str = "https://eaip.eans.ee/2025-10-02/html/index-en-GB.html"):
		self.base_url = base_url
		self.playwright = None
		self.browser = None
		self.page = None
		self.setup_browser()

	def setup_browser(self):
		"""Setup Playwright browser (visible window for validation)."""
		try:
			self.playwright = sync_playwright().start()
			self.browser = self.playwright.chromium.launch(headless=False, args=['--window-size=1600,1000'])
			self.page = self.browser.new_page()
			self.page.set_default_timeout(30000)
			logger.info("Playwright browser initialized for Estonia AIP (visible browser)")
		except Exception as e:
			logger.error(f"Failed to initialize Playwright browser: {e}")
			raise

	def _open_eaip(self):
		logger.info(f"Opening Estonia eAIP: {self.base_url}")
		self.page.goto(self.base_url)
		self.page.wait_for_load_state("networkidle")
		time.sleep(2)

	def _go_to_part3_ad2(self):
		"""Navigate left menu: Part 3 Aerodromes → AD 2."""
		logger.info("Navigating to Part 3 Aerodromes → AD 2")
		
		# Try navigating directly to the frameset URL
		frameset_url = "https://eaip.eans.ee/2025-10-02/html/toc-frameset-en-GB.html"
		logger.info(f"Trying direct navigation to frameset: {frameset_url}")
		
		try:
			self.page.goto(frameset_url)
			self.page.wait_for_load_state("networkidle")
			time.sleep(3)
			
			# Check for frames in the frameset
			frames = self.page.frames
			logger.info(f"Found {len(frames)} frames in frameset")
			
			for frame in frames:
				name = frame.name or ''
				url = frame.url or ''
				logger.info(f"Frame: name='{name}', url='{url[:100]}'")
			
			# Try to find the navigation frame
			nav_frame = None
			for frame in frames:
				name = frame.name or ''
				if 'toc' in name.lower() or 'nav' in name.lower() or 'eaisnavigation' in name.lower():
					nav_frame = frame
					break
			
			if nav_frame:
				logger.info("Found navigation frame in frameset")
				# Wait for frame content to load
				try:
					nav_frame.wait_for_load_state("networkidle")
					time.sleep(2)
				except Exception as e:
					logger.info(f"Frame load state wait failed: {e}")
				
				# Debug: Check what's in the navigation frame
				try:
					nav_text = nav_frame.text_content('body')
					logger.info(f"Navigation frame content length: {len(nav_text)}")
					logger.info(f"Navigation frame preview: {nav_text[:500]}")
					
					# Search for Part 3 in the text
					if 'Part 3' in nav_text:
						logger.info("Found 'Part 3' in navigation text")
						# Find the position and show more context
						pos = nav_text.find('Part 3')
						logger.info(f"Part 3 context: {nav_text[pos-50:pos+200]}")
					else:
						logger.info("'Part 3' not found in navigation text")
					
					if 'AERODROMES' in nav_text:
						logger.info("Found 'AERODROMES' in navigation text")
						# Find the position and show more context
						pos = nav_text.find('AERODROMES')
						logger.info(f"AERODROMES context: {nav_text[pos-100:pos+200]}")
					else:
						logger.info("'AERODROMES' not found in navigation text")
					
					# Try to find any text containing "3" and "AERODROMES"
					import re
					pattern = r'.*3.*AERODROMES.*'
					matches = re.findall(pattern, nav_text, re.IGNORECASE)
					if matches:
						logger.info(f"Found pattern matches: {matches}")
					else:
						logger.info("No pattern matches found")
						
				except Exception as e:
					logger.info(f"Could not get navigation frame content: {e}")
				
				# Expand Part 3 Aerodromes - try different selectors
				try:
					# Try just "AERODROMES" first
					part3_link = nav_frame.locator("//a[contains(., 'AERODROMES')]").first
					part3_link.click()
					time.sleep(1)
					logger.info("Opened AERODROMES section")
				except Exception as e:
					logger.info(f"Could not click AERODROMES directly: {e}; trying alternative selectors")
					# Try any element containing AERODROMES
					links = nav_frame.locator("//*[contains(text(), 'AERODROMES')]")
					if links.count() > 0:
						links.first.click()
						time.sleep(1)
						logger.info("Clicked AERODROMES element")
					else:
						logger.info("No AERODROMES elements found")

				# No need to click AD 2 - it's just a section header
				# The airport codes are directly clickable
				logger.info("AD 2 section is now visible with airport codes")
				
			else:
				logger.error("No navigation frame found in frameset")
				raise Exception("No navigation frame found")
				
		except Exception as e:
			logger.error(f"Failed to navigate to frameset: {e}")
			raise

	def _open_airport(self, airport_code: str):
		"""Navigate directly to airport page using the href URL."""
		airport_code = airport_code.upper().strip()
		logger.info(f"Navigating directly to airport {airport_code} page")
		
		# Construct the direct URL to the airport page
		# From the href we saw: "../eAIP/EE-AD-2.EETN-en-GB.html#AD-2.EETN"
		airport_url = f"https://eaip.eans.ee/2025-10-02/html/eAIP/EE-AD-2.{airport_code}-en-GB.html#AD-2.{airport_code}"
		logger.info(f"Direct URL: {airport_url}")
		
		try:
			# Navigate directly to the airport page
			self.page.goto(airport_url)
			self.page.wait_for_load_state("networkidle")
			time.sleep(2)
			logger.info(f"Successfully navigated to {airport_code} page")
		except Exception as e:
			logger.error(f"Failed to navigate to {airport_code} page: {e}")
			raise Exception(f"Failed to navigate to airport {airport_code} page")

	def _extract_sections_text(self) -> str:
		"""Return visible text of current content page."""
		# Try to find content frame
		content_frame = None
		for frame in self.page.frames:
			name = frame.name or ''
			if 'content' in name.lower() or 'eaiscontent' in name.lower():
				content_frame = frame
				break
		
		if content_frame:
			logger.info("Using content frame for text extraction")
			text = content_frame.text_content('body')
		else:
			logger.info("Using main page for text extraction")
			text = self.page.text_content('body')
		
		logger.info(f"Content length: {len(text)}")
		logger.info(f"Preview: {text[:600]}")
		return text

	def _parse_operational_hours(self, text: str) -> List[Dict]:
		results: List[Dict] = []
		# Look for AD 2.2 OPERATIONAL HOURS block; fallback to any 'OPERATIONAL HOURS'
		upper = text.upper()
		start_idx = upper.find('AD 2.2')
		if start_idx == -1:
			start_idx = upper.find('OPERATIONAL HOURS')
		end_idx = upper.find('AD 2.3') if start_idx != -1 else -1
		segment = text[start_idx:end_idx] if start_idx != -1 and end_idx != -1 else text

		# Common patterns: H24, 24 HR, times like 0700-1700, 07:00-17:00, MON-FRI etc.
		patterns = [
			r"H\s*24|24H|24\s*HR|H24",
			r"(?:MON|TUE|WED|THU|FRI|SAT|SUN|MON-FRI|SAT-SUN|DAILY)\s*[:\-]?\s*(\d{2}[:.]?\d{2})\s*[-–]\s*(\d{2}[:.]?\d{2})",
			r"(\d{3,4})\s*[-–]\s*(\d{3,4})",
		]
		for pat in patterns:
			for m in re.finditer(pat, segment, flags=re.IGNORECASE):
				val = m.group(0)
				results.append({"day": "General", "hours": val.replace('.', ':')})
		if not results:
			results.append({"day": "General", "hours": "Hours information not available"})
		return results

	def _parse_contacts(self, text: str) -> List[Dict]:
		contacts: List[Dict] = []
		upper = text.upper()
		start_idx = upper.find('AD 2.3')
		if start_idx == -1:
			start_idx = upper.find('AERODROME GEOGRAPHICAL AND ADMINISTRATIVE DATA')
		end_idx = upper.find('AD 2.4') if start_idx != -1 else -1
		segment = text[start_idx:end_idx] if start_idx != -1 and end_idx != -1 else text

		phone_regex = r"(?:\+?372|\+?\d{1,3})?\s*(?:\(\d+\)\s*)?(?:\d[\s-]?){6,}"
		emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", segment)
		phones = [p.strip() for p in re.findall(phone_regex, segment) if len(p.strip()) >= 7]
		for i, ph in enumerate(phones[:3]):
			contacts.append({"type": f"Contact {i+1}", "phone": ph, "name": "", "email": emails[i] if i < len(emails) else "", "notes": ""})
		if not contacts:
			contacts.append({"type": "General Contact", "phone": "", "name": "", "email": emails[0] if emails else "", "notes": "Contact information not available"})
		return contacts

	def get_airport_info(self, airport_code: str) -> Dict:
		self._open_eaip()
		self._go_to_part3_ad2()
		self._open_airport(airport_code)
		text = self._extract_sections_text()
		info = {
			"airportCode": airport_code.upper(),
			"towerHours": self._parse_operational_hours(text),
			"contacts": self._parse_contacts(text)
		}
		logger.info(f"Extracted data for {airport_code}")
		return info

	def close(self):
		if self.browser:
			self.browser.close()
		if self.playwright:
			self.playwright.stop()
		logger.info("Playwright browser closed")


def main():
	scraper = EstoniaAIPScraperPlaywright()
	try:
		# Example: Tallinn EETN
		result = scraper.get_airport_info("EETN")
		print("\n=== RESULTS ===")
		print(result)
	except Exception as e:
		print(f"Error: {e}")
	finally:
		scraper.close()

if __name__ == "__main__":
	main()
