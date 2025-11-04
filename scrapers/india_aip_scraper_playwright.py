#!/usr/bin/env python3
import re
import time
import logging
from typing import Dict, List
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IndiaAIPScraperPlaywright:
	def __init__(self, base_url: str = "https://aim-india.aai.aero/aip-supplements?page=1"):
		self.base_url = base_url
		self.playwright = None
		self.browser = None
		self.page = None
		self.current_aip_url = None

	def _setup_browser(self):
		"""Setup Playwright browser in headless mode."""
		try:
			self.playwright = sync_playwright().start()
			self.browser = self.playwright.chromium.launch(headless=True, args=['--window-size=1600,1000'])
			self.page = self.browser.new_page()
			self.page.set_default_timeout(45000)
			logger.info("Playwright browser initialized for India AIP (headless)")
		except Exception as e:
			logger.error(f"Failed to initialize Playwright browser: {e}")
			raise

	def _navigate_to_current_aip(self):
		"""Navigate to current AIP version using Effective Date Button Div pattern."""
		logger.info(f"Navigating to India AIP supplements page: {self.base_url}")
		self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=45000)
		time.sleep(2)
		
		# Pattern from JSON: <li class="leaf new" id="new"><a href="https://aim-india.aai.aero/eaip/eaip-v2-05-2025/index-en-GB.html" id="new" class="new">eAIP India AMDT 05/2025 (Effective Date 02 OCT 2025)</a></li>
		try:
			# Find the link with id="new" or class containing "new" that also contains "eaip" and "index-en-GB"
			new_link = self.page.locator("li.leaf.new a.new[href*='eaip'][href*='index-en-GB'], li#new a#new[href*='eaip'][href*='index-en-GB'], a.new[href*='eaip'][href*='index-en-GB']").first
			if new_link.count() > 0:
				href = new_link.get_attribute('href')
				link_text = new_link.text_content()
				logger.info(f"Found current AIP link: {link_text[:100]}, href: {href}")
				
				if href and 'eaip' in href.lower() and 'index-en-GB' in href:
					if href.startswith('http'):
						self.current_aip_url = href
					else:
						base = urlparse(self.base_url)
						self.current_aip_url = urljoin(f"{base.scheme}://{base.netloc}", href)
					
					logger.info(f"Navigating to current AIP: {self.current_aip_url}")
					self.page.goto(self.current_aip_url, wait_until="domcontentloaded", timeout=45000)
					time.sleep(2)
					return
			
			# Fallback: look for links containing "eaip" and "index-en-GB" specifically
			all_links = self.page.locator("a[href*='eaip'][href*='index-en-GB']")
			if all_links.count() > 0:
				href = all_links.first.get_attribute('href')
				if href and 'eaip' in href.lower() and 'index-en-GB' in href:
					if href.startswith('http'):
						self.current_aip_url = href
					else:
						base = urlparse(self.base_url)
						self.current_aip_url = urljoin(f"{base.scheme}://{base.netloc}", href)
					self.page.goto(self.current_aip_url, wait_until="domcontentloaded", timeout=45000)
					time.sleep(2)
					logger.info(f"Used fallback navigation to: {self.current_aip_url}")
					return
			
			raise Exception("Could not find current AIP link")
		except Exception as e:
			logger.error(f"Failed to navigate to current AIP: {e}")
			raise

	def _navigate_to_ad2_section(self):
		"""Navigate to Part 3 Aerodromes → AD 2."""
		logger.info("Navigating to Part 3 Aerodromes → AD 2")
		
		try:
			base_url = self.current_aip_url or self.base_url
			base_parsed = urlparse(base_url)
			frameset_url = f"{base_parsed.scheme}://{base_parsed.netloc}{base_parsed.path.rsplit('/', 1)[0]}/toc-frameset-en-GB.html"
			logger.info(f"Trying frameset: {frameset_url}")
			self.page.goto(frameset_url)
			self.page.wait_for_load_state("networkidle")
			time.sleep(2)
			
			frames = self.page.frames
			nav_frame = None
			for frame in frames:
				name = frame.name or ''
				if 'toc' in name.lower() or 'nav' in name.lower() or 'eaisnavigation' in name.lower():
					nav_frame = frame
					break
			
			if nav_frame:
				logger.info("Found navigation frame")
				try:
					aerodromes_link = nav_frame.locator("//a[contains(., 'AERODROMES')]").first
					if aerodromes_link.count() > 0:
						aerodromes_link.click()
						time.sleep(1)
						logger.info("Opened AERODROMES section")
				except Exception as e:
					logger.warning(f"Could not click AERODROMES: {e}")
					links = nav_frame.locator("//*[contains(text(), 'AERODROMES')]")
					if links.count() > 0:
						links.first.click()
			time.sleep(1)
		except Exception as e:
			logger.warning(f"Frameset navigation failed: {e}")

	def _open_airport(self, airport_code: str):
		"""Navigate to specific airport page via navigation frame."""
		airport_code = airport_code.upper().strip()
		logger.info(f"Opening airport {airport_code}")
		
		# Find navigation frame
		nav_frame = None
		for frame in self.page.frames:
			name = frame.name or ''
			if 'toc' in name.lower() or 'nav' in name.lower() or 'eaisnavigation' in name.lower():
				nav_frame = frame
				break
		
		if nav_frame:
			try:
				# Find airport link - look for href containing airport code
				airport_link = nav_frame.locator(f"//a[contains(@href, '{airport_code}') or contains(@id, '{airport_code}') or contains(@title, '{airport_code}')]").first
				if airport_link.count() > 0:
					href = airport_link.get_attribute('href')
					logger.info(f"Found airport link, href: {href}")
					
					# Try to click using JavaScript (link may not be visible)
					try:
						nav_frame.evaluate(f"""
							const link = document.querySelector('a[href*="{airport_code}"], a[id*="{airport_code}"], a[title="{airport_code}"]');
							if (link) {{
								link.click();
							}}
						""")
						time.sleep(2)  # Wait for content frame to update
						logger.info(f"Clicked airport link for {airport_code} via JavaScript")
						
						# Verify content frame has updated
						text = self._extract_sections_text()
						if airport_code in text.upper() or len(text) > 500:
							logger.info(f"Successfully navigated to {airport_code} via frame click")
							return
					except Exception as e:
						logger.warning(f"JavaScript click failed: {e}")
						
						# Fallback: construct URL from href
						if href and href.endswith('.html'):
							href_clean = href.split('#')[0]
							# Replace spaces with hyphens in the href
							href_clean = href_clean.replace(' ', '-')
							if self.current_aip_url:
								base_parsed = urlparse(self.current_aip_url)
								base_path = base_parsed.path.rsplit('/', 1)[0]
								airport_url = f"{base_parsed.scheme}://{base_parsed.netloc}{base_path}/eAIP/{href_clean}"
								logger.info(f"Trying constructed URL: {airport_url}")
								self.page.goto(airport_url, wait_until="domcontentloaded", timeout=45000)
								time.sleep(1)
								text = self._extract_sections_text()
								if airport_code in text.upper() or len(text) > 500:
									return
				else:
					logger.warning(f"Airport link for {airport_code} not found in navigation")
			except Exception as e:
				logger.warning(f"Error accessing airport link: {e}")
		
		# Fallback: try direct URL construction
		if self.current_aip_url:
			base_parsed = urlparse(self.current_aip_url)
			base_path = base_parsed.path.rsplit('/', 1)[0] if '/' in base_parsed.path else ''
			
			# India AIP patterns: IN-AD 2.1XXXX-en-GB.html (with spaces) or IN-AD-2.1XXXX-en-GB.html (with hyphens)
			prefix = airport_code[:2] if len(airport_code) >= 2 else "IN"
			patterns = [
				f"{base_parsed.scheme}://{base_parsed.netloc}{base_path}/eAIP/{prefix}-AD-2.1{airport_code}-en-GB.html",
				f"{base_parsed.scheme}://{base_parsed.netloc}{base_path}/eAIP/{prefix}-AD-2-{airport_code}-en-GB.html",
				f"{base_parsed.scheme}://{base_parsed.netloc}{base_path}/eAIP/VE-AD-2.{airport_code}-en-GB.html",
			]
			
			for pattern_url in patterns:
				try:
					self.page.goto(pattern_url)
					self.page.wait_for_load_state("networkidle")
					time.sleep(2)
					text = self._extract_sections_text()
					if airport_code in text.upper() or len(text) > 500:
						logger.info(f"Successfully navigated to {airport_code} via direct URL")
						return
				except Exception as e:
					logger.debug(f"Direct URL failed {pattern_url}: {e}")
					continue
		
		raise Exception(f"Failed to navigate to airport {airport_code}")

	def _extract_sections_text(self) -> str:
		"""Extract text from current page/frame."""
		content_frame = None
		for frame in self.page.frames:
			name = frame.name or ''
			if 'content' in name.lower() or 'eaiscontent' in name.lower():
				content_frame = frame
				break
		
		if content_frame:
			text = content_frame.text_content('body')
		else:
			text = self.page.text_content('body')
		
		logger.info(f"Extracted {len(text)} characters")
		return text

	def _extract_airport_name(self, text: str, airport_code: str) -> str:
		"""Extract airport name."""
		try:
			upper = text.upper()
			start_idx = upper.find('AERODROME LOCATION INDICATOR AND NAME')
			if start_idx == -1:
				start_idx = upper.find('AD 2.1')
			
			if start_idx != -1:
				end_idx = upper.find('AD 2.2', start_idx)
				if end_idx == -1:
					end_idx = start_idx + 500
				
				name_section = text[start_idx:end_idx]
				code_upper = airport_code.upper()
				name_pattern = rf'{re.escape(code_upper)}\s*[—–-]\s*(.+?)(?=\s*{re.escape(code_upper)}|\s*AD\s*2)'
				name_match = re.search(name_pattern, name_section, re.IGNORECASE)
				
				if name_match:
					airport_name = name_match.group(1).strip()
					airport_name = re.sub(r'\s+', ' ', airport_name)
					airport_name = re.sub(r'\s*AD\s*2\.\d+.*$', '', airport_name, flags=re.IGNORECASE)
					return f"{code_upper} — {airport_name}"
			
			lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
			code_upper = airport_code.upper()
			for line in lines[:50]:
				if code_upper in line and len(line) <= 150:
					if '—' in line or '–' in line or '-' in line:
						return line.strip()
			
			return airport_code.upper()
		except Exception as e:
			logger.warning(f"Error extracting airport name: {e}")
			return airport_code.upper()

	def _parse_operational_hours(self, text: str) -> Dict:
		"""Parse operational hours from AD 2.3."""
		upper = text.upper()
		start_idx = upper.find('AD 2.3 OPERATIONAL HOURS')
		if start_idx == -1:
			start_idx = upper.find('OPERATIONAL HOURS')
		
		end_idx = upper.find('AD 2.4') if start_idx != -1 else -1
		segment = text[start_idx:end_idx] if start_idx != -1 and end_idx != -1 else text
		
		result = {
			"adAdministration": "NIL",
			"adOperator": "NIL",
			"customsAndImmigration": "NIL",
			"ats": "NIL"
		}
		
		# AD Administration
		ad_admin_match = re.search(r'AD\s+Administration.*?(H24|NIL)', segment, re.IGNORECASE | re.DOTALL)
		if ad_admin_match:
			result["adAdministration"] = "H24" if "H24" in ad_admin_match.group(1).upper() else "NIL"
		
		# AD Operator
		ad_op_match = re.search(r'AD\s+Operator.*?(H24|NIL|(\d{2}[:.]?\d{2})\s*[–\-]\s*(\d{2}[:.]?\d{2}))', segment, re.IGNORECASE | re.DOTALL)
		if ad_op_match:
			if len(ad_op_match.groups()) >= 3 and ad_op_match.group(2):
				result["adOperator"] = f"{ad_op_match.group(2).replace('.', ':')}-{ad_op_match.group(3).replace('.', ':')}"
			else:
				result["adOperator"] = "H24" if "H24" in ad_op_match.group(0).upper() else "NIL"
		
		# Customs and Immigration
		customs_match = re.search(r'Customs.*?immigration.*?(H24|NIL|On request|May be requested)', segment, re.IGNORECASE | re.DOTALL)
		if customs_match:
			hours_text = customs_match.group(1)
			if 'request' in hours_text.lower():
				result["customsAndImmigration"] = "On request"
			else:
				result["customsAndImmigration"] = "H24" if "H24" in hours_text.upper() else "NIL"
		
		# ATS
		ats_match = re.search(r'(?<!Reporting )(?<!MET\s)ATS(?![A-Z]).*?(H24|NIL)', segment, re.IGNORECASE | re.DOTALL)
		if ats_match:
			result["ats"] = "H24" if "H24" in ats_match.group(1).upper() else "NIL"
		
		return result

	def _parse_contacts(self, text: str) -> List[Dict]:
		"""Extract contact information."""
		contacts = []
		upper = text.upper()
		start_idx = upper.find('AD OPERATOR')
		if start_idx == -1:
			start_idx = upper.find('TELEPHONE')
		
		if start_idx != -1:
			end_idx = upper.find('AD 2.3', start_idx)
			if end_idx == -1:
				end_idx = start_idx + 2000
			
			contact_section = text[start_idx:end_idx]
			
			# Phone numbers (India: +91)
			phone_regex = r'(\+91[0-9\s\-]+|\+?[0-9\s\-]{8,})'
			phones = re.findall(phone_regex, contact_section)
			phones = [re.sub(r'\s+', ' ', p.strip()) for p in phones if len(p.strip()) >= 7 and len(p.strip()) <= 20]
			
			# Emails
			email_regex = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
			emails = re.findall(email_regex, contact_section)
			
			for i, phone in enumerate(phones[:3]):
				contacts.append({
					"type": f"AD Operator Contact {i+1}",
					"phone": phone.strip(),
					"name": "",
					"email": emails[i] if i < len(emails) else "",
					"notes": ""
				})
		
		if not contacts:
			contacts.append({
				"type": "AD Operator Contact",
				"phone": "",
				"name": "",
				"email": "",
				"notes": "Contact information not available"
			})
		
		return contacts

	def _extract_fire_fighting_category(self, text: str) -> str:
		"""Extract fire fighting category from AD 2.6."""
		try:
			upper = text.upper()
			start_idx = upper.find('AD 2.6')
			if start_idx == -1:
				start_idx = upper.find('RESCUE AND FIRE FIGHTING')
			
			if start_idx != -1:
				end_idx = upper.find('AD 2.7', start_idx)
				if end_idx == -1:
					end_idx = start_idx + 2000
				
				fire_section = text[start_idx:end_idx]
				category_patterns = [
					r'AD\s+CATEGORY[:\s]+([0-9])',
					r'Category[:\s]+([0-9])',
				]
				
				for pattern in category_patterns:
					match = re.search(pattern, fire_section, re.IGNORECASE)
					if match:
						return match.group(1)
			
			return "Not specified"
		except Exception as e:
			logger.warning(f"Error extracting fire fighting category: {e}")
			return "Not specified"

	def _extract_operational_remarks(self, text: str) -> str:
		"""Extract operational remarks from AD 2.3."""
		try:
			upper = text.upper()
			ad23_idx = upper.find('AD 2.3')
			if ad23_idx == -1:
				return "NIL"
			
			remarks_idx = upper.find('REMARKS', ad23_idx)
			if remarks_idx != -1:
				end_idx = upper.find('AD 2.4', remarks_idx)
				if end_idx == -1:
					end_idx = remarks_idx + 500
				
				remarks_text = text[remarks_idx:end_idx]
				remarks_text = re.sub(r'^REMARKS[:\s]*', '', remarks_text, flags=re.IGNORECASE)
				remarks_text = re.sub(r'AD\s+2\.4.*$', '', remarks_text, flags=re.IGNORECASE | re.DOTALL)
				remarks_text = re.sub(r'\s+', ' ', remarks_text.strip())
				if len(remarks_text) > 5:
					return remarks_text[:200]
			
			return "NIL"
		except Exception as e:
			logger.warning(f"Error extracting operational remarks: {e}")
			return "NIL"

	def _extract_traffic_types(self, text: str) -> str:
		"""Extract traffic types from AD 2.2."""
		try:
			upper = text.upper()
			start_idx = upper.find('AD 2.2')
			if start_idx == -1:
				start_idx = upper.find('AERODROME GEOGRAPHICAL')
			
			if start_idx != -1:
				end_idx = upper.find('AD 2.3', start_idx)
				if end_idx == -1:
					end_idx = start_idx + 2000
				
				traffic_section = text[start_idx:end_idx]
				traffic_patterns = [
					r'Types?\s+of\s+traffic.*?(IFR[/, ]VFR|VFR[/, ]IFR|IFR|VFR)',
					r'Traffic.*?(IFR[/, ]VFR|VFR[/, ]IFR|IFR|VFR)',
				]
				
				for pattern in traffic_patterns:
					match = re.search(pattern, traffic_section, re.IGNORECASE)
					if match:
						return match.group(1)
			
			return "Not specified"
		except Exception as e:
			logger.warning(f"Error extracting traffic types: {e}")
			return "Not specified"

	def _extract_administrative_remarks(self, text: str) -> str:
		"""Extract administrative remarks from AD 2.2."""
		try:
			upper = text.upper()
			ad22_start = upper.find('AD 2.2')
			if ad22_start == -1:
				return "NIL"
			
			ad23_start = upper.find('AD 2.3', ad22_start)
			if ad23_start == -1:
				ad23_start = ad22_start + 3000
			
			remarks_idx = upper.find('REMARKS', ad22_start, ad23_start)
			if remarks_idx != -1:
				remarks_text = text[remarks_idx:min(ad23_start, remarks_idx + 1000)]
				remarks_text = re.sub(r'^REMARKS[:\s]*', '', remarks_text, flags=re.IGNORECASE)
				remarks_text = re.sub(r'AD\s+2\.3.*$', '', remarks_text, flags=re.IGNORECASE | re.DOTALL)
				remarks_text = re.sub(r'©.*$', '', remarks_text, flags=re.DOTALL)
				remarks_text = re.sub(r'\s+', ' ', remarks_text.strip())
				if len(remarks_text) > 5:
					return remarks_text[:200]
			
			return "NIL"
		except Exception as e:
			logger.warning(f"Error extracting administrative remarks: {e}")
			return "NIL"

	def get_airport_info(self, airport_code: str) -> Dict:
		"""Main method to extract airport information."""
		self._setup_browser()
		try:
			self._navigate_to_current_aip()
			self._navigate_to_ad2_section()
			self._open_airport(airport_code)
			text = self._extract_sections_text()
			
			operational_hours = self._parse_operational_hours(text)
			
			# Only required fields according to specifications
			info = {
				"airportCode": airport_code.upper(),
				"airportName": self._extract_airport_name(text, airport_code),
				# AD 2.3 OPERATIONAL HOURS - Required fields only
				"adOperator": operational_hours.get("adOperator", "NIL"),
				"customsAndImmigration": operational_hours.get("customsAndImmigration", "NIL"),
				"ats": operational_hours.get("ats", "NIL"),
				"operationalRemarks": self._extract_operational_remarks(text),
				# AD 2.2 GEOGRAPHICAL DATA - Required fields only
				"trafficTypes": self._extract_traffic_types(text),
				"administrativeRemarks": self._extract_administrative_remarks(text),
				# AD 2.6 FIRE FIGHTING - Required field only
				"fireFightingCategory": self._extract_fire_fighting_category(text),
			}
			
			logger.info(f"Successfully extracted data for {airport_code}")
			return info
		finally:
			self.close()

	def close(self):
		"""Clean up browser resources."""
		try:
			if self.browser:
				self.browser.close()
		except Exception as e:
			logger.warning(f"Error closing browser: {e}")
		try:
			if self.playwright:
				self.playwright.stop()
		except Exception as e:
			logger.warning(f"Error stopping playwright: {e}")
		logger.info("Playwright browser closed")


def main():
	scraper = IndiaAIPScraperPlaywright()
	try:
		# Example: Delhi Airport (VIDP)
		result = scraper.get_airport_info("VIDP")
		import json
		print("\n=== RESULTS ===")
		print(json.dumps(result, indent=2))
	except Exception as e:
		print(f"Error: {e}")
	finally:
		scraper.close()

if __name__ == "__main__":
	main()
