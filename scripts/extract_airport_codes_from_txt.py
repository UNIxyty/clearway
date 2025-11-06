#!/usr/bin/env python3
"""
Search each TXT document for "AD 2.1" to identify airport codes
Extract and save airport codes with countries to a JSON file
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional
from collections import defaultdict
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Country mapping from folder/file names
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

REGION_MAPPING = {
    'ASIA': ['afghanistan', 'azerbaijan', 'bhutan', 'brunei', 'macao', 'macau', 'maldives', 'nepal', 'iran', 'timor', 'timor-leste'],
    'EUROPE': ['andorra', 'austria', 'bulgaria', 'czech_republic', 'denmark', 'greece', 'ireland', 'italy', 'malta'],
    'AFRICA': ['angola', 'djibouti', 'ethiopia', 'libya', 'seychelles', 'south_africa', 'sudan'],
    'NORTH_AMERICA': ['antigua_and_barbuda', 'cuba', 'haiti', 'trinidad_and_tobago'],
}

def get_region(country: str) -> str:
    """Get region for a country"""
    country_lower = country.lower().replace(' ', '_')
    for region, countries in REGION_MAPPING.items():
        if country_lower in countries:
            return region
    return 'UNKNOWN'

def normalize_country_name(name: str) -> str:
    """Normalize country name from folder/file name"""
    name = name.lower().replace(' ', '_').replace('-', '_')
    # Remove common suffixes
    name = name.replace('_aip', '').replace('_aip.pdf', '').replace('.pdf', '').replace('.txt', '')
    return name

def get_country_from_path(file_path: Path, aip_dir: Path) -> Optional[str]:
    """Extract country name from file path"""
    # Get relative path from AIP directory
    try:
        relative = file_path.relative_to(aip_dir)
    except ValueError:
        return None
    
    # If file is in a subfolder, use folder name
    if len(relative.parts) > 1:
        folder_name = relative.parts[0]
        return normalize_country_name(folder_name)
    
    # If file is in root, use filename
    filename = relative.stem
    return normalize_country_name(filename)

def find_ad21_sections(text: str) -> List[Dict]:
    """Find all AD 2.1 sections in text and extract airport codes"""
    sections = []
    
    # Pattern to find AD 2.1 sections
    # AD 2.1 can appear as "AD 2.1", "AD2.1", "AD-2.1", etc.
    ad21_pattern = re.compile(r'AD\s*[-\.]?\s*2\.1', re.IGNORECASE)
    
    # Split text into lines for better processing
    lines = text.split('\n')
    
    # Find all AD 2.1 occurrences
    for i, line in enumerate(lines):
        if ad21_pattern.search(line):
            # Look for airport code in nearby lines (next 10 lines)
            section_text = '\n'.join(lines[i:min(i+20, len(lines))])
            
            # Extract 4-letter ICAO codes
            icao_pattern = re.compile(r'\b([A-Z]{4})\b')
            codes = set()
            
            for match in icao_pattern.finditer(section_text):
                code = match.group(1)
                # Filter out common false positives
                false_positives = {
                    'PAGE', 'DATE', 'TIME', 'NOTE', 'LIST', 'PART', 'SECT', 'TEXT', 
                    'CONT', 'COPY', 'ICAO', 'INFO', 'DOC', 'REV', 'AMDT', 'AIP',
                    'GEN', 'ENR', 'AD 2', 'AD 1', 'AD-2', 'AD-1'
                }
                if code not in false_positives:
                    codes.add(code)
            
            if codes:
                sections.append({
                    'line': i + 1,
                    'text': section_text[:200],  # First 200 chars for debugging
                    'codes': codes
                })
    
    return sections

def extract_airport_codes_from_txt(txt_path: Path, country: Optional[str] = None) -> Set[str]:
    """Extract airport codes from a TXT file by finding AD 2.1 sections"""
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text:
            return set()
        
        # Find AD 2.1 sections
        sections = find_ad21_sections(text)
        
        all_codes = set()
        for section in sections:
            all_codes.update(section['codes'])
        
        # If country is known, filter by prefix
        if country and country in COUNTRY_TO_PREFIX:
            prefix = COUNTRY_TO_PREFIX[country]
            filtered_codes = {code for code in all_codes if code.upper().startswith(prefix.upper())}
            if filtered_codes:
                return filtered_codes
        
        return all_codes
        
    except Exception as e:
        logger.error(f"Error processing {txt_path.name}: {e}")
        return set()

def count_ad21_occurrences(text: str) -> int:
    """Count how many times 'AD 2.1' appears in the text"""
    pattern = re.compile(r'AD\s*[-\.]?\s*2\.1', re.IGNORECASE)
    return len(pattern.findall(text))

def process_txt_directory(txt_dir: Path, aip_dir: Path) -> Dict:
    """Process all TXT files and extract airport codes"""
    results = defaultdict(lambda: {
        'country': '',
        'region': 'UNKNOWN',
        'airports': set(),
        'ad21_count': 0,
        'files_processed': 0
    })
    
    # Process single TXT files in root
    for txt_file in sorted(txt_dir.glob('*.txt')):
        if txt_file.name.startswith('.'):
            continue
        
        country = get_country_from_path(txt_file, aip_dir)
        if not country:
            logger.warning(f"Could not determine country for {txt_file.name}")
            continue
        
        logger.info(f"Processing: {txt_file.name} -> {country}")
        
        # Count AD 2.1 occurrences
        with open(txt_file, 'r', encoding='utf-8') as f:
            text = f.read()
        ad21_count = count_ad21_occurrences(text)
        
        # Extract airport codes
        codes = extract_airport_codes_from_txt(txt_file, country)
        
        if country in COUNTRY_TO_PREFIX:
            prefix = COUNTRY_TO_PREFIX[country]
            results[prefix]['country'] = country.replace('_', ' ').title()
            results[prefix]['region'] = get_region(country)
            results[prefix]['airports'].update(codes)
            results[prefix]['ad21_count'] += ad21_count
            results[prefix]['files_processed'] += 1
            
            logger.info(f"  Found {ad21_count} AD 2.1 sections, {len(codes)} airport codes")
    
    # Process country folders
    for country_folder in sorted(txt_dir.iterdir()):
        if not country_folder.is_dir() or country_folder.name.startswith('.'):
            continue
        
        country = normalize_country_name(country_folder.name)
        logger.info(f"\nProcessing folder: {country_folder.name} -> {country}")
        
        # Process TXT files in folder
        for txt_file in sorted(country_folder.glob('*.txt')):
            if txt_file.name.startswith('.'):
                continue
            
            logger.info(f"  Processing: {txt_file.name}")
            
            # Count AD 2.1 occurrences
            with open(txt_file, 'r', encoding='utf-8') as f:
                text = f.read()
            ad21_count = count_ad21_occurrences(text)
            
            # Extract airport codes
            codes = extract_airport_codes_from_txt(txt_file, country)
            
            if country in COUNTRY_TO_PREFIX:
                prefix = COUNTRY_TO_PREFIX[country]
                results[prefix]['country'] = country.replace('_', ' ').title()
                results[prefix]['region'] = get_region(country)
                results[prefix]['airports'].update(codes)
                results[prefix]['ad21_count'] += ad21_count
                results[prefix]['files_processed'] += 1
                
                logger.info(f"    Found {ad21_count} AD 2.1 sections, {len(codes)} airport codes")
    
    return results

def save_airport_codes_json(results: Dict, output_path: Path):
    """Save airport codes to JSON file"""
    output_data = {
        'description': 'ICAO airport codes extracted from AIP TXT files by searching for AD 2.1 sections',
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'codes': {}
    }
    
    for prefix, data in results.items():
        output_data['codes'][prefix] = {
            'country': data['country'],
            'region': data['region'],
            'airports': sorted(list(data['airports'])),
            'ad21_count': data['ad21_count'],
            'files_processed': data['files_processed']
        }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved airport codes to {output_path}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract airport codes from TXT AIP files')
    parser.add_argument('--txt-dir', type=str, default="AIP's/txt_versions", help='Path to TXT directory')
    parser.add_argument('--aip-dir', type=str, default="AIP's", help='Path to AIP directory (for path resolution)')
    parser.add_argument('--output', type=str, default="assets/airport_codes_from_txt.json", help='Output JSON file')
    args = parser.parse_args()
    
    txt_dir = Path(args.txt_dir)
    aip_dir = Path(args.aip_dir)
    output_path = Path(args.output)
    
    if not txt_dir.exists():
        logger.error(f"TXT directory not found: {txt_dir}")
        logger.info("Please run convert_pdfs_to_txt.py first")
        return
    
    logger.info(f"Extracting airport codes from TXT files in {txt_dir}")
    
    results = process_txt_directory(txt_dir, aip_dir)
    
    logger.info(f"\n{'='*60}")
    logger.info("EXTRACTION SUMMARY")
    logger.info(f"{'='*60}")
    for prefix, data in sorted(results.items()):
        logger.info(f"{prefix} ({data['country']}): {len(data['airports'])} airports, {data['ad21_count']} AD 2.1 sections")
    
    save_airport_codes_json(results, output_path)
    logger.info(f"\nDone!")

if __name__ == '__main__':
    main()

