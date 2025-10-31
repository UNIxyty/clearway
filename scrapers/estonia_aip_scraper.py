#!/usr/bin/env python3
import re
import time
import logging
from typing import Dict, List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EstoniaAIPScraper:
	def __init__(self, base_url: str = "https://eaip.eans.ee/2025-10-02/html/index-en-GB.html"):
		self.base_url = base_url
		self.driver = None
		self.setup_driver()

	def setup_driver(self):
		"""Setup Chrome WebDriver (visible window for validation)."""
		options = Options()
		options.add_argument("--no-sandbox")
		options.add_argument("--disable-dev-shm-usage")
		options.add_argument("--disable-gpu")
		options.add_argument("--disable-extensions")
		options.add_argument("--window-size=1600,1000")
		options.page_load_strategy = 'eager'
		# Visible browser to observe navigation
		try:
			service = Service(ChromeDriverManager().install())
			self.driver = webdriver.Chrome(service=service, options=options)
			self.driver.set_page_load_timeout(30)
			self.driver.implicitly_wait(5)
			logger.info("WebDriver initialized for Estonia AIP (visible browser)")
		except Exception as e:
			logger.error(f"Failed to initialize WebDriver: {e}")
			raise

	def _open_eaip(self):
		logger.info(f"Opening Estonia eAIP: {self.base_url}")
		self.driver.get(self.base_url)
		WebDriverWait(self.driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
		time.sleep(2)

	def _go_to_part3_ad2(self):
		"""Navigate left menu: Part 3 Aerodromes → AD 2."""
		logger.info("Navigating to Part 3 Aerodromes → AD 2")
		# The TOC is typically in a left frame; try to switch if frames exist
		frames = self.driver.find_elements(By.TAG_NAME, 'frame')
		if frames:
			logger.info(f"Found {len(frames)} frames; trying TOC frame")
			# Heuristic: the TOC frame often has 'toc' in name/src
			for i, f in enumerate(frames):
				src = f.get_attribute('src') or ''
				name = f.get_attribute('name') or ''
				if 'toc' in src.lower() or 'nav' in name.lower() or 'eaisnavigation' in name.lower():
					self.driver.switch_to.frame(f)
					logger.info(f"Switched to TOC frame {i}")
					break
			else:
				self.driver.switch_to.frame(frames[0])
				logger.info("Switched to first frame as fallback")

		# Expand Part 3 Aerodromes
		try:
			part3_link = WebDriverWait(self.driver, 15).until(
				EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Part 3') and contains(., 'Aerodromes')]"))
			)
			part3_link.click()
			time.sleep(1)
			logger.info("Opened Part 3 Aerodromes")
		except Exception as e:
			logger.info(f"Could not click Part 3 directly: {e}; trying alternative selectors")
			# Sometimes entries are spans or different anchors
			links = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Part 3') and contains(text(), 'Aerodromes')]")
			if links:
				self.driver.execute_script("arguments[0].click();", links[0])
				time.sleep(1)

		# Click AD 2
		try:
			ad2_link = WebDriverWait(self.driver, 15).until(
				EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'AD 2')]"))
			)
			ad2_link.click()
			time.sleep(1)
			logger.info("Opened AD 2")
		except Exception as e:
			logger.error(f"Failed to open AD 2: {e}")
			raise

		# Return to main content (content usually in another frame)
		self.driver.switch_to.default_content()
		content_frame = None
		frames = self.driver.find_elements(By.TAG_NAME, 'frame')
		for f in frames:
			src = f.get_attribute('src') or ''
			name = f.get_attribute('name') or ''
			if 'content' in name.lower() or 'content' in src.lower() or 'eaiscontent' in name.lower():
				content_frame = f
				break
		if content_frame:
			self.driver.switch_to.frame(content_frame)
			logger.info("Switched to content frame")
			time.sleep(1)

	def _open_airport(self, airport_code: str):
		"""Click airport code in AD 2 list."""
		airport_code = airport_code.upper().strip()
		logger.info(f"Selecting airport {airport_code}")
		try:
			link = WebDriverWait(self.driver, 15).until(
				EC.element_to_be_clickable((By.XPATH, f"//a[normalize-space()='{airport_code}']"))
			)
			link.click()
			time.sleep(2)
		except Exception as e:
			logger.error(f"Airport link not found for {airport_code}: {e}")
			raise

	def _extract_sections_text(self) -> str:
		"""Return visible text of current content page."""
		WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
		text = self.driver.find_element(By.TAG_NAME, 'body').text
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
		if self.driver:
			self.driver.quit()
			logger.info("WebDriver closed")


def main():
	scraper = EstoniaAIPScraper()
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
