#!/usr/bin/env python3
"""
Lithuania AIP scraper reading from PDF files
Reads airport information from Lithuanian AIP PDF files stored locally
"""

import re
import os
import logging
from typing import Dict, List
from PyPDF2 import PdfReader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LithuaniaAIPScraperPDF:
	def __init__(self, pdf_dir: str = None):
		"""Initialize the Lithuania AIP scraper with PDF directory"""
		if pdf_dir is None:
			# Try to find assets directory relative to this file or in current directory
			script_dir = os.path.dirname(os.path.abspath(__file__))
			parent_dir = os.path.dirname(script_dir)
			pdf_dir = os.path.join(parent_dir, "assets")
		self.pdf_dir = pdf_dir
		self.pdf_paths = self._find_pdf_files()
		logger.info(f"PDF directory: {self.pdf_dir}")
		logger.info(f"Found {len(self.pdf_paths)} PDF files")

	def _find_pdf_files(self) -> Dict[str, str]:
		"""Find all Lithuania AIP PDF files in the directory"""
		pdf_paths = {}
		
		try:
			if os.path.exists(self.pdf_dir):
				for filename in os.listdir(self.pdf_dir):
					if filename.endswith('.pdf') and filename.startswith('EY-AD-2-'):
						# Extract airport code from filename like EY-AD-2-EYVI.pdf
						airport_code = filename.replace('EY-AD-2-', '').replace('.pdf', '')
						filepath = os.path.join(self.pdf_dir, filename)
						pdf_paths[airport_code.upper()] = filepath
						logger.info(f"Found PDF: {airport_code} -> {filepath}")
		except Exception as e:
			logger.error(f"Error finding PDF files: {e}")
		
		return pdf_paths

	def _read_pdf_text(self, filepath: str) -> str:
		"""Extract text from PDF file"""
		try:
			reader = PdfReader(filepath)
			text = ""
			for page in reader.pages:
				text += page.extract_text() + "\n"
			return text
		except Exception as e:
			logger.error(f"Error reading PDF {filepath}: {e}")
			return ""

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
		"""Parse operational hours from text"""
		results: List[Dict] = []
		upper = text.upper()
		start_idx = upper.find('OPERATIONAL HOURS')
		if start_idx == -1:
			start_idx = upper.find('AD 2.3')
		
		# Take enough content to capture all operational hours data
		# Lithuania AIP has AD 2.3 (OPERATIONAL HOURS) followed by AD 2.4
		# So we need to look beyond AD 2.4 marker
		if start_idx != -1:
			# Take 3000 characters to ensure we get all services
			end_idx = start_idx + 3000
		else:
			end_idx = -1
		
		segment = text[start_idx:end_idx] if start_idx != -1 else text

		# Use full segment to match across line breaks
		lines = [ln.strip() for ln in segment.split('\n') if ln.strip()]
		
		# Look for AD Operator hours with MON-THU and FRI patterns across lines
		# Track which patterns we've found to avoid duplicates
		found_mon_thu = False
		found_fri = False
		found_mon_fri = False
		
		for i, line in enumerate(lines):
			# Extract MON-THU hours (e.g., "MON-THU 0500-1400")
			mon_thu_match = re.search(r'MON-THU\s+(\d{4})-(\d{4})', line, re.IGNORECASE)
			if mon_thu_match and not found_mon_thu:
				time_start = f"{mon_thu_match.group(1)[:2]}:{mon_thu_match.group(1)[2:]}"
				time_end = f"{mon_thu_match.group(2)[:2]}:{mon_thu_match.group(2)[2:]}"
				results.append({
					"day": "AD Operator Hours (MON-THU)",
					"hours": f"{time_start}-{time_end}"
				})
				found_mon_thu = True
			
			# Extract FRI hours (e.g., "FRI 0500-1245") - only if at start of line
			fri_match = re.search(r'^FRI\s+(\d{4})-(\d{4})', line, re.IGNORECASE)
			if fri_match and not found_fri:
				time_start = f"{fri_match.group(1)[:2]}:{fri_match.group(1)[2:]}"
				time_end = f"{fri_match.group(2)[:2]}:{fri_match.group(2)[2:]}"
				results.append({
					"day": "AD Operator Hours (FRI)",
					"hours": f"{time_start}-{time_end}"
				})
				found_fri = True
			
			# Also check for MON-FRI pattern
			mon_fri_match = re.search(r'MON-FRI\s+(\d{4})-(\d{4})', line, re.IGNORECASE)
			if mon_fri_match and not found_mon_fri:
				time_start = f"{mon_fri_match.group(1)[:2]}:{mon_fri_match.group(1)[2:]}"
				time_end = f"{mon_fri_match.group(2)[:2]}:{mon_fri_match.group(2)[2:]}"
				results.append({
					"day": "AD Operator Hours (MON-FRI)",
					"hours": f"{time_start}-{time_end}"
				})
				found_mon_fri = True
		
		# Search in full segment for services (to handle line breaks)
		segment_for_search = ' '.join(lines)
		
		# Extract H24 services - look for specific service patterns
		# Services are numbered in Lithuanian AIP: 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
		# ONLY extract: AD Operator, Customs and Immigration, ATS, Remarks
		service_patterns = [
			(r'2.*?Customs.*?(H24|NIL)', "Customs and Immigration"),
			(r'7.*?ATS(?![A-Z]).*?(H24|NIL)', "ATS"),
		]
		
		for pattern, service_name in service_patterns:
			match = re.search(pattern, segment_for_search, re.IGNORECASE | re.DOTALL)
			if match:
				hours_text = match.group(1)
				if 'H24' in hours_text.upper():
					results.append({
						"day": service_name,
						"hours": "H24"
					})
				elif 'NIL' in hours_text.upper():
					results.append({
						"day": service_name,
						"hours": "NIL"
					})
		
		# Fallback: look for H24
		if not results:
			if 'H24' in text or '24H' in text:
				results.append({"day": "General", "hours": "H24"})
		
		if not results:
			results.append({"day": "General", "hours": "Hours information not available"})
		
		# Deduplicate results while preserving order
		unique_results = []
		seen = set()
		for r in results:
			key = (r.get('day'), r.get('hours'))
			if key not in seen:
				seen.add(key)
				unique_results.append(r)
		
		return unique_results

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
			
			# Extract phone numbers (Lithuanian format: +370)
			phone_regex = r'(\+370[0-9\s]+)'
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
				# Remove common footer patterns
				remarks_text = re.sub(r'NĖRA.*$', '', remarks_text, flags=re.IGNORECASE | re.DOTALL)
				remarks_text = re.sub(r'NIL.*$', '', remarks_text, flags=re.IGNORECASE | re.DOTALL)
				remarks_text = re.sub(r'©.*$', '', remarks_text, flags=re.DOTALL)
				remarks_text = re.sub(r'AIP\s+\w+\s+AIRAC.*$', '', remarks_text, flags=re.IGNORECASE | re.DOTALL)
				remarks_text = re.sub(r'\d{2}\s+[A-Z]{3}\s+\d{4}.*$', '', remarks_text, flags=re.IGNORECASE)
				remarks_text = re.sub(r'\s+', ' ', remarks_text.strip())
				# If only whitespace or empty, return empty string
				if not remarks_text or len(remarks_text.strip()) < 3:
					return ""
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
		"""Get airport information from PDF file"""
		airport_code = airport_code.upper().strip()
		
		# Check if we have a PDF for this airport
		if airport_code not in self.pdf_paths:
			logger.error(f"No PDF file found for airport {airport_code}")
			raise Exception(f"No PDF file found for airport {airport_code}")
		
		pdf_path = self.pdf_paths[airport_code]
		logger.info(f"Reading PDF: {pdf_path}")
		
		# Read PDF text
		text = self._read_pdf_text(pdf_path)
		
		if not text:
			raise Exception(f"Could not extract text from PDF {pdf_path}")
		
		logger.info(f"Extracted {len(text)} characters from PDF")
		
		# Parse airport information
		info = {
			"airportCode": airport_code,
			"airportName": self._extract_airport_name(text, airport_code),
			"towerHours": self._parse_operational_hours(text),
			"contacts": self._parse_contacts(text),
			"fireFightingCategory": self._extract_fire_fighting_category(text),
			"remarks": self._extract_remarks(text),
			"trafficTypes": self._extract_traffic_types(text)
		}
		
		logger.info(f"Extracted data for {airport_code}")
		return info

	def close(self):
		"""No-op for PDF scraper (no browser to close)"""
		pass


def main():
	"""Test the Lithuania AIP PDF scraper"""
	scraper = LithuaniaAIPScraperPDF()
	try:
		# Test with available airports
		if scraper.pdf_paths:
			test_airport = list(scraper.pdf_paths.keys())[0]
			logger.info(f"Testing with airport: {test_airport}")
			result = scraper.get_airport_info(test_airport)
			print("\n=== RESULTS ===")
			print(f"Airport Code: {result['airportCode']}")
			print(f"Airport Name: {result['airportName']}")
			print(f"Hours: {result['towerHours']}")
			print(f"Contacts: {result['contacts']}")
		else:
			print("No PDF files found in assets folder")
	except Exception as e:
		print(f"Error: {e}")
		import traceback
		traceback.print_exc()
	finally:
		scraper.close()

if __name__ == "__main__":
	main()

