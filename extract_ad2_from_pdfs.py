#!/usr/bin/env python3
"""
Extract AD2 sections from PDF AIP files:
1. Identify and save page numbers for AD2 sections per airport
2. Extract airport information from AD2 sections:
   - Airport name
   - Operational hours (AD 2.3)
   - Contacts (AD 2.24)
   - Other relevant data
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from datetime import datetime

try:
    from pypdf import PdfReader
except ImportError:
    raise ImportError("Please install pypdf: pip install pypdf")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Country to prefix mapping
COUNTRY_TO_PREFIX = {
    'Afghanistan': 'OA', 'Andorra': 'LE', 'Angola': 'FN', 'Austria': 'LO',
    'Azerbaijan': 'UB', 'Bhutan': 'VQ', 'Bulgaria': 'LZ', 'Canada': 'C',
    'Cuba': 'MU', 'Czech Republic': 'LK', 'Denmark': 'EK', 'Djibouti': 'HD',
    'Ethiopia': 'HA', 'Greece': 'LG', 'Haiti': 'MT', 'Iran': 'OI',
    'Ireland': 'EI', 'Italy': 'LI', 'Libya': 'HL', 'Macao': 'VM',
    'Malta': 'LM', 'Maldives': 'VR', 'Nepal': 'VN', 'Seychelles': 'FS',
    'South Africa': 'FA', 'Sudan': 'HS', 'South Sudan': 'HSS', 'Timor': 'WP',
    'Timor-Leste': 'WP', 'Trinidad and Tobago': 'TT',
}

# AD2 section patterns
AD2_SECTIONS = {
    'AD_2_1': r'AD\s*2\.1|AD\s*2-1|AERODROME\s*LOCATION\s*INDICATOR',
    'AD_2_2': r'AD\s*2\.2|AD\s*2-2|AERODROME\s*GEOGRAPHICAL',
    'AD_2_3': r'AD\s*2\.3|AD\s*2-3|OPERATIONAL\s*HOURS',
    'AD_2_4': r'AD\s*2\.4|AD\s*2-4',
    'AD_2_5': r'AD\s*2\.5|AD\s*2-5',
    'AD_2_6': r'AD\s*2\.6|AD\s*2-6|RESCUE\s*AND\s*FIRE',
    'AD_2_24': r'AD\s*2\.24|AD\s*2-24|CONTACT\s*INFORMATION',
}

def find_ad2_sections(pdf_path: Path, country_prefix: Optional[str] = None) -> Dict[str, Dict[str, List[int]]]:
    """
    Find AD2 sections in PDF and return page numbers for each airport
    Returns: {airport_code: {section: [page_numbers]}}
    """
    ad2_data = defaultdict(lambda: defaultdict(list))
    
    # Extended false positive list
    FALSE_POSITIVES = {
        'PAGE', 'DATE', 'TIME', 'NOTE', 'LIST', 'PART', 'SECT', 'TEXT', 'CONT', 'COPY', 
        'ICAO', 'INFO', 'DOC', 'ZOLL', 'FROM', 'SITA', 'AMDT', 'AERO', 'AFIS', 'AFTN',
        'AIDS', 'ALTN', 'AMSL', 'ANCE', 'APCH', 'APPR', 'APRO', 'AREA', 'ASDA', 'ATIS',
        'AVBL', 'BIRD', 'BLUE', 'BNAH', 'BOLO', 'CAMP', 'CARF', 'CDNM', 'CEIL', 'CFBN',
        'CHAR', 'CITY', 'CLUB', 'COMM', 'CONV', 'DATA', 'DCAT', 'DDME', 'DECL', 'DESC',
        'DIST', 'DMDA', 'DMEV', 'DMOR', 'DORI', 'DTHR', 'DVAR', 'DVLF', 'EAST', 'EDGE',
        'EHDP', 'ELEV', 'ENAH', 'EQPT', 'EVOR', 'FATO', 'FEET', 'FIRE', 'FIVE', 'FLIG',
        'FLIP', 'FMHO', 'FOUR', 'FPAP', 'GEAR', 'GIOR', 'GNSS', 'GUID', 'HAND', 'HAOR',
        'HELI', 'HLDG', 'HOLD', 'HREE', 'HVWD', 'ICAL', 'IIGD', 'INST', 'INTL', 'ITEM',
        'JCAB', 'JIMA', 'JKOR', 'JSDF', 'KIAS', 'KROG', 'KROR', 'KUME', 'LEFT', 'LGTD',
        'LHOX', 'LINE', 'LJKW', 'LNAV', 'LOCA', 'LPXP', 'MAHF', 'MAIL', 'MATF', 'MCAS',
        'MEAN', 'MEHT', 'METE', 'MOON', 'MSAS', 'NAHA', 'NAME', 'NAVI', 'NOIS', 'NYOR',
        'OBST', 'OHIW', 'OLPE', 'ONAL', 'ONLY', 'OPER', 'OTHE', 'OVHD', 'OWER', 'PALS',
        'PAPI', 'PARL', 'PASS', 'PATH', 'PDWK', 'PLUS', 'POLE', 'PREF', 'PROC', 'PSWE',
        'PSWF', 'PSWG', 'PSWI', 'PSWM', 'PTER', 'QDPH', 'QJOH', 'RADI', 'RATS', 'RCLL',
        'REDL', 'RENL', 'RESA', 'RESC', 'SPOT', 'SROR', 'STAR', 'STOP', 'SURF', 'SYST',
        'TAKE', 'TAPS', 'THIS', 'THRU', 'TION', 'TKOF', 'TLOF', 'TODA', 'TORA', 'TREE',
        'TROR', 'TRUE', 'TTWY', 'TURE', 'TURN', 'TWDI', 'TWYB', 'TYPE', 'URVV', 'USAF',
        'VANL', 'VANR', 'VANV', 'VIGE', 'VLGH', 'VNAV', 'VORV', 'VTOL', 'WAYS', 'WBAR',
        'WBRG', 'WEST', 'WIND', 'WING', 'WRNP', 'WXUQ', 'YMOR', 'YORO', 'YROR', 'ZLWK', 'ZONE'
    }
    
    try:
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        logger.info(f"Scanning {pdf_path.name} ({total_pages} pages) for AD2 sections")
        
        airport_code_pattern = re.compile(r'\b([A-Z]{4})\b')
        current_airport = None
        
        for page_num in range(total_pages):
            try:
                page = reader.pages[page_num]
                text = page.extract_text()
                if not text:
                    continue
                
                text_upper = text.upper()
                
                # First, try to find airport code in AD 2.1 context (most reliable)
                # Pattern: "AD 2.1 CODE" or "CODE AD 2.1" or just the code near AD 2.1
                ad21_match = re.search(r'AD\s*2\.1[^\n]*\b([A-Z]{4})\b|\b([A-Z]{4})\b[^\n]*AD\s*2\.1', text, re.IGNORECASE)
                if ad21_match:
                    code = (ad21_match.group(1) or ad21_match.group(2)).upper()
                    # Filter by country prefix if provided
                    if country_prefix and not code.startswith(country_prefix):
                        # Try next match
                        continue
                    if code not in FALSE_POSITIVES:
                        current_airport = code
                
                # Check for AD 2 sections
                found_ad2 = False
                for section_name, pattern in AD2_SECTIONS.items():
                    if re.search(pattern, text_upper, re.IGNORECASE):
                        found_ad2 = True
                        
                        # If we have a current airport from AD 2.1, use it
                        if current_airport:
                            if page_num + 1 not in ad2_data[current_airport][section_name]:
                                ad2_data[current_airport][section_name].append(page_num + 1)
                            continue
                        
                        # Try to find airport code in context (e.g., "AD 2.X CODE")
                        code_in_context = re.search(rf'AD\s*2\.\d+\s+([A-Z]{{4}})\b|\b([A-Z]{{4}})\b\s+AD\s*2\.\d+', text, re.IGNORECASE)
                        if code_in_context:
                            code = (code_in_context.group(1) or code_in_context.group(2)).upper()
                            # Filter by country prefix if provided
                            if country_prefix and not code.startswith(country_prefix):
                                continue
                            if code not in FALSE_POSITIVES:
                                if page_num + 1 not in ad2_data[code][section_name]:
                                    ad2_data[code][section_name].append(page_num + 1)
                                current_airport = code
                                continue
                        
                        # Last resort: find codes on page, but filter by prefix
                        codes = set()
                        for match in airport_code_pattern.finditer(text):
                            code = match.group(1)
                            if code in FALSE_POSITIVES:
                                continue
                            # If country prefix provided, only accept codes starting with it
                            if country_prefix and not code.startswith(country_prefix):
                                continue
                            codes.add(code)
                        
                        # Associate codes with section
                        if codes:
                            for code in codes:
                                if page_num + 1 not in ad2_data[code][section_name]:
                                    ad2_data[code][section_name].append(page_num + 1)
                                if not current_airport:
                                    current_airport = code
                
                # If we found AD2 but no specific code, try to use current airport context
                if found_ad2 and current_airport:
                    for section_name, pattern in AD2_SECTIONS.items():
                        if re.search(pattern, text_upper, re.IGNORECASE):
                            if page_num + 1 not in ad2_data[current_airport][section_name]:
                                ad2_data[current_airport][section_name].append(page_num + 1)
            
            except Exception as e:
                logger.warning(f"Error processing page {page_num + 1}: {e}")
                continue
        
        # Clean up - remove airports with no sections and filter by prefix
        result = {}
        for code, sections in ad2_data.items():
            if sections:
                # Final filter by country prefix
                if country_prefix and not code.startswith(country_prefix):
                    continue
                if code not in FALSE_POSITIVES:
                    result[code] = dict(sections)
        
        return result
    
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        return {}

def extract_airport_info_from_ad2(pdf_path: Path, airport_code: str, page_numbers: List[int]) -> Dict:
    """
    Extract airport information from AD2 sections on specified pages
    """
    airport_info = {
        'airportCode': airport_code.upper(),
        'airportName': '',
        'operationalHours': [],
        'contacts': [],
        'ad2_1': '',
        'ad2_2': '',
        'ad2_3': '',
        'ad2_6': '',
        'ad2_24': '',
    }
    
    try:
        reader = PdfReader(str(pdf_path))
        
        for page_num in page_numbers:
            if page_num > len(reader.pages):
                continue
            
            try:
                page = reader.pages[page_num - 1]  # Convert to 0-indexed
                text = page.extract_text()
                if not text:
                    continue
                
                text_upper = text.upper()
                
                # Extract AD 2.1 - Location Indicator / Airport Name
                if re.search(AD2_SECTIONS['AD_2_1'], text_upper, re.IGNORECASE):
                    # Try to find airport name pattern: "CODE - NAME" or "CODE NAME"
                    # Look for patterns like "LOWW - Wien-Schwechat" or "LOWW Wien"
                    name_patterns = [
                        re.search(rf'{airport_code}\s*[-–]\s*([^\n]+)', text, re.IGNORECASE),
                        re.search(rf'{airport_code}\s+([A-Z][^\n]{3,})', text),
                    ]
                    for pattern in name_patterns:
                        if pattern:
                            name = pattern.group(1).strip()
                            # Clean up name (remove common suffixes)
                            name = re.sub(r'\s*(AD\s*2\.\d+|AERODROME|LOCATION).*', '', name, flags=re.IGNORECASE)
                            if len(name) > 3:  # Valid name
                                airport_info['airportName'] = name
                                break
                    airport_info['ad2_1'] = text[:1000]  # First 1000 chars
                
                # Extract AD 2.3 - Operational Hours
                if re.search(AD2_SECTIONS['AD_2_3'], text_upper, re.IGNORECASE):
                    # Extract hours patterns
                    hours_patterns = [
                        r'H\s*24|24H|24\s*HR',
                        r'(\d{2}[:.]?\d{2})\s*[-–]\s*(\d{2}[:.]?\d{2})',
                        r'MON[DAY]?.*?(\d{2}[:.]?\d{2})\s*[-–]\s*(\d{2}[:.]?\d{2})',
                    ]
                    for pattern in hours_patterns:
                        matches = re.finditer(pattern, text, re.IGNORECASE)
                        for match in matches:
                            airport_info['operationalHours'].append({
                                'day': 'General',
                                'hours': match.group(0).replace('.', ':')
                            })
                    airport_info['ad2_3'] = text[:1000]
                
                # Extract AD 2.24 - Contact Information
                if re.search(AD2_SECTIONS['AD_2_24'], text_upper, re.IGNORECASE) or 'CONTACT' in text_upper:
                    # Extract emails
                    emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
                    # Extract phones
                    phones = re.findall(r'(?:\+?\d{1,3})?\s*(?:\(\d+\)\s*)?(?:\d[\s-]?){6,}', text)
                    
                    for i, phone in enumerate(phones[:3]):
                        airport_info['contacts'].append({
                            'type': f'Contact {i+1}',
                            'phone': phone.strip(),
                            'email': emails[i] if i < len(emails) else '',
                            'name': '',
                            'notes': ''
                        })
                    airport_info['ad2_24'] = text[:1000]
                
                # Extract AD 2.2 - Geographical Data
                if re.search(AD2_SECTIONS['AD_2_2'], text_upper, re.IGNORECASE):
                    airport_info['ad2_2'] = text[:1000]
                
                # Extract AD 2.6 - Rescue and Fire Fighting
                if re.search(AD2_SECTIONS['AD_2_6'], text_upper, re.IGNORECASE):
                    airport_info['ad2_6'] = text[:1000]
            
            except Exception as e:
                logger.warning(f"Error extracting from page {page_num}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Error extracting airport info: {e}")
    
    return airport_info

def process_pdf_for_ad2(pdf_path: Path, country: Optional[str] = None) -> Dict:
    """
    Process a PDF and extract AD2 sections with page numbers and airport info
    """
    logger.info(f"Processing {pdf_path.name} for AD2 sections")
    
    # Get country prefix for filtering
    country_prefix = None
    if country and country in COUNTRY_TO_PREFIX:
        country_prefix = COUNTRY_TO_PREFIX[country]
    
    # Find AD2 sections and page numbers
    ad2_sections = find_ad2_sections(pdf_path, country_prefix)
    
    # Extract airport information for each airport found
    airport_data = {}
    for airport_code, sections in ad2_sections.items():
        # Get all page numbers for this airport
        all_pages = []
        for section_pages in sections.values():
            all_pages.extend(section_pages)
        all_pages = sorted(set(all_pages))
        
        # Extract info from those pages
        airport_info = extract_airport_info_from_ad2(pdf_path, airport_code, all_pages)
        airport_info['ad2_pages'] = {section: pages for section, pages in sections.items()}
        airport_data[airport_code] = airport_info
    
    return airport_data

def process_all_pdfs(aip_folder: Path) -> Dict:
    """
    Process all PDFs in the AIP folder and extract AD2 data
    """
    results = defaultdict(lambda: {'country': '', 'airports': {}})
    
    # Process single PDF files in root
    for pdf_file in sorted(aip_folder.glob('*.pdf')):
        if pdf_file.name.startswith('.'):
            continue
        
        # Try to determine country from filename
        country = normalize_country_name(pdf_file.stem)
        if country and country in COUNTRY_TO_PREFIX:
            prefix = COUNTRY_TO_PREFIX[country]
            airport_data = process_pdf_for_ad2(pdf_file, country)
            if airport_data:
                results[prefix]['country'] = country
                results[prefix]['airports'].update(airport_data)
    
    # Process country folders
    for country_folder in sorted(aip_folder.iterdir()):
        if not country_folder.is_dir() or country_folder.name.startswith('.'):
            continue
        
        country = normalize_country_name(country_folder.name)
        if not country or country not in COUNTRY_TO_PREFIX:
            continue
        
        prefix = COUNTRY_TO_PREFIX[country]
        logger.info(f"Processing folder: {country_folder.name} ({country})")
        
        for pdf_file in sorted(country_folder.glob('*.pdf')):
            airport_data = process_pdf_for_ad2(pdf_file, country)
            if airport_data:
                results[prefix]['country'] = country
                results[prefix]['airports'].update(airport_data)
    
    return dict(results)

def normalize_country_name(filename: str) -> Optional[str]:
    """Extract and normalize country name from filename"""
    # Same as in analyze_pdf_aips.py
    name = filename.replace(' AIP.pdf', '').replace(' Aip.pdf', '').replace(' AIP', '').replace(' Aip', '').replace('.pdf', '').replace('AIP-', '').replace('AIP ', '').strip()
    
    if 'Afhanistan' in name or 'Afghanistan' in name:
        return 'Afghanistan'
    if 'Sudam' in name:
        return 'South Sudan'
    if 'Azeirbaijan' in name:
        return 'Azerbaijan'
    if 'Lybia' in name:
        return 'Libya'
    
    if name in COUNTRY_TO_PREFIX:
        return name
    
    name_lower = name.lower()
    for country in COUNTRY_TO_PREFIX.keys():
        if country.lower() == name_lower:
            return country
    
    return None

def main():
    """Main function"""
    aip_folder = Path("AIP's")
    output_file = Path('assets/pdf_ad2_extracted_data.json')
    
    if not aip_folder.exists():
        logger.error(f"AIP folder not found: {aip_folder}")
        return
    
    logger.info(f"Processing PDFs in {aip_folder} for AD2 sections")
    results = process_all_pdfs(aip_folder)
    
    # Save results
    output_data = {
        'description': 'AD2 section data extracted from PDF AIP files',
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'countries': {}
    }
    
    for prefix, data in results.items():
        output_data['countries'][prefix] = {
            'country': data['country'],
            'airports': data['airports']
        }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved AD2 extraction results to {output_file}")
    logger.info(f"Processed {len(results)} countries")
    for prefix, data in results.items():
        logger.info(f"  {prefix} ({data['country']}): {len(data['airports'])} airports with AD2 data")

if __name__ == '__main__':
    main()

