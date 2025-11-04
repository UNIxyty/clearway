#!/usr/bin/env python3
import re
import time
import logging
from typing import Dict, List

from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EurocontrolGenericScraper:
	"""Generic scraper for Eurocontrol-style eAIP sites using Playwright.

	Strategy:
	- Open the country's eAIP index URL
	- Find anchor to AD 2 airport page by pattern: <CC>-AD-2.<ICAO>
	- Navigate to that page, then parse AD 2.2 and AD 2.3 text
	"""

	def __init__(self, index_url: str, headless: bool = False):
		self.index_url = index_url
		self.headless = headless
		self.playwright = None
		self.browser = None
		self.page = None
		self._setup()

	def _setup(self):
		self.playwright = sync_playwright().start()
		self.browser = self.playwright.chromium.launch(headless=self.headless, args=['--window-size=1600,1000'])
		self.page = self.browser.new_page()
		self.page.set_default_timeout(30000)

	def close(self):
		if self.browser:
			self.browser.close()
		if self.playwright:
			self.playwright.stop()

	def _goto_index(self):
		logger.info(f"Opening index: {self.index_url}")
		self.page.goto(self.index_url)
		try:
			self.page.wait_for_load_state("networkidle")
		except Exception:
			time.sleep(1)

	def _find_airport_href(self, airport_code: str) -> str:
		cc = airport_code[:2].upper()
		pattern = f"{cc}-AD-2.{airport_code.upper()}"
		logger.info(f"Searching link by pattern: {pattern}")
		# Try to find any anchor containing the pattern
		loc = self.page.locator(f"a[href*='{pattern}']").first
		if loc and loc.count() > 0:
			href = loc.get_attribute('href')
			if href:
				return href
		# Fallback: try text search
		loc2 = self.page.locator(f"//a[contains(., '{airport_code.upper()}') and contains(@href, 'AD-2')]").first
		if loc2 and loc2.count() > 0:
			href = loc2.get_attribute('href')
			if href:
				return href
		raise Exception(f"Could not find airport link for {airport_code}")

	def _abs_url(self, href: str) -> str:
		if href.startswith('http://') or href.startswith('https://'):
			return href
		base = self.page.url
		if href.startswith('/'):
			m = re.match(r'^(https?://[^/]+)', base)
			return (m.group(1) if m else '').rstrip('/') + href
		# relative
		return base.rsplit('/', 1)[0] + '/' + href

	def _open_airport_page(self, airport_code: str):
		href = self._find_airport_href(airport_code)
		url = self._abs_url(href)
		logger.info(f"Navigating to airport page: {url}")
		self.page.goto(url)
		try:
			self.page.wait_for_load_state("networkidle")
		except Exception:
			time.sleep(1)

	def _extract_page_text(self) -> str:
		# Try content frame if present
		for frame in self.page.frames:
			name = frame.name or ''
			if 'content' in name.lower() or 'eaiscontent' in name.lower():
				try:
					text = frame.text_content('body')
					if text:
						return text
				except Exception:
					pass
		text = self.page.text_content('body') or ''
		return text

	def _parse_operational_hours(self, text: str) -> List[Dict]:
		upper = text.upper()
		start_idx = upper.find('AD 2.2')
		if start_idx == -1:
			start_idx = upper.find('OPERATIONAL HOURS')
		end_idx = upper.find('AD 2.3') if start_idx != -1 else -1
		segment = text[start_idx:end_idx] if (start_idx != -1 and end_idx != -1) else text
		patterns = [
			r"H\s*24|24H|24\s*HR|H24",
			r"(?:MON|TUE|WED|THU|FRI|SAT|SUN|MON-FRI|SAT-SUN|DAILY)\s*[:\-]?\s*(\d{2}[:.]?\d{2})\s*[-–]\s*(\d{2}[:.]?\d{2})",
			r"(\d{3,4})\s*[-–]\s*(\d{3,4})",
		]
		results: List[Dict] = []
		for pat in patterns:
			for m in re.finditer(pat, segment, flags=re.IGNORECASE):
				results.append({"day": "General", "hours": m.group(0).replace('.', ':')})
		if not results:
			results.append({"day": "General", "hours": "Hours information not available"})
		return results

	def _parse_contacts(self, text: str) -> List[Dict]:
		upper = text.upper()
		start_idx = upper.find('AD 2.3')
		if start_idx == -1:
			start_idx = upper.find('AERODROME GEOGRAPHICAL AND ADMINISTRATIVE DATA')
		end_idx = upper.find('AD 2.4') if start_idx != -1 else -1
		segment = text[start_idx:end_idx] if (start_idx != -1 and end_idx != -1) else text
		phone_regex = r"(?:\+?\d{1,3})?\s*(?:\(\d+\)\s*)?(?:\d[\s-]?){6,}"
		emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", segment)
		phones = [p.strip() for p in re.findall(phone_regex, segment) if len(re.sub(r"\D", "", p)) >= 6]
		contacts: List[Dict] = []
		for i, ph in enumerate(phones[:3]):
			contacts.append({"type": f"Contact {i+1}", "phone": ph, "name": "", "email": emails[i] if i < len(emails) else "", "notes": ""})
		if not contacts:
			contacts.append({"type": "General Contact", "phone": "", "name": "", "email": emails[0] if emails else "", "notes": "Contact information not available"})
		return contacts

	def get_airport_info(self, airport_code: str) -> Dict:
		airport_code = airport_code.upper().strip()
		self._goto_index()
		self._open_airport_page(airport_code)
		text = self._extract_page_text()
		return {
			"airportCode": airport_code,
			"towerHours": self._parse_operational_hours(text),
			"contacts": self._parse_contacts(text),
		}


