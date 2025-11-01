#!/usr/bin/env python3
"""
Latvia AIP scraper using Playwright
Handles the Latvian AIP structure from ais.lgs.lv
"""

import re
import time
import logging
from typing import Dict, List
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LatviaAIPScraperPlaywright:
	def __init__(self):
		"""Initialize the Latvia AIP scraper"""
		self.aip_page_url = "https://ais.lgs.lv/aiseaip"
		self.base_url = None  # Will be fetched from the page
		self.playwright = None
		self.browser = None
		self.page = None

	def _setup_browser(self):
		"""Setup Playwright browser in headless mode."""
		try:
			self.playwright = sync_playwright().start()
			self.browser = self.playwright.chromium.launch(headless=True, args=['--window-size=1600,1000'])
			self.page = self.browser.new_page()
			self.page.set_default_timeout(30000)
			logger.info("Playwright browser initialized for Latvia AIP (headless)")
		except Exception as e:
			logger.error(f"Failed to initialize Playwright browser: {e}")
			raise

	def _get_base_url(self):
		"""Get the current AIP base URL from the Latvia AIP page"""
		if self.base_url:
			return self.base_url
			
		logger.info("Fetching Latvia AIP base URL")
		
		# Navigate to the AIP page
		self.page.goto(self.aip_page_url, wait_until="domcontentloaded")
		time.sleep(2)
		
		# Look for the "CURRENT ISSUE" button with href
		try:
			# Find all buttons with eAIPfiles links
			buttons = self.page.locator("a[href*='eAIPfiles']").all()
			logger.info(f"Found {len(buttons)} buttons with eAIPfiles links")
			
			# Get text of all buttons to find which one is CURRENT ISSUE
			logger.info("Checking button texts...")
			for i, button in enumerate(buttons):
				try:
					button_text = button.text_content()
					href = button.get_attribute("href")
					
					# Look for "AIRAC" at start of button text (current issues are AIRAC)
					if button_text.strip().startswith("AIRAC"):
						logger.info(f"Found AIRAC button {i}: {button_text.strip()}")
						if href:
							if href.startswith("eAIPfiles"):
								self.base_url = f"https://ais.lgs.lv/{href.rsplit('/', 1)[0]}"
							elif href.startswith("/"):
								self.base_url = f"https://ais.lgs.lv{href.rsplit('/', 1)[0]}"
							else:
								self.base_url = href.rsplit('/', 1)[0]
							
							logger.info(f"Base URL: {self.base_url}")
							return self.base_url
				except Exception as e:
					logger.info(f"Error checking button {i}: {e}")
			
			# Fallback: Get the second button (first AIRAC should be current)
			if len(buttons) >= 3:
				button = buttons[2]  # Third button should be CURRENT ISSUE (first AIRAC)
				if button.is_visible():
					href = button.get_attribute("href")
					logger.info(f"Found AIP button (fallback) with href: {href}")
					if href:
						if href.startswith("eAIPfiles"):
							self.base_url = f"https://ais.lgs.lv/{href.rsplit('/', 1)[0]}"
						elif href.startswith("/"):
							self.base_url = f"https://ais.lgs.lv{href.rsplit('/', 1)[0]}"
						else:
							self.base_url = href.rsplit('/', 1)[0]
						return self.base_url
		
		except Exception as e:
			logger.warning(f"Could not find AIP button: {e}")
		
		# Fallback to default URL
		self.base_url = "https://ais.lgs.lv/eAIPfiles/2025_007_30-OCT-2025/data/2025-10-30/html"
		logger.info(f"Using default base URL: {self.base_url}")
		return self.base_url

	def _open_eaip(self):
		"""Open the Latvia eAIP"""
		self._get_base_url()  # This will set self.base_url
		start_url = f"{self.base_url}/index.html"
		logger.info(f"Opening Latvia eAIP: {start_url}")
		self.page.goto(start_url, wait_until="domcontentloaded")
		self.page.wait_for_load_state("networkidle")
		time.sleep(3)

	def _go_to_part3_ad2(self, airport_code: str):
		"""Navigate to Part 3 Aerodromes → AD 2 → Airport"""
		logger.info("Navigating to Part 3 Aerodromes → AD 2")
		
		# Find the navigation frame and navigate through it
		nav_frame = None
		for frame in self.page.frames:
			name = frame.name or ''
			if 'navigation' in name.lower() or 'eaisnavigation' in name.lower():
				nav_frame = frame
				logger.info(f"Found navigation frame: {name}")
				break
		
		if not nav_frame:
			logger.error("No navigation frame found")
			raise Exception("No navigation frame found")
		
		try:
			nav_frame.wait_for_load_state("networkidle")
			time.sleep(2)
			
			# Get navigation content
			nav_text = nav_frame.text_content("body")
			logger.info(f"Navigation content length: {len(nav_text)}")
			
			# Look for Part 3
			if "Part 3" in nav_text or "PART 3" in nav_text:
				logger.info("Found Part 3 in navigation")
				# Try to click Part 3 link
				part3_link = nav_frame.locator("//a[contains(., 'Part 3')]").first
				if part3_link.is_visible():
					part3_link.click()
					time.sleep(1)
					logger.info("Clicked Part 3")
			
			# Look for Aerodromes or AERODROMES
			if "AERODROMES" in nav_text or "Aerodromes" in nav_text:
				logger.info("Found AERODROMES in navigation")
				aerodromes_link = nav_frame.locator("//a[contains(., 'AERODROMES') or contains(., 'Aerodromes')]").first
				if aerodromes_link.is_visible():
					aerodromes_link.click()
					time.sleep(1)
					logger.info("Clicked AERODROMES")
			
			# Look for the airport code
			airport_code = airport_code.upper().strip()
			airport_link = nav_frame.locator(f"//a[contains(., '{airport_code}')]").first
			if airport_link.is_visible():
				airport_link.click()
				time.sleep(2)
				logger.info(f"Clicked airport {airport_code}")
			else:
				logger.warning(f"Could not find airport {airport_code} link, trying direct navigation")
				# Direct navigation as fallback
				self._open_airport_direct(airport_code)
			
		except Exception as e:
			logger.warning(f"Error navigating in frames: {e}")
			# Fallback to direct navigation
			self._open_airport_direct(airport_code)

	def _open_airport_direct(self, airport_code: str):
		"""Navigate to airport page directly"""
		airport_code = airport_code.upper().strip()
		logger.info(f"Navigating directly to airport {airport_code} page")
		
		# Construct airport URL (Latvia uses EV prefix, not LV)
		# Format: {base_url}/eAIP/EV-AD-2.{code}-en-GB.html#EVRA-AD-2.1
		airport_url = f"{self.base_url}/eAIP/EV-AD-2.{airport_code}-en-GB.html#{airport_code}-AD-2.1"
		logger.info(f"Direct URL: {airport_url}")
		
		try:
			self.page.goto(airport_url, wait_until="domcontentloaded")
			time.sleep(2)
			logger.info(f"Successfully navigated to {airport_code} page")
		except Exception as e:
			logger.error(f"Failed to navigate to {airport_code} page: {e}")

	def _extract_sections_text(self) -> str:
		"""Extract visible text from current page"""
		time.sleep(2)
		
		# Try to find content frame
		content_frame = None
		for frame in self.page.frames:
			name = frame.name or ''
			if 'content' in name.lower() or 'eaiscontent' in name.lower():
				content_frame = frame
				logger.info(f"Found content frame: {name}")
				break
		
		if content_frame:
			text = content_frame.text_content('body')
		else:
			logger.info("No content frame found, using main page")
			text = self.page.text_content('body')
		
		logger.info(f"Content length: {len(text)}")
		if len(text) > 100:
			logger.info(f"Preview: {text[:500]}")
		return text

	def _extract_airport_name(self, text: str, airport_code: str) -> str:
		"""Extract airport name from the AERODROME LOCATION INDICATOR AND NAME section"""
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
				# Pattern: CODE — NAME
				name_pattern = rf'{re.escape(code_upper)}\s*[—–-]\s*(.+?)(?=\s*{re.escape(code_upper)}|$)'
				name_match = re.search(name_pattern, name_section, re.IGNORECASE)
				
				if name_match:
					airport_name = name_match.group(1).strip()
					airport_name = re.sub(r'\s+', ' ', airport_name)
					airport_name = re.sub(r'\s*(Aerodrome)$', '', airport_name, flags=re.IGNORECASE)
					airport_name = re.sub(r'\s*AD\s*2\.\d+.*$', '', airport_name, flags=re.IGNORECASE)
					airport_name = re.sub(rf'\s*{re.escape(code_upper)}.*$', '', airport_name, flags=re.IGNORECASE)
					airport_name = airport_name.rstrip(' /').strip()
					return f"{code_upper} — {airport_name}"
			
			# Fallback: try to find any line with the airport code
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

	def _parse_operational_hours(self, text: str) -> List[Dict]:
		"""Parse operational hours from AD 2.3 - return all fields"""
		results: List[Dict] = []
		upper = text.upper()
		start_idx = upper.find('AD 2.3 OPERATIONAL HOURS')
		if start_idx == -1:
			start_idx = upper.find('OPERATIONAL HOURS')
		
		end_idx = upper.find('AD 2.4') if start_idx != -1 else -1
		segment = text[start_idx:end_idx] if start_idx != -1 and end_idx != -1 else text
		operational_hours_section = segment

		# Track found fields
		ad_admin_found = False
		ad_operator_found = False
		customs_found = False
		ats_found = False
		
		# Search for AD Administration
		ad_admin_patterns = [
			r'(?:^|\s)AD\s+Administration.*?(H24|NIL)',
		]
		for pattern in ad_admin_patterns:
			match = re.search(pattern, operational_hours_section, re.IGNORECASE | re.DOTALL)
			if match:
				hours = "H24" if "H24" in match.group(1).upper() else "NIL"
				results.append({"day": "AD Administration", "hours": hours})
				ad_admin_found = True
				break
		
		# Search for AD Operator
		ad_operator_patterns = [
			r'(?:^|\s)AD\s+Operator.*?(H24|NIL)',
			r'1AD.*?(H24|NIL)',
		]
		for pattern in ad_operator_patterns:
			match = re.search(pattern, operational_hours_section, re.IGNORECASE | re.DOTALL)
			if match:
				hours = "H24" if "H24" in match.group(1).upper() else "NIL"
				results.append({"day": "AD Operator", "hours": hours})
				ad_operator_found = True
				break
		
		# Search for Customs and Immigration
		customs_pattern = r'Customs.*?immigration.*?(H24|NIL|May be requested)'
		customs_match = re.search(customs_pattern, operational_hours_section, re.IGNORECASE | re.DOTALL)
		if customs_match:
			hours_text = customs_match.group(1)
			if 'May be requested' in hours_text:
				results.append({"day": "Customs and immigration", "hours": "On request"})
			else:
				hours = "H24" if "H24" in hours_text.upper() else "NIL"
				results.append({"day": "Customs and immigration", "hours": hours})
			customs_found = True
		
		# Search for ATS
		ats_pattern = r'(?<!Reporting )(?<!MET\s)ATS(?![A-Z]).*?(H24|NIL)'
		ats_match = re.search(ats_pattern, operational_hours_section, re.IGNORECASE | re.DOTALL)
		if ats_match:
			hours = "H24" if "H24" in ats_match.group(1).upper() else "NIL"
			results.append({"day": "ATS", "hours": hours})
			ats_found = True
		
		# Add NIL for missing fields
		if not ad_admin_found:
			results.append({"day": "AD Administration", "hours": "NIL"})
		if not ad_operator_found:
			results.append({"day": "AD Operator", "hours": "NIL"})
		if not customs_found:
			results.append({"day": "Customs and immigration", "hours": "NIL"})
		if not ats_found:
			results.append({"day": "ATS", "hours": "NIL"})
		
		return results

	def _parse_contacts(self, text: str) -> List[Dict]:
		"""Parse contacts from text"""
		contacts: List[Dict] = []
		
		upper = text.upper()
		start_idx = upper.find('AD OPERATOR, ADDRESS, TELEPHONE, TELEFAX, E-MAIL, AFS, URL')
		if start_idx == -1:
			start_idx = upper.find('AD OPERATOR')
		
		if start_idx != -1:
			end_idx = upper.find('7TYPES OF TRAFFIC', start_idx)
			if end_idx == -1:
				end_idx = upper.find('AD 2.3', start_idx)
			if end_idx == -1:
				end_idx = start_idx + 2000
			
			ad_operator_section = text[start_idx:end_idx]
			
			# Extract phone numbers (Latvian format: +371)
			phone_regex = r'(\+371[0-9\s]+)'
			phones = re.findall(phone_regex, ad_operator_section)
			phones = [re.sub(r'\s+', ' ', p.strip()) for p in phones if len(p.strip()) <= 20]
			
			# Extract emails
			email_regex = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
			emails = re.findall(email_regex, ad_operator_section)
			emails = [re.sub(r'[A-Z]{2,}.*$', '', email) for email in emails]
			
			# Create contacts
			for i, phone in enumerate(phones[:3]):
				contacts.append({
					"type": f"AD Operator Contact {i+1}",
					"phone": phone.strip(),
					"name": "",
					"email": emails[i] if i < len(emails) else "",
					"notes": "From AD operator section"
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
		"""Extract AD Category for fire fighting from AD 2.6 section"""
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
				
				# Look for AD Category
				category_patterns = [
					r'AD\s+CATEGORY[:\s]+([0-9])',
					r'Category[:\s]+([0-9])',
					r'Category\s+([0-9])[:\s]+for',
				]
				
				for pattern in category_patterns:
					match = re.search(pattern, fire_section, re.IGNORECASE)
					if match:
						return match.group(1)
			
			return "Not specified"
		except Exception as e:
			logger.warning(f"Error extracting fire fighting category: {e}")
			return "Not specified"
	
	def _extract_remarks(self, text: str) -> str:
		"""Extract Remarks from text - must be standalone remarks, not operational hours"""
		try:
			upper = text.upper()
			# Look for AD 2. section that has "Remarks:" or standalone remarks
			# Skip AD 2.3 OPERATIONAL HOURS
			ad23_idx = upper.find('AD 2.3')
			
			if ad23_idx != -1:
				# Look BEFORE AD 2.3 for remarks in AD 2.2 or early in AD 2.3
				ad22_idx = upper.rfind('AD 2.2', 0, ad23_idx)
				if ad22_idx != -1:
					# Search in AD 2.2 section
					remarks_idx = upper.find('REMARKS', ad22_idx, ad23_idx)
					if remarks_idx != -1:
						end_idx = min(ad23_idx, remarks_idx + 500)
						remarks_text = text[remarks_idx:end_idx]
						remarks_text = re.sub(r'^REMARKS[:\s]*', '', remarks_text, flags=re.IGNORECASE)
						remarks_text = re.sub(r'AD\s+2\.3.*$', '', remarks_text, flags=re.IGNORECASE | re.DOTALL)
						remarks_text = re.sub(r'\s+', ' ', remarks_text.strip())
						if len(remarks_text) > 5:  # Not just "NIL" or empty
							return remarks_text[:200]
			
			return "NIL"
		except Exception as e:
			logger.warning(f"Error extracting remarks: {e}")
			return "NIL"
	
	def _extract_traffic_types(self, text: str) -> str:
		"""Extract Types of traffic permitted from AD 2.2 section"""
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
				
				# Look for traffic type
				traffic_patterns = [
					r'Types?\s+of\s+traffic.*?(IFR[/, ]VFR|VFR[/, ]IFR|IFR|VFR)',
					r'Traffic.*?(IFR[/, ]VFR|VFR[/, ]IFR|IFR|VFR)',
					r'(IFR/VFR|VFR/IFR)',
				]
				
				for pattern in traffic_patterns:
					match = re.search(pattern, traffic_section, re.IGNORECASE)
					if match:
						return match.group(1)
			
			return "Not specified"
		except Exception as e:
			logger.warning(f"Error extracting traffic types: {e}")
			return "Not specified"

	def get_airport_info(self, airport_code: str) -> Dict:
		"""Get airport information with fixed field structure"""
		self._setup_browser()
		try:
			self._open_eaip()
			self._go_to_part3_ad2(airport_code)
			text = self._extract_sections_text()
			
			# Extract operational hours from AD 2.3
			operational_hours = self._parse_operational_hours(text)
			
			# Build fixed structure
			info = {
				"airportCode": airport_code.upper(),
				"airportName": self._extract_airport_name(text, airport_code),
				"contacts": self._parse_contacts(text),
				# AD 2.3 OPERATIONAL HOURS section
				"adAdministration": self._get_field_value(operational_hours, "AD Administration"),
				"adOperator": self._get_field_value(operational_hours, "AD Operator"),
				"customsAndImmigration": self._get_field_value(operational_hours, "Customs and immigration"),
				"ats": self._get_field_value(operational_hours, "ATS"),
				"operationalRemarks": self._extract_operational_remarks(text),
				# AD 2.2 AERODROME GEOGRAPHICAL AND ADMINISTRATIVE DATA
				"trafficTypes": self._extract_traffic_types(text),
				"administrativeRemarks": self._extract_administrative_remarks(text),
				# AD 2.6 RESCUE AND FIREFIGHTING SERVICES
				"fireFightingCategory": self._extract_fire_fighting_category(text),
			}
			logger.info(f"Extracted data for {airport_code}")
			return info
		finally:
			self.close()
	
	def _get_field_value(self, operational_hours: List[Dict], field_name: str) -> str:
		"""Get value for a specific field from operational hours"""
		for hour in operational_hours:
			if hour.get("day", "") == field_name:
				return hour.get("hours", "NIL")
		return "NIL"
	
	def _extract_operational_remarks(self, text: str) -> str:
		"""Extract Remarks from AD 2.3 OPERATIONAL HOURS section"""
		return self._extract_remarks(text)
	
	def _extract_administrative_remarks(self, text: str) -> str:
		"""Extract Remarks from AD 2.2 section"""
		try:
			upper = text.upper()
			ad22_start = upper.find('AD 2.2')
			if ad22_start == -1:
				return "NIL"
			
			ad23_start = upper.find('AD 2.3', ad22_start)
			if ad23_start == -1:
				ad23_start = ad22_start + 3000
			
			ad22_section = text[ad22_start:ad23_start]
			remarks_idx = upper.find('REMARKS', ad22_start, ad23_start)
			
			if remarks_idx != -1:
				remarks_text = text[remarks_idx:min(ad23_start, remarks_idx + 1000)]
				remarks_text = re.sub(r'^REMARKS[:\s]*', '', remarks_text, flags=re.IGNORECASE)
				# Stop at next AD 2.X section
				next_ad = re.search(r'\w+\s+AD\s+2\.\d+', remarks_text, re.IGNORECASE)
				if next_ad:
					remarks_text = remarks_text[:next_ad.start()]
				# Remove copyright and AIP footer patterns
				remarks_text = re.sub(r'©.*$', '', remarks_text, flags=re.DOTALL)
				remarks_text = re.sub(r'AIP\s+\w+\s+AIRAC.*$', '', remarks_text, flags=re.IGNORECASE | re.DOTALL)
				remarks_text = re.sub(r'\s+', ' ', remarks_text.strip())
				if len(remarks_text) > 5:
					return remarks_text[:200]
			
			return "NIL"
		except Exception as e:
			logger.warning(f"Error extracting administrative remarks: {e}")
			return "NIL"

	def close(self):
		"""Close browser"""
		try:
			if self.browser:
				self.browser.close()
		except:
			pass
		try:
			if self.playwright:
				self.playwright.stop()
		except:
			pass
		logger.info("Playwright browser closed")


def main():
	"""Test the Latvia AIP scraper"""
	scraper = LatviaAIPScraperPlaywright()
	try:
		# Test with a Latvian airport (e.g., EVRA - Riga)
		result = scraper.get_airport_info("EVRA")
		print("\n=== RESULTS ===")
		print(result)
	except Exception as e:
		print(f"Error: {e}")
		import traceback
		traceback.print_exc()
	finally:
		scraper.close()

if __name__ == "__main__":
	main()

