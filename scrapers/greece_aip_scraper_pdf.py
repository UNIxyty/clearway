"""
Greece AIP PDF Scraper
Extracts operational data from Greece AIP PDF
ICAO Prefix: LG
"""

import os
import re
import PyPDF2
from pathlib import Path
from typing import Dict, List, Optional


class GreeceAIPScraperPDF:
    """Scraper for Greece AIP PDF files"""

    def __init__(self):
        self.aip_dir = Path(__file__).parent.parent / "AIP's"
        self.pdf_path = self.aip_dir / "greece_aip.pdf"
        self.airport_codes = self._extract_airport_codes()

    def _extract_text(self) -> str:
        """Extract all text from Greece AIP PDF"""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error reading Greece AIP: {e}")
            return ""

    def _extract_airport_codes(self) -> List[str]:
        """Extract all airport codes from Greece AIP"""
        text = self._extract_text()
        if not text:
            return []

        # Greece uses LG prefix
        codes = set()
        pattern = r'\b(LG[A-Z]{2})\b'
        matches = re.findall(pattern, text)
        codes.update(matches)

        return sorted(list(codes))

    def get_airport_info(self, airport_code: str) -> Dict:
        """
        Get operational information for a Greece airport
        Returns the standard 9-field structure
        """
        airport_code = airport_code.upper()

        if airport_code not in self.airport_codes:
            return {"error": f"Airport code {airport_code} not found in Greece AIP"}

        text = self._extract_text()

        # Find the section for this airport
        pattern = rf'{airport_code}[\s\S]*?(?=\n[A-Z]{{4}}\s|$)'
        match = re.search(pattern, text)

        if not match:
            return {"error": f"Could not find data for {airport_code}"}

        section_text = match.group(0)

        return {
            'airportCode': airport_code,
            'airportName': self._extract_airport_name(section_text, airport_code),
            'contacts': self._extract_contacts(section_text),
            'adAdministration': self._extract_ad_administration(section_text),
            'adOperator': self._extract_ad_operator(section_text),
            'customsAndImmigration': self._extract_customs(section_text),
            'ats': self._extract_ats(section_text),
            'operationalRemarks': self._extract_operational_remarks(section_text),
            'trafficTypes': self._extract_traffic_types(section_text),
            'administrativeRemarks': self._extract_admin_remarks(section_text),
            'fireFightingCategory': self._extract_fire_category(section_text)
        }

    def _extract_airport_name(self, text: str, code: str) -> str:
        """Extract airport name"""
        pattern = rf'{code}\s*[—\-]\s*([^\n]+(?:\n[^\n]*)?)'
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            # Clean up the name
            name = re.sub(r'\s+', ' ', name)
            return f"{code} — {name}"
        return code

    def _extract_contacts(self, text: str) -> List[Dict]:
        """Extract contact information"""
        contacts = []

        # Extract phone numbers and emails
        lines = text.split('\n')

        current_contact = None
        for i, line in enumerate(lines):
            # Look for contact type
            if re.match(r'(Chief|Head|Officer|Manager|Director|Information)', line, re.IGNORECASE):
                if current_contact and (current_contact.get('phone') or current_contact.get('email')):
                    contacts.append(current_contact)

                current_contact = {
                    'type': line.strip()[:50],
                    'phone': '',
                    'email': '',
                    'name': ''
                }

            # Extract phone
            phone_match = re.search(r'(?:Phone|Tel|TEL):\s*([+\d\s\(\)]+)', line)
            if phone_match and current_contact:
                if not current_contact['phone']:
                    current_contact['phone'] = phone_match.group(1).strip()

            # Extract email
            email_match = re.search(r'(?:Email|E-mail):\s*([^\s\n]+@[^\s\n]+)', line, re.IGNORECASE)
            if email_match and current_contact:
                current_contact['email'] = email_match.group(1).strip()

        if current_contact and (current_contact.get('phone') or current_contact.get('email')):
            contacts.append(current_contact)

        return contacts[:3]  # Return top 3 contacts

    def _extract_ad_administration(self, text: str) -> str:
        """Extract AD Administration operational hours"""
        patterns = [
            r'AD\s*Administration[:\s]+([^\n]+)',
            r'(?:^|\n)\s*\d+\s+AD\s*Administration[:\s]+(H24|NIL|[\d:]+\s*[-–]\s*[\d:]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                hours = match.group(1).strip()
                if 'H24' in hours:
                    return 'H24'
                elif 'NIL' in hours:
                    return 'NIL'
                elif any(day in hours for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']):
                    return hours
                return hours

        return 'NIL'

    def _extract_ad_operator(self, text: str) -> str:
        """Extract AD Operator operational hours"""
        patterns = [
            r'Aerodrome\s*Duty\s*Officer[:\s]+(H24|[\d:]+)',
            r'Operations\s*Duty\s*Officer[:\s]+(H24|[\d:]+)',
            r'AD\s*Operator[:\s]+(H24|NIL)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return 'NIL'

    def _extract_customs(self, text: str) -> str:
        """Extract Customs and Immigration hours"""
        pattern = r'Customs\s*(?:and\s*)?Immigration[:\s]+(H24|NIL|On\s*request|[\d:]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return 'NIL'

    def _extract_ats(self, text: str) -> str:
        """Extract ATS operational hours"""
        patterns = [
            r'(?:^|\n)\s*\d+\s+ATS[:\s]+(H24|NIL)',
            r'ATS\s*Reporting\s*Office.*?[:\s]+(H24|NIL)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()

        return 'NIL'

    def _extract_operational_remarks(self, text: str) -> str:
        """Extract operational remarks"""
        patterns = [
            r'(?:Operational\s*)?Remarks[:\s]+((?:(?!AD\s*2\.\d).)+)',
            r'\d+\s+Remarks[:\s]+(Nil|NIL|[^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                remarks = match.group(1).strip()
                if remarks and remarks.lower() not in ['nil', 'none']:
                    remarks = re.sub(r'\s+', ' ', remarks)
                    return remarks[:200]

        return 'NIL'

    def _extract_traffic_types(self, text: str) -> str:
        """Extract types of traffic permitted"""
        pattern = r'Types?\s*of\s*traffic\s*permitted.*?[:\s]+([A-Z/]+)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            traffic = match.group(1).strip()
            if 'IFR' in traffic and 'VFR' in traffic:
                return 'IFR/VFR'
            return traffic
        return 'Not specified'

    def _extract_admin_remarks(self, text: str) -> str:
        """Extract administrative remarks"""
        pattern = r'Remarks[:\s]+((?:(?!AD\s*2\.\d).)+)'
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)

        for match in matches:
            remarks = match.strip()
            if remarks and remarks.lower() not in ['nil', 'none']:
                remarks = re.sub(r'\s+', ' ', remarks)
                return remarks[:200]

        return 'NIL'

    def _extract_fire_category(self, text: str) -> str:
        """Extract fire fighting category"""
        patterns = [
            r'AD\s*category\s*for\s*fire\s*fighting[:\s]+(?:H24:\s*)?CAT\s*(\d+)',
            r'Category[:\s]+(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return 'Not specified'


# Test function
if __name__ == "__main__":
    scraper = GreeceAIPScraperPDF()
    print(f"Found {len(scraper.airport_codes)} Greece airports: {', '.join(scraper.airport_codes)}")

    if scraper.airport_codes:
        # Test with first airport
        code = scraper.airport_codes[0]
        print(f"\nTesting with {code}:")
        import json
        result = scraper.get_airport_info(code)
        print(json.dumps(result, indent=2))
