#!/usr/bin/env python3
"""
Extract specific information from AIP TXT files:
- AD 2.2: Types of traffic permitted (IFR/VFR) and Remarks
- AD 2.3: AD Administrator/AD Operator, Customs and immigration, ATS, Remarks
- AD 2.6: AD Category for fire fighting
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_section_content(text: str, section_pattern: str, airport_code: Optional[str] = None) -> Optional[str]:
    """
    Find content of a specific section (e.g., AD 2.2, AD 2.3, AD 2.6)
    Returns the text content of that section
    """
    # Pattern to match section header
    pattern = re.compile(section_pattern, re.IGNORECASE | re.MULTILINE)
    
    lines = text.split('\n')
    section_start = None
    
    # Find section start
    for i, line in enumerate(lines):
        if pattern.search(line):
            # If airport code is specified, check if it's in nearby lines
            if airport_code:
                # Check previous and next few lines for airport code
                context = '\n'.join(lines[max(0, i-5):min(i+20, len(lines))])
                if airport_code.upper() not in context.upper():
                    continue
            section_start = i
            break
    
    if section_start is None:
        return None
    
    # Extract section content until next AD section or end of document
    section_lines = []
    next_section_pattern = re.compile(r'AD\s*[-\.]?\s*2\.\d+', re.IGNORECASE)
    
    for i in range(section_start + 1, len(lines)):
        line = lines[i]
        
        # Stop if we hit another AD 2.x section (but not subsections like 2.2.1)
        if next_section_pattern.search(line) and not line.strip().startswith('AD 2.' + section_pattern.split(r'2\.')[1].split(r'\.')[0]):
            # Check if it's a different main section (2.2, 2.3, etc.)
            current_section_num = section_pattern.split(r'2\.')[1].split(r'\.')[0]
            match = next_section_pattern.search(line)
            if match:
                found_section = match.group(0)
                if current_section_num not in found_section:
                    break
        
        section_lines.append(line)
        
        # Limit section length (stop after 100 lines or empty section marker)
        if len(section_lines) > 100:
            break
    
    return '\n'.join(section_lines)

def extract_ad22_info(text: str, airport_code: Optional[str] = None) -> Dict:
    """Extract AD 2.2 information: Types of traffic permitted and Remarks"""
    section_text = find_section_content(text, r'AD\s*[-\.]?\s*2\.2', airport_code)
    
    if not section_text:
        return {
            'types_of_traffic_permitted': None,
            'remarks': None
        }
    
    result = {
        'types_of_traffic_permitted': None,
        'remarks': None
    }
    
    # Look for "Types of traffic permitted" or similar
    traffic_patterns = [
        r'Types?\s+of\s+traffic\s+permitted[:\s]+([^\n]+)',
        r'Traffic\s+permitted[:\s]+([^\n]+)',
        r'IFR[:\s/]+VFR[:\s]+([^\n]+)',
        r'(IFR|VFR|IFR/VFR|VFR/IFR)',
    ]
    
    for pattern in traffic_patterns:
        match = re.search(pattern, section_text, re.IGNORECASE)
        if match:
            result['types_of_traffic_permitted'] = match.group(1) if len(match.groups()) > 0 else match.group(0)
            break
    
    # Look for Remarks section
    remarks_patterns = [
        r'Remarks?[:\s]+(.+?)(?=\n\s*[A-Z]|\n\n|$)',
        r'Note[:\s]+(.+?)(?=\n\s*[A-Z]|\n\n|$)',
    ]
    
    for pattern in remarks_patterns:
        match = re.search(pattern, section_text, re.IGNORECASE | re.DOTALL)
        if match:
            remarks = match.group(1).strip()
            if len(remarks) > 10:  # Filter out very short matches
                result['remarks'] = remarks[:500]  # Limit length
                break
    
    return result

def extract_ad23_info(text: str, airport_code: Optional[str] = None) -> Dict:
    """Extract AD 2.3 information: AD Administrator/Operator, Customs, ATS, Remarks"""
    section_text = find_section_content(text, r'AD\s*[-\.]?\s*2\.3', airport_code)
    
    if not section_text:
        return {
            'ad_administrator': None,
            'ad_operator': None,
            'customs_and_immigration': None,
            'ats': None,
            'remarks': None
        }
    
    result = {
        'ad_administrator': None,
        'ad_operator': None,
        'customs_and_immigration': None,
        'ats': None,
        'remarks': None
    }
    
    # Look for AD Administrator
    admin_patterns = [
        r'AD\s+Administrator[:\s]+(.+?)(?=\n|$)',
        r'Aerodrome\s+Administrator[:\s]+(.+?)(?=\n|$)',
        r'Administrator[:\s]+(.+?)(?=\n|$)',
    ]
    
    for pattern in admin_patterns:
        match = re.search(pattern, section_text, re.IGNORECASE)
        if match:
            result['ad_administrator'] = match.group(1).strip()[:200]
            break
    
    # Look for AD Operator
    operator_patterns = [
        r'AD\s+Operator[:\s]+(.+?)(?=\n|$)',
        r'Aerodrome\s+Operator[:\s]+(.+?)(?=\n|$)',
        r'Operator[:\s]+(.+?)(?=\n|$)',
    ]
    
    for pattern in operator_patterns:
        match = re.search(pattern, section_text, re.IGNORECASE)
        if match:
            result['ad_operator'] = match.group(1).strip()[:200]
            break
    
    # Look for Customs and immigration
    customs_patterns = [
        r'Customs\s+and\s+immigration[:\s]+(.+?)(?=\n\s*[A-Z]|\n\n|$)',
        r'Customs[:\s]+(.+?)(?=\n\s*[A-Z]|\n\n|$)',
        r'Immigration[:\s]+(.+?)(?=\n\s*[A-Z]|\n\n|$)',
    ]
    
    for pattern in customs_patterns:
        match = re.search(pattern, section_text, re.IGNORECASE | re.DOTALL)
        if match:
            customs = match.group(1).strip()
            if len(customs) > 5:
                result['customs_and_immigration'] = customs[:300]
                break
    
    # Look for ATS
    ats_patterns = [
        r'ATS[:\s]+(.+?)(?=\n\s*[A-Z]|\n\n|$)',
        r'Air\s+Traffic\s+Services?[:\s]+(.+?)(?=\n\s*[A-Z]|\n\n|$)',
    ]
    
    for pattern in ats_patterns:
        match = re.search(pattern, section_text, re.IGNORECASE | re.DOTALL)
        if match:
            ats = match.group(1).strip()
            if len(ats) > 5:
                result['ats'] = ats[:300]
                break
    
    # Look for Remarks
    remarks_patterns = [
        r'Remarks?[:\s]+(.+?)(?=\n\s*[A-Z]|\n\n|$)',
        r'Note[:\s]+(.+?)(?=\n\s*[A-Z]|\n\n|$)',
    ]
    
    for pattern in remarks_patterns:
        match = re.search(pattern, section_text, re.IGNORECASE | re.DOTALL)
        if match:
            remarks = match.group(1).strip()
            if len(remarks) > 10:
                result['remarks'] = remarks[:500]
                break
    
    return result

def extract_ad26_info(text: str, airport_code: Optional[str] = None) -> Dict:
    """Extract AD 2.6 information: AD Category for fire fighting"""
    section_text = find_section_content(text, r'AD\s*[-\.]?\s*2\.6', airport_code)
    
    if not section_text:
        return {
            'ad_category_fire_fighting': None
        }
    
    result = {
        'ad_category_fire_fighting': None
    }
    
    # Look for AD Category for fire fighting
    category_patterns = [
        r'AD\s+Category\s+for\s+fire\s+fighting[:\s]+([^\n]+)',
        r'Category\s+for\s+fire\s+fighting[:\s]+([^\n]+)',
        r'Fire\s+fighting\s+category[:\s]+([^\n]+)',
        r'Category[:\s]+([0-9]+)',
        r'Category\s+([0-9]+)',
    ]
    
    for pattern in category_patterns:
        match = re.search(pattern, section_text, re.IGNORECASE)
        if match:
            result['ad_category_fire_fighting'] = match.group(1).strip()[:50]
            break
    
    return result

def extract_airport_code_from_text(text: str) -> Optional[str]:
    """Extract airport code from text (usually near AD 2.1 or in header)"""
    # Look for 4-letter ICAO codes
    icao_pattern = re.compile(r'\b([A-Z]{4})\b')
    
    # Check first 500 characters for airport code
    header = text[:500].upper()
    matches = list(icao_pattern.finditer(header))
    
    for match in matches:
        code = match.group(1)
        # Filter out common false positives
        false_positives = {'PAGE', 'DATE', 'TIME', 'NOTE', 'LIST', 'PART', 'SECT', 'TEXT', 'CONT', 'COPY', 'ICAO', 'INFO', 'DOC'}
        if code not in false_positives:
            return code
    
    return None

def process_txt_file(txt_path: Path) -> Dict:
    """Process a single TXT file and extract all sections for all airports"""
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text:
            return {}
        
        # Find all airport codes in the document
        # Look for AD 2.1 sections to identify airports
        ad21_pattern = re.compile(r'AD\s*[-\.]?\s*2\.1', re.IGNORECASE)
        icao_pattern = re.compile(r'\b([A-Z]{4})\b')
        
        airports = {}
        lines = text.split('\n')
        
        # Find each AD 2.1 section and extract airport code
        for i, line in enumerate(lines):
            if ad21_pattern.search(line):
                # Look for airport code in nearby lines
                context = '\n'.join(lines[max(0, i-2):min(i+10, len(lines))])
                codes = set()
                for match in icao_pattern.finditer(context):
                    code = match.group(1)
                    false_positives = {'PAGE', 'DATE', 'TIME', 'NOTE', 'LIST', 'PART', 'SECT', 'TEXT', 'CONT', 'COPY', 'ICAO', 'INFO', 'DOC', 'AD 2', 'AD 1'}
                    if code not in false_positives:
                        codes.add(code)
                
                # Use the first valid code found
                if codes:
                    airport_code = sorted(codes)[0]
                    
                    # Extract sections for this airport
                    if airport_code not in airports:
                        airports[airport_code] = {
                            'airport_code': airport_code,
                            'ad22': extract_ad22_info(text, airport_code),
                            'ad23': extract_ad23_info(text, airport_code),
                            'ad26': extract_ad26_info(text, airport_code)
                        }
        
        # If no airports found via AD 2.1, try to extract from filename or text
        if not airports:
            airport_code = extract_airport_code_from_text(text)
            if airport_code:
                airports[airport_code] = {
                    'airport_code': airport_code,
                    'ad22': extract_ad22_info(text, airport_code),
                    'ad23': extract_ad23_info(text, airport_code),
                    'ad26': extract_ad26_info(text, airport_code)
                }
        
        return airports
        
    except Exception as e:
        logger.error(f"Error processing {txt_path.name}: {e}")
        return {}

def process_txt_directory(txt_dir: Path, aip_dir: Path) -> Dict:
    """Process all TXT files and extract AIP sections"""
    all_data = defaultdict(lambda: {
        'country': '',
        'airports': {}
    })
    
    # Get country mapping (define locally to avoid import issues)
    COUNTRY_TO_PREFIX = {
        'afghanistan': 'OA',
        'andorra': 'LE',
        'angola': 'FN',
        'antigua_and_barbuda': 'TAPA',
        'austria': 'LO',
        'azerbaijan': 'UB',
        'bhutan': 'VQ',
        'bulgaria': 'LB',
        'cuba': 'MU',
        'czech_republic': 'LK',
        'denmark': 'EK',
        'djibouti': 'HD',
        'ethiopia': 'HA',
        'greece': 'LG',
        'haiti': 'MT',
        'iran': 'OI',
        'ireland': 'EI',
        'italy': 'LI',
        'libya': 'HL',
        'macao': 'VM',
        'macau': 'VM',
        'malta': 'LM',
        'maldives': 'VR',
        'nepal': 'VN',
        'saint_vincent_and_the_grenadines': 'TV',
        'seychelles': 'FS',
        'south_africa': 'FA',
        'sudan': 'HS',
        'timor': 'WP',
        'timor-leste': 'WP',
        'trinidad_and_tobago': 'TT',
        'brunei': 'WB',
    }
    
    def normalize_country_name(name: str) -> str:
        """Normalize country name from folder/file name"""
        name = name.lower().replace(' ', '_').replace('-', '_')
        name = name.replace('_aip', '').replace('_aip.pdf', '').replace('.pdf', '').replace('.txt', '')
        return name
    
    def get_country_from_path(file_path: Path, aip_dir: Path) -> Optional[str]:
        """Extract country name from file path"""
        try:
            relative = file_path.relative_to(aip_dir)
        except ValueError:
            return None
        
        if len(relative.parts) > 1:
            folder_name = relative.parts[0]
            return normalize_country_name(folder_name)
        
        filename = relative.stem
        return normalize_country_name(filename)
    
    # Process single TXT files in root
    for txt_file in sorted(txt_dir.glob('*.txt')):
        if txt_file.name.startswith('.'):
            continue
        
        country = get_country_from_path(txt_file, aip_dir)
        if not country:
            continue
        
        logger.info(f"Processing: {txt_file.name}")
        airports = process_txt_file(txt_file)
        
        if country in COUNTRY_TO_PREFIX:
            prefix = COUNTRY_TO_PREFIX[country]
            country_name = country.replace('_', ' ').title()
            all_data[prefix]['country'] = country_name
            all_data[prefix]['airports'].update(airports)
            logger.info(f"  Extracted data for {len(airports)} airports")
    
    # Process country folders
    for country_folder in sorted(txt_dir.iterdir()):
        if not country_folder.is_dir() or country_folder.name.startswith('.'):
            continue
        
        country = normalize_country_name(country_folder.name)
        logger.info(f"\nProcessing folder: {country_folder.name}")
        
        for txt_file in sorted(country_folder.glob('*.txt')):
            if txt_file.name.startswith('.'):
                continue
            
            logger.info(f"  Processing: {txt_file.name}")
            airports = process_txt_file(txt_file)
            
            if country in COUNTRY_TO_PREFIX:
                prefix = COUNTRY_TO_PREFIX[country]
                country_name = country.replace('_', ' ').title()
                all_data[prefix]['country'] = country_name
                all_data[prefix]['airports'].update(airports)
                logger.info(f"    Extracted data for {len(airports)} airports")
    
    return all_data

def save_extracted_data(data: Dict, output_path: Path):
    """Save extracted AIP data to JSON file"""
    output_data = {
        'description': 'Extracted AIP information from AD 2.2, AD 2.3, and AD 2.6 sections',
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'countries': {}
    }
    
    for prefix, country_data in data.items():
        output_data['countries'][prefix] = {
            'country': country_data['country'],
            'airports': country_data['airports']
        }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved extracted data to {output_path}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract AIP sections from TXT files')
    parser.add_argument('--txt-dir', type=str, default="AIP's/txt_versions", help='Path to TXT directory')
    parser.add_argument('--aip-dir', type=str, default="AIP's", help='Path to AIP directory')
    parser.add_argument('--output', type=str, default="assets/aip_extracted_data.json", help='Output JSON file')
    args = parser.parse_args()
    
    txt_dir = Path(args.txt_dir)
    aip_dir = Path(args.aip_dir)
    output_path = Path(args.output)
    
    if not txt_dir.exists():
        logger.error(f"TXT directory not found: {txt_dir}")
        logger.info("Please run convert_pdfs_to_txt.py first")
        return
    
    logger.info(f"Extracting AIP sections from TXT files in {txt_dir}")
    
    data = process_txt_directory(txt_dir, aip_dir)
    
    logger.info(f"\n{'='*60}")
    logger.info("EXTRACTION SUMMARY")
    logger.info(f"{'='*60}")
    for prefix, country_data in sorted(data.items()):
        logger.info(f"{prefix} ({country_data['country']}): {len(country_data['airports'])} airports")
    
    save_extracted_data(data, output_path)
    logger.info(f"\nDone!")

if __name__ == '__main__':
    main()

