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
		# Don't initialize browser in __init__ to avoid threading issues
		self.playwright = None
		self.browser = None
		self.page = None

	def _setup_browser(self):
		"""Setup Playwright browser in headless mode (no visible window)."""
		try:
			self.playwright = sync_playwright().start()
			self.browser = self.playwright.chromium.launch(headless=True, args=['--window-size=1600,1000'])
			self.page = self.browser.new_page()
			self.page.set_default_timeout(30000)
			logger.info("Playwright browser initialized for Estonia AIP (headless)")
		except Exception as e:
			logger.error(f"Failed to initialize Playwright browser: {e}")
			raise

	def _open_eaip(self):
		logger.info(f"Opening Estonia eAIP: {self.base_url}")
		self.page.goto(self.base_url)
		self.page.wait_for_load_state("networkidle")

	def _go_to_part3_ad2(self):
		"""Navigate left menu: Part 3 Aerodromes → AD 2."""
		logger.info("Navigating to Part 3 Aerodromes → AD 2")
		
		# Try navigating directly to the frameset URL
		frameset_url = "https://eaip.eans.ee/2025-10-02/html/toc-frameset-en-GB.html"
		logger.info(f"Trying direct navigation to frameset: {frameset_url}")
		
		try:
			self.page.goto(frameset_url)
			self.page.wait_for_load_state("networkidle")
			
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
					logger.info("Opened AERODROMES section")
				except Exception as e:
					logger.info(f"Could not click AERODROMES directly: {e}; trying alternative selectors")
					# Try any element containing AERODROMES
					links = nav_frame.locator("//*[contains(text(), 'AERODROMES')]")
					if links.count() > 0:
						links.first.click()
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

	def _extract_airport_name(self, text: str, airport_code: str) -> str:
		"""Extract airport name and code from the AERODROME LOCATION INDICATOR AND NAME section."""
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
				
				# Look for pattern like "EEEI — ÄMARI militaarlennuväli / Military Aerodrome"
				# or "EETN — LENNART MERI TALLINN"
				code_upper = airport_code.upper()
				
				# Pattern: CODE — NAME (with optional additional info)
				# Capture everything after the dash until we hit the airport code again
				name_pattern = rf'{re.escape(code_upper)}\s*[—–-]\s*(.+?)(?=\s*{re.escape(code_upper)})'
				name_match = re.search(name_pattern, name_section, re.IGNORECASE)
				
				if name_match:
					airport_name = name_match.group(1).strip()
					# Clean up the name - remove extra whitespace and common suffixes
					airport_name = re.sub(r'\s+', ' ', airport_name)
					airport_name = re.sub(r'\s*(militaarlennuväli|Military Aerodrome|lennuväli|Aerodrome)$', '', airport_name, flags=re.IGNORECASE)
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

	def _parse_operational_hours(self, text: str) -> List[Dict]:
		results: List[Dict] = []
		# Look for the specific operational hours table structure
		upper = text.upper()
		start_idx = upper.find('AD 2.3 OPERATIONAL HOURS')
		if start_idx == -1:
			start_idx = upper.find('AD 2.2 OPERATIONAL HOURS')
		if start_idx == -1:
			start_idx = upper.find('OPERATIONAL HOURS')
		end_idx = upper.find('AD 2.4') if start_idx != -1 else -1
		segment = text[start_idx:end_idx] if start_idx != -1 and end_idx != -1 else text

		# Parse the structured table format
		lines = [ln.strip() for ln in segment.split('\n') if ln.strip()]
		
		# Debug: Log the first few lines to understand the structure
		# logger.info(f"Parsing operational hours from {len(lines)} lines")
		# for i, line in enumerate(lines[:10]):
		#     logger.info(f"Line {i}: {line[:100]}")
		
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
			
			# ONLY extract: Customs and Immigration, ATS
			# 2Customs and immigration - May be requested with PPR
			customs_match = re.search(r'2Customs and immigration.*?(H24|NIL|May be requested)', operational_hours_line, re.IGNORECASE | re.DOTALL)
			if customs_match:
				hours_text = customs_match.group(1)
				if 'May be requested' in hours_text:
					results.append({
						"day": "Customs and Immigration",
						"hours": "On request"
					})
				elif 'H24' in hours_text.upper():
					results.append({
						"day": "Customs and Immigration",
						"hours": "H24"
					})
				elif 'NIL' in hours_text.upper():
					results.append({
						"day": "Customs and Immigration",
						"hours": "NIL"
					})
			
			# 7ATS - H24
			ats_match = re.search(r'7ATS.*?(H24|NIL)', operational_hours_line, re.IGNORECASE | re.DOTALL)
			if ats_match and 'H24' in ats_match.group(1).upper():
				results.append({
					"day": "ATS",
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
						results.append({"day": "H24", "hours": "H24"})
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

	def _parse_contacts(self, text: str) -> List[Dict]:
		contacts: List[Dict] = []
		
		# Look specifically for the "AD operator, address, telephone, telefax, e-mail, AFS, URL" section
		upper = text.upper()
		start_idx = upper.find('AD OPERATOR, ADDRESS, TELEPHONE, TELEFAX, E-MAIL, AFS, URL')
		if start_idx == -1:
			start_idx = upper.find('AD OPERATOR')
		
		if start_idx != -1:
			# Find the end of this section (next numbered item or end of AD 2.2)
			end_idx = upper.find('7TYPES OF TRAFFIC', start_idx)
			if end_idx == -1:
				end_idx = upper.find('AD 2.3', start_idx)
			if end_idx == -1:
				end_idx = start_idx + 2000  # Fallback: take next 2000 chars
			
			ad_operator_section = text[start_idx:end_idx]
			
			# Extract phone numbers specifically from this section
			# Pattern for Estonian phone numbers: +372 followed by digits
			phone_regex = r'(\+372[0-9\s]+)'
			phones = re.findall(phone_regex, ad_operator_section)
			
			# Clean up phone numbers - remove extra spaces and limit length
			phones = [re.sub(r'\s+', ' ', p.strip()) for p in phones if len(p.strip()) <= 20]
			
			# Extract emails from this section
			email_regex = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
			emails = re.findall(email_regex, ad_operator_section)
			
			# Clean up emails - remove any concatenated text after the email
			emails = [re.sub(r'[A-Z]{2,}.*$', '', email) for email in emails]
			
			# Create contacts from the AD operator section
			for i, phone in enumerate(phones[:3]):  # Limit to 3 phone numbers
				contacts.append({
					"type": f"AD Operator Contact {i+1}",
					"phone": phone.strip(),
					"name": "",
					"email": emails[i] if i < len(emails) else "",
					"notes": "From AD operator section"
				})
		
		# If no contacts found in AD operator section, add a placeholder
		if not contacts:
			contacts.append({
				"type": "AD Operator Contact",
				"phone": "",
				"name": "",
				"email": "",
				"notes": "Contact information not available in AD operator section"
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
		"""Extract Remarks from text"""
		try:
			upper = text.upper()
			# Look for Remarks section
			start_idx = upper.find('REMARKS')
			
			if start_idx != -1:
				# Find end of remarks (next AD section or end of text)
				end_idx = upper.find('AD 2.', start_idx + 50)
				if end_idx == -1:
					end_idx = start_idx + 500
				
				remarks_text = text[start_idx:end_idx]
				# Clean up the text
				remarks_text = re.sub(r'^REMARKS[:\s]*', '', remarks_text, flags=re.IGNORECASE)
				remarks_text = re.sub(r'\s+', ' ', remarks_text.strip())
				return remarks_text[:200]  # Limit length
			
			return ""
		except Exception as e:
			logger.warning(f"Error extracting remarks: {e}")
			return ""
	
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
		# Setup browser for this request to avoid threading issues
		self._setup_browser()
		try:
			self._open_eaip()
			self._go_to_part3_ad2()
			self._open_airport(airport_code)
			text = self._extract_sections_text()
			info = {
				"airportCode": airport_code.upper(),
				"airportName": self._extract_airport_name(text, airport_code),
				"towerHours": self._parse_operational_hours(text),
				"contacts": self._parse_contacts(text),
				"fireFightingCategory": self._extract_fire_fighting_category(text),
				"remarks": self._extract_remarks(text),
				"trafficTypes": self._extract_traffic_types(text)
			}
			logger.info(f"Extracted data for {airport_code}")
			return info
		finally:
			# Clean up browser after each request
			self.close()

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
