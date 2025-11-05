"""
Generic AIP PDF Extractor
Extracts airport codes and operational information from AIP PDFs
"""

import os
import re
import json
import PyPDF2
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class AIPPDFExtractor:
    """Generic extractor for AIP PDFs"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.country_name = self._extract_country_name()
        self.text = self._extract_text()

    def _extract_country_name(self) -> str:
        """Extract country name from filename"""
        filename = os.path.basename(self.pdf_path)
        name = filename.replace('_aip.pdf', '').replace('_', ' ').title()
        return name

    def _extract_text(self) -> str:
        """Extract all text from PDF"""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error extracting text from {self.pdf_path}: {e}")
            return ""

    def extract_airport_codes(self) -> List[str]:
        """
        Extract ICAO airport codes from the PDF
        ICAO codes are 4-letter codes (e.g., LMML, EVRA, KJFK)
        """
        codes = set()

        # Pattern 1: Look for explicit airport code patterns (e.g., "LMML —", "Code: LMML")
        pattern1 = r'\b([A-Z]{4})\s*[—\-]'
        matches1 = re.findall(pattern1, self.text)
        codes.update(matches1)

        # Pattern 2: Look for AD 2 sections (e.g., "AD 2 LMML")
        pattern2 = r'AD\s*2\s*([A-Z]{4})'
        matches2 = re.findall(pattern2, self.text)
        codes.update(matches2)

        # Pattern 3: Look for standalone 4-letter codes in context
        pattern3 = r'(?:Airport|Aerodrome|Code)\s+([A-Z]{4})\b'
        matches3 = re.findall(pattern3, self.text, re.IGNORECASE)
        codes.update(matches3)

        # Pattern 4: Headers with airport codes
        pattern4 = r'\n([A-Z]{4})\s+AD\s+2\.'
        matches4 = re.findall(pattern4, self.text)
        codes.update(matches4)

        # Filter out common false positives
        false_positives = {'ICAO', 'CODE', 'TYPE', 'DATA', 'INTL', 'AVBL', 'LGTD'}
        codes = {code for code in codes if code not in false_positives}

        return sorted(list(codes))

    def extract_airport_info(self, airport_code: str) -> Optional[Dict]:
        """
        Extract operational information for a specific airport code
        Returns the 9-field structure defined in PROJECT_INFO.md
        """
        # Find the section for this airport
        pattern = rf'{airport_code}\s*AD\s*2\.[\s\S]*?(?=\n[A-Z]{{4}}\s*AD\s*2\.|$)'
        match = re.search(pattern, self.text)

        if not match:
            return None

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
        # Pattern: LMML — LUQA/International
        pattern = rf'{code}\s*[—\-]\s*([^\n]+)'
        match = re.search(pattern, text)
        if match:
            return f"{code} — {match.group(1).strip()}"
        return f"{code}"

    def _extract_contacts(self, text: str) -> List[Dict]:
        """Extract contact information"""
        contacts = []

        # Look for phone numbers and emails
        phone_pattern = r'Phone:\s*([+\d\s\(\)]+)'
        email_pattern = r'Email:\s*([^\s\n]+@[^\s\n]+)'

        phones = re.findall(phone_pattern, text)
        emails = re.findall(email_pattern, text)

        for i, phone in enumerate(phones[:3]):  # Limit to 3 contacts
            contact = {
                'type': f'Contact {i+1}',
                'phone': phone.strip(),
                'email': emails[i].strip() if i < len(emails) else '',
                'name': ''
            }
            contacts.append(contact)

        return contacts if contacts else []

    def _extract_ad_administration(self, text: str) -> str:
        """Extract AD Administration hours"""
        # Look in AD 2.3 OPERATIONAL HOURS section
        pattern = r'AD\s*Administration[:\s]+(H24|NIL|[\d:]+\s*[-–]\s*[\d:]+|[^\n]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            hours = match.group(1).strip()
            if 'H24' in hours:
                return 'H24'
            elif 'NIL' in hours:
                return 'NIL'
            return hours
        return 'NIL'

    def _extract_ad_operator(self, text: str) -> str:
        """Extract AD Operator hours"""
        # Multiple patterns to match different formats
        patterns = [
            r'AD\s*Operator[:\s]+(H24|NIL|[\d:]+\s*[-–]\s*[\d:]+)',
            r'Aerodrome\s*Duty\s*Officer[:\s]+(H24|NIL)',
            r'Operations\s*Duty\s*Officer[:\s]+(H24|NIL)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                hours = match.group(1).strip()
                return 'H24' if 'H24' in hours else hours

        return 'NIL'

    def _extract_customs(self, text: str) -> str:
        """Extract Customs and Immigration hours"""
        pattern = r'Customs\s*and\s*Immigration[:\s]+(H24|NIL|On\s*request|[\d:]+\s*[-–]\s*[\d:]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return 'NIL'

    def _extract_ats(self, text: str) -> str:
        """Extract ATS hours"""
        pattern = r'(?:^|\n)\s*ATS[:\s]+(H24|NIL|[\d:]+\s*[-–]\s*[\d:]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return 'NIL'

    def _extract_operational_remarks(self, text: str) -> str:
        """Extract operational remarks from AD 2.3 section"""
        # Look for remarks in operational hours section
        pattern = r'(?:Operational\s*)?Remarks[:\s]+([^\n]+(?:\n(?![A-Z]{2}\s*\d).*)*)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            remarks = match.group(1).strip()
            if remarks and remarks.lower() not in ['nil', 'none', '']:
                return remarks[:200]  # Limit to 200 chars
        return 'NIL'

    def _extract_traffic_types(self, text: str) -> str:
        """Extract types of traffic permitted (IFR/VFR)"""
        pattern = r'Types?\s*of\s*traffic\s*permitted[:\s]+([A-Z/]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return 'Not specified'

    def _extract_admin_remarks(self, text: str) -> str:
        """Extract administrative remarks from AD 2.2 section"""
        # Look for remarks in AD 2.2 section
        pattern = r'AD\s*2\.2[\s\S]*?Remarks[:\s]+([^\n]+(?:\n(?![A-Z]{2}\s*\d).*)*)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            remarks = match.group(1).strip()
            if remarks and remarks.lower() not in ['nil', 'none', '']:
                return remarks[:200]  # Limit to 200 chars
        return 'NIL'

    def _extract_fire_category(self, text: str) -> str:
        """Extract fire fighting category from AD 2.6 section"""
        patterns = [
            r'AD\s*category\s*for\s*fire\s*fighting[:\s]+(?:H24:\s*)?CAT\s*(\d+)',
            r'Category[:\s]+(\d+)',
            r'CAT\s*(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return 'Not specified'


def main():
    """Main function to demonstrate usage"""
    # Example usage
    aips_dir = Path("/Users/whae/Downloads/Clearway/AIP's")

    if not aips_dir.exists():
        print(f"Directory not found: {aips_dir}")
        return

    # Process all PDF AIPs
    results = {}

    for pdf_file in aips_dir.glob("*.pdf"):
        print(f"\nProcessing: {pdf_file.name}")
        extractor = AIPPDFExtractor(str(pdf_file))

        # Extract airport codes
        codes = extractor.extract_airport_codes()
        print(f"  Found {len(codes)} airport code(s): {', '.join(codes)}")

        results[extractor.country_name] = {
            'codes': codes,
            'file': pdf_file.name
        }

    # Save results
    output_file = aips_dir.parent / "scripts" / "extracted_codes.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to: {output_file}")
    print(f"✓ Processed {len(results)} AIP files")


if __name__ == "__main__":
    main()
