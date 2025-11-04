#!/usr/bin/env python3
import re
import time
import logging
from typing import Dict, List
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MongoliaAIPScraperPlaywright:
	def __init__(self):
		self.index_url = "https://ais.mn/files/aip/eAIP/2025-10-30-AIRAC/html/index-en-MN.html"
		self.base_url = "https://ais.mn/files/aip/eAIP/2025-10-30-AIRAC/html"
		self.playwright = None
		self.browser = None
		self.page = None

	def _setup(self):
		self.playwright = sync_playwright().start()
		self.browser = self.playwright.chromium.launch(headless=True, args=['--window-size=1600,1000'])
		self.page = self.browser.new_page()
		self.page.set_default_timeout(30000)

	def _teardown(self):
		try:
			if self.browser:
				self.browser.close()
		finally:
			if self.playwright:
				self.playwright.stop()

	def _open_index(self):
		start = self.index_url or (self.base_url.rstrip('/') + '/index.html')
		logger.info(f"Opening {start}")
		self.page.goto(start, wait_until='domcontentloaded')
		try:
			self.page.wait_for_load_state('networkidle')
		except Exception:
			time.sleep(1)

	def _open_airport(self, airport_code: str):
		code = airport_code.upper().strip()
		prefix = code[:2]
		# Try direct pattern used by many eAIP sites
		cand = f"{self.base_url.rstrip('/')}/eAIP/{prefix}-AD-2.{code}-en-GB.html#{code}-AD-2.1"
		logger.info(f"Navigating to airport page: {cand}")
		self.page.goto(cand, wait_until='domcontentloaded')
		try:
			self.page.wait_for_load_state('networkidle')
		except Exception:
			time.sleep(1)

	def _extract_text(self) -> str:
		for frame in self.page.frames:
			name = (frame.name or '').lower()
			if 'content' in name or 'eaiscontent' in name:
				try:
					text = frame.text_content('body')
					if text:
						return text
				except Exception:
					pass
		return self.page.text_content('body') or ''

	def _parse_hours(self, text: str) -> List[Dict]:
		up = text.upper()
		start = up.find('AD 2.3') if 'AD 2.3' in up else up.find('OPERATIONAL HOURS')
		end = up.find('AD 2.4') if start != -1 else -1
		segment = text[start:end] if (start != -1 and end != -1) else text
		patterns = [r"H\s*24|24H|24\s*HR|H24", r"(\d{2}[:.]?\d{2})\s*[-–]\s*(\d{2}[:.]?\d{2})"]
		out: List[Dict] = []
		for pat in patterns:
			for m in re.finditer(pat, segment, flags=re.IGNORECASE):
				out.append({"day": "General", "hours": m.group(0).replace('.', ':')})
		return out or [{"day": "General", "hours": "Hours information not available"}]

	def _parse_contacts(self, text: str) -> List[Dict]:
		emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
		phones = re.findall(r"(?:\+?\d{1,3})?\s*(?:\(\d+\)\s*)?(?:\d[\s-]?){6,}", text)
		contacts: List[Dict] = []
		for i, ph in enumerate([p.strip() for p in phones][:3]):
			contacts.append({"type": f"Contact {i+1}", "phone": ph, "name": "", "email": emails[i] if i < len(emails) else "", "notes": ""})
		return contacts or [{"type": "General Contact", "phone": "", "name": "", "email": emails[0] if emails else "", "notes": "Contact information not available"}]

	def get_airport_info(self, airport_code: str) -> Dict:
		self._setup()
		try:
			self._open_index()
			self._open_airport(airport_code)
			text = self._extract_text()
			return {
				"airportCode": airport_code.upper(),
				"towerHours": self._parse_hours(text),
				"contacts": self._parse_contacts(text),
			}
		finally:
			self._teardown()

def main():
	s = MongoliaAIPScraperPlaywright()
	print(s.get_airport_info("XXXX"))

if __name__ == '__main__':
	main()
