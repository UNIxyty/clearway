"""
Malta AIP PDF Scraper
Extracts operational data from Malta AIP PDF
ICAO Prefix: LM
"""

import os
import re
import PyPDF2
from pathlib import Path
from typing import Dict, List, Optional


class MaltaAIPScraperPDF:
    """Scraper for Malta AIP PDF files"""

    def __init__(self):
        self.aip_dir = Path(__file__).parent.parent / "AIP's"
        self.pdf_path = self.aip_dir / "malta_aip.pdf"
        self.airport_codes = self._extract_airport_codes()

    def _extract_text(self) -> str:
        """Extract all text from Malta AIP PDF"""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error reading Malta AIP: {e}")
            return ""

    def _extract_airport_codes(self) -> List[str]:
        """Extract all airport codes from Malta AIP"""
        text = self._extract_text()
        if not text:
            return []

        # Malta uses LM prefix
        codes = set()
        pattern = r'\b(LM[A-Z]{2})\b'
        matches = re.findall(pattern, text)
        codes.update(matches)

        return sorted(list(codes))

    def get_airport_info(self, airport_code: str) -> Dict:
        """
        Get operational information for a Malta airport
        Returns the standard 9-field structure
        """
        airport_code = airport_code.upper()

        if airport_code not in self.airport_codes:
            return {"error": f"Airport code {airport_code} not found in Malta AIP"}

        # Use the entire PDF text for extraction (Malta AIP typically covers one main airport)
        text = self._extract_text()

        if not text:
            return {"error": f"Could not extract text from Malta AIP PDF"}

        return {
            'airportCode': airport_code,
            'airportName': self._extract_airport_name(text, airport_code),
            'contacts': self._extract_contacts(text),
            'adAdministration': self._extract_ad_administration(text),
            'adOperator': self._extract_ad_operator(text),
            'customsAndImmigration': self._extract_customs(text),
            'ats': self._extract_ats(text),
            'operationalRemarks': self._extract_operational_remarks(text),
            'trafficTypes': self._extract_traffic_types(text),
            'administrativeRemarks': self._extract_admin_remarks(text),
            'fireFightingCategory': self._extract_fire_category(text)
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
            if re.match(r'(Chief|Head|Officer|Manager|Director)', line, re.IGNORECASE):
                if current_contact and (current_contact.get('phone') or current_contact.get('email')):
                    contacts.append(current_contact)

                current_contact = {
                    'type': line.strip()[:50],
                    'phone': '',
                    'email': '',
                    'name': ''
                }

            # Extract phone
            phone_match = re.search(r'Phone:\s*([+\d\s\(\)]+)', line)
            if phone_match and current_contact:
                if not current_contact['phone']:
                    current_contact['phone'] = phone_match.group(1).strip()

            # Extract email
            email_match = re.search(r'Email:\s*([^\s\n]+@[^\s\n]+)', line)
            if email_match and current_contact:
                current_contact['email'] = email_match.group(1).strip()

        if current_contact and (current_contact.get('phone') or current_contact.get('email')):
            contacts.append(current_contact)

        return contacts[:3]  # Return top 3 contacts

    def _extract_ad_administration(self, text: str) -> str:
        """Extract AD Administration operational hours"""
        # Malta format: "1 AD Administration Malta International Airport\nMON – FRI: 0800 LT – 1700 LT"
        patterns = [
            r'1\s+AD\s*Administration[^\n]*\n([^\n]+)',
            r'AD\s*Administration[:\s]+([^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                hours = match.group(1).strip()
                if 'H24' in hours:
                    return 'H24'
                elif 'MON' in hours or 'TUE' in hours or 'FRI' in hours:
                    return hours
                elif 'NIL' in hours.upper():
                    return 'NIL'
                return hours

        return 'NIL'

    def _extract_ad_operator(self, text: str) -> str:
        """Extract AD Operator operational hours"""
        # Malta format: "Aerodrome Duty Officer: H24" or "Operations Duty Officer: H24"
        patterns = [
            r'Aerodrome\s+Duty\s+Officer:\s*(H24|[\d:]+[^\n]*)',
            r'Operations\s+Duty\s+Officer:\s*(H24|[\d:]+[^\n]*)',
            r'AD\s*Operator[:\s]+(H24|NIL)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return 'NIL'

    def _extract_customs(self, text: str) -> str:
        """Extract Customs and Immigration hours"""
        # Malta format: "2 Customs and Immigration H24"
        patterns = [
            r'2\s+Customs\s+and\s+Immigration\s+(H24|NIL|On\s*request|[\d:]+[^\n]*)',
            r'Customs\s+and\s+Immigration\s+(H24|NIL|On\s*request|[\d:]+[^\n]*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return 'NIL'

    def _extract_ats(self, text: str) -> str:
        """Extract ATS operational hours"""
        # Malta format: "5 ATS Reporting Office (ARO) H24" or "7ATS H24"
        patterns = [
            r'[57]\s*ATS\s+Reporting\s+Office[^\n]*(H24|NIL)',
            r'7\s*A\s*T\s*S\s+(H24|NIL)',
            r'ATS\s+Reporting\s+Office[^\n]*(H24|NIL)',
            r'[57]A\s*T\s*S\s+(H24|NIL)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()

        return 'NIL'

    def _extract_operational_remarks(self, text: str) -> str:
        """Extract operational remarks"""
        # Malta format: "11 Remarks Nil" in AD 2.3 section
        patterns = [
            r'11\s+Remarks\s+(Nil|NIL|[^\n]+?)(?=\n\d+\s+[A-Z]|\nLMML|\n[A-Z]{4}\s+AD|$)',
            r'AD\s*2\.3[^\n]*\n.*?Remarks[:\s]+(Nil|NIL|[^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                remarks = match.group(1).strip()
                if remarks and remarks.lower() not in ['nil', 'none']:
                    return remarks[:200]

        return 'NIL'

    def _extract_traffic_types(self, text: str) -> str:
        """Extract types of traffic permitted"""
        # Malta format: "6 Types of traffic perm itted (IFR/VFR) IFR/VFR"
        patterns = [
            r'6\s+Types?\s*of\s*traffic\s*perm[^\n]*\)\s*(IFR/VFR|VFR/IFR|IFR|VFR)',
            r'Types?\s*of\s*traffic\s*permitted[^\n]*\)\s*(IFR/VFR|VFR/IFR|IFR|VFR)',
            r'Types?\s*of\s*traffic\s*permitted[^\n]*(IFR/VFR|VFR/IFR)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return 'Not specified'

    def _extract_admin_remarks(self, text: str) -> str:
        """Extract administrative remarks"""
        # Malta format: "7 Remarks Airport Operator Website: www.maltairport.com"
        patterns = [
            r'7\s+Remarks\s+([^\n]+?)(?=\n[A-Z]{4}\s+AD|12\s+JUN|\d{2}\s+[A-Z]{3}|$)',
            r'AD\s*2\.2[^\n]*\n.*?Remarks[:\s]+([^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                remarks = match.group(1).strip()
                remarks = re.sub(r'\s+', ' ', remarks)
                if remarks and remarks.lower() not in ['nil', 'none']:
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
    scraper = MaltaAIPScraperPDF()
    print(f"Found {len(scraper.airport_codes)} Malta airports: {', '.join(scraper.airport_codes)}")

    if scraper.airport_codes:
        # Test with first airport
        code = scraper.airport_codes[0]
        print(f"\nTesting with {code}:")
        import json
        result = scraper.get_airport_info(code)
        print(json.dumps(result, indent=2))
