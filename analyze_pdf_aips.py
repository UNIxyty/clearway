#!/usr/bin/env python3
"""
Analyze PDF AIP files to:
1. Identify page numbers with airport data (AD 2 sections)
2. Rename files/folders to consistent format
3. Extract airport codes and update airport_codes.json
4. Create documentation of page numbers per country
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

# Load country mapping from extract_airport_codes_from_pdfs.py
COUNTRY_TO_PREFIX = {
    'Afghanistan': 'OA',
    'Andorra': 'LE',
    'Angola': 'FN',
    'Antigua and Barbuda': 'TAPA',
    'Austria': 'LO',
    'Azerbaijan': 'UB',
    'Bhutan': 'VQ',
    'Bulgaria': 'LZ',
    'Canada': 'C',
    'Cuba': 'MU',
    'Czech Republic': 'LK',
    'Denmark': 'EK',
    'Djibouti': 'HD',
    'Ethiopia': 'HA',
    'Greece': 'LG',
    'Haiti': 'MT',
    'Iran': 'OI',
    'Ireland': 'EI',
    'Italy': 'LI',
    'Libya': 'HL',
    'Lybia': 'HL',
    'Macau': 'VM',
    'Macao': 'VM',
    'Malta': 'LM',
    'Maldives': 'VR',
    'Nepal': 'VN',
    'Saint Vincent and the Grenadines': 'TV',
    'Seychelles': 'FS',
    'South Africa': 'FA',
    'South Sudan': 'HSS',
    'Sudan': 'HS',
    'Timor': 'WP',
    'Timor-Leste': 'WP',
    'Trinidad and Tobago': 'TT',
    'Brunei': 'WBA',
}

REGION_MAPPING = {
    'ASIA': ['Afghanistan', 'Azerbaijan', 'Bhutan', 'Brunei', 'Macau', 'Macao', 'Maldives', 'Nepal', 'Iran', 'Timor', 'Timor-Leste'],
    'EUROPE': ['Andorra', 'Austria', 'Bulgaria', 'Czech Republic', 'Denmark', 'Greece', 'Ireland', 'Italy', 'Malta'],
    'AFRICA': ['Angola', 'Djibouti', 'Ethiopia', 'Libya', 'Lybia', 'Seychelles', 'South Africa', 'Sudan', 'South Sudan'],
    'NORTH_AMERICA': ['Antigua and Barbuda', 'Canada', 'Cuba', 'Haiti', 'Trinidad and Tobago'],
}

def get_region(country: str) -> str:
    """Get region for a country"""
    for region, countries in REGION_MAPPING.items():
        if country in countries:
            return region
    return 'UNKNOWN'

def normalize_country_name(filename: str) -> Optional[str]:
    """Extract and normalize country name from filename or folder name"""
    # Remove common suffixes and fix typos
    name = filename.replace(' AIP.pdf', '').replace(' Aip.pdf', '').replace(' AIP', '').replace(' Aip', '').replace('.pdf', '').replace('AIP-', '').replace('AIP ', '').strip()
    
    # Handle special cases and typos
    if 'Afhanistan' in name or 'Afghanistan' in name:
        return 'Afghanistan'
    if 'Sudam' in name:
        return 'South Sudan'
    if 'Azeirbaijan' in name:
        return 'Azerbaijan'
    if 'Lybia' in name:
        return 'Libya'
    
    # Try exact match first
    if name in COUNTRY_TO_PREFIX:
        return name
    
    # Try case-insensitive match
    name_lower = name.lower()
    for country, prefix in COUNTRY_TO_PREFIX.items():
        if country.lower() == name_lower:
            return country
    
    # Try partial match
    for country, prefix in COUNTRY_TO_PREFIX.items():
        if name_lower in country.lower() or country.lower() in name_lower:
            return country
    
    return None

def normalize_filename(country: str) -> str:
    """Convert country name to normalized filename format (lowercase with underscores)"""
    return country.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace("'", '')

def find_airport_data_pages(pdf_path: Path) -> Dict[str, List[int]]:
    """
    Scan PDF and identify pages containing airport data
    Returns: dict mapping airport codes to page numbers
    """
    airport_pages = {}
    try:
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        logger.info(f"Scanning {pdf_path.name} ({total_pages} pages)")
        
        # Patterns to identify airport data sections
        ad2_pattern = re.compile(r'AD\s*2\.', re.IGNORECASE)
        airport_code_pattern = re.compile(r'\b([A-Z]{4})\b')
        
        # Scan each page
        for page_num in range(total_pages):
            try:
                page = reader.pages[page_num]
                text = page.extract_text()
                if not text:
                    continue
                
                text_upper = text.upper()
                
                # Check for AD 2 sections (airport data)
                if ad2_pattern.search(text):
                    # Extract potential airport codes from this page
                    codes = set()
                    for match in airport_code_pattern.finditer(text):
                        code = match.group(1)
                        # Filter out common false positives
                        if code not in ['PAGE', 'DATE', 'TIME', 'NOTE', 'LIST', 'PART', 'SECT', 'TEXT', 'CONT', 'COPY', 'ICAO', 'INFO', 'DOC']:
                            codes.add(code)
                    
                    # Store page numbers for each airport code found
                    for code in codes:
                        if code not in airport_pages:
                            airport_pages[code] = []
                        if page_num + 1 not in airport_pages[code]:  # +1 because pages are 1-indexed
                            airport_pages[code].append(page_num + 1)
                    
                    if codes:
                        logger.debug(f"  Page {page_num + 1}: Found AD 2 section with codes: {sorted(codes)}")
            
            except Exception as e:
                logger.warning(f"  Error processing page {page_num + 1}: {e}")
                continue
        
        if airport_pages:
            logger.info(f"  Found airport data on {len(airport_pages)} different airport codes")
        else:
            logger.warning(f"  No airport data sections found")
        
        return airport_pages
    
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        return {}

def extract_icao_codes(text: str) -> Set[str]:
    """Extract ICAO airport codes from text"""
    codes = set()
    
    # Pattern: 4 uppercase letters (ICAO code pattern)
    pattern = r'\b([A-Z]{4})\b'
    matches = re.findall(pattern, text)
    for match in matches:
        # Filter out common false positives
        if match not in ['PAGE', 'DATE', 'TIME', 'NOTE', 'LIST', 'AD 2', 'AD 1', 'GEN ', 'GEN1', 'GEN2', 'GEN3', 'GEN4', 'GEN5', 'GEN6', 'GEN7', 'GEN8', 'GEN9', 'ENR ', 'ENR1', 'ENR2', 'ENR3', 'ENR4', 'ENR5', 'ENR6', 'PART', 'SECT', 'TEXT', 'CONT', 'COPY', 'REV ', 'REV1', 'REV2', 'REV3', 'REV4', 'REV5', 'REV6', 'REV7', 'REV8', 'REV9', 'AMDT', 'AMDT1', 'AMDT2', 'AMDT3', 'AMDT4', 'AMDT5', 'AMDT6', 'AMDT7', 'AMDT8', 'AMDT9', 'AIP ', 'AIP1', 'AIP2', 'AIP3', 'AIP4', 'AIP5', 'AIP6', 'AIP7', 'AIP8', 'AIP9', 'ICAO', 'INFO', 'DOC ', 'DOC1', 'DOC2', 'DOC3', 'DOC4', 'DOC5', 'DOC6', 'DOC7', 'DOC8', 'DOC9']:
            codes.add(match)
    
    return codes

def process_pdf_for_codes(pdf_path: Path, country: Optional[str] = None) -> Set[str]:
    """Process a single PDF and extract ICAO codes"""
    try:
        reader = PdfReader(str(pdf_path))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        if not text:
            return set()
        
        codes = extract_icao_codes(text)
        
        # Filter codes by country prefix if country is known
        if country and country in COUNTRY_TO_PREFIX:
            prefix = COUNTRY_TO_PREFIX[country]
            filtered_codes = {code for code in codes if code.upper().startswith(prefix.upper())}
            if filtered_codes:
                return filtered_codes
            else:
                return codes
        
        return codes
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {e}")
        return set()

def analyze_and_rename_aip_folder(folder_path: Path, dry_run: bool = False) -> Dict:
    """Analyze PDFs, extract page numbers, rename files, and collect airport codes"""
    results = {
        'page_mapping': {},  # {country: {airport_code: [page_numbers]}}
        'airport_codes': defaultdict(lambda: {'country': '', 'region': 'UNKNOWN', 'airports': set()}),
        'renamed_files': [],
        'file_structure': {}
    }
    
    # Process single PDF files in root
    for pdf_file in sorted(folder_path.glob('*.pdf')):
        if pdf_file.name == '.DS_Store':
            continue
        
        country = normalize_country_name(pdf_file.stem)
        if not country:
            logger.warning(f"Could not determine country for {pdf_file.name}")
            continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {pdf_file.name} -> {country}")
        logger.info(f"{'='*60}")
        
        # Find airport data pages
        airport_pages = find_airport_data_pages(pdf_file)
        if airport_pages:
            results['page_mapping'][country] = airport_pages
        
        # Extract airport codes
        codes = process_pdf_for_codes(pdf_file, country)
        if codes and country in COUNTRY_TO_PREFIX:
            prefix = COUNTRY_TO_PREFIX[country]
            results['airport_codes'][prefix]['country'] = country
            results['airport_codes'][prefix]['region'] = get_region(country)
            results['airport_codes'][prefix]['airports'].update(codes)
        
        # Rename file
        normalized_name = normalize_filename(country)
        new_name = f"{normalized_name}_aip.pdf"
        new_path = pdf_file.parent / new_name
        
        if pdf_file.name != new_name:
            if not dry_run:
                pdf_file.rename(new_path)
                logger.info(f"  Renamed: {pdf_file.name} -> {new_name}")
            else:
                logger.info(f"  Would rename: {pdf_file.name} -> {new_name}")
            results['renamed_files'].append((str(pdf_file), str(new_path)))
    
    # Process country folders
    for country_folder in sorted(folder_path.iterdir()):
        if not country_folder.is_dir() or country_folder.name.startswith('.'):
            continue
        
        country = normalize_country_name(country_folder.name)
        if not country:
            logger.warning(f"Could not determine country for folder {country_folder.name}")
            continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing folder: {country_folder.name} -> {country}")
        logger.info(f"{'='*60}")
        
        # Rename folder
        normalized_name = normalize_filename(country)
        new_folder_name = normalized_name
        new_folder_path = country_folder.parent / new_folder_name
        
        if country_folder.name != new_folder_name:
            if not dry_run:
                country_folder.rename(new_folder_path)
                logger.info(f"  Renamed folder: {country_folder.name} -> {new_folder_name}")
            else:
                logger.info(f"  Would rename folder: {country_folder.name} -> {new_folder_name}")
                new_folder_path = country_folder  # Use original for processing
        
        # Process PDFs in folder
        airport_pages_by_file = {}
        for pdf_file in sorted(new_folder_path.glob('*.pdf')):
            if pdf_file.name.startswith('.'):
                continue
            
            logger.info(f"  Processing: {pdf_file.name}")
            
            # Find airport data pages (individual airport PDFs)
            airport_pages = find_airport_data_pages(pdf_file)
            if airport_pages:
                airport_pages_by_file[pdf_file.name] = airport_pages
            
            # Extract airport codes
            codes = process_pdf_for_codes(pdf_file, country)
            if codes:
                prefix = COUNTRY_TO_PREFIX.get(country, '')
                if prefix:
                    results['airport_codes'][prefix]['country'] = country
                    results['airport_codes'][prefix]['region'] = get_region(country)
                    results['airport_codes'][prefix]['airports'].update(codes)
        
        if airport_pages_by_file:
            results['page_mapping'][country] = airport_pages_by_file
        
        results['file_structure'][country] = {
            'folder': str(new_folder_path.name),
            'files': [f.name for f in sorted(new_folder_path.glob('*.pdf'))]
        }
    
    return results

def update_airport_codes_json(extracted_codes: Dict, output_path: Path):
    """Update airport_codes.json with extracted codes"""
    # Load existing codes
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        existing_codes = existing_data.get('codes', {})
    else:
        existing_codes = {}
        existing_data = {
            'description': 'ICAO airport codes organized by country prefix for auto-detection',
            'last_updated': '',
            'codes': {}
        }
    
    # Merge extracted codes with existing codes
    for prefix, data in extracted_codes.items():
        if prefix in existing_codes:
            # Merge airports (keep unique)
            existing_airports = set(existing_codes[prefix].get('airports', []))
            new_airports = set(data['airports'])
            merged_airports = sorted(list(existing_airports | new_airports))
            existing_codes[prefix]['airports'] = merged_airports
            # Update country/region if not set
            if not existing_codes[prefix].get('country'):
                existing_codes[prefix]['country'] = data['country']
            if not existing_codes[prefix].get('region') or existing_codes[prefix]['region'] == 'UNKNOWN':
                existing_codes[prefix]['region'] = data['region']
        else:
            # Add new prefix
            existing_codes[prefix] = {
                'country': data['country'],
                'region': data['region'],
                'airports': sorted(list(data['airports']))
            }
    
    # Update metadata
    existing_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    existing_data['codes'] = existing_codes
    
    # Write updated data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Updated {output_path} with {len(existing_codes)} country prefixes")

def save_page_mapping_report(page_mapping: Dict, output_path: Path):
    """Save page mapping report to JSON file"""
    report = {
        'description': 'Page numbers with airport data (AD 2 sections) in PDF AIP files',
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'countries': page_mapping
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved page mapping report to {output_path}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze PDF AIP files and extract airport data')
    parser.add_argument('--dry-run', action='store_true', help='Do not rename files, just show what would be done')
    parser.add_argument('--aip-folder', type=str, default="AIP's", help='Path to AIP folder')
    args = parser.parse_args()
    
    aip_folder = Path(args.aip_folder)
    output_file = Path('assets/airport_codes.json')
    report_file = Path('assets/pdf_aip_page_mapping.json')
    
    if not aip_folder.exists():
        logger.error(f"AIP folder not found: {aip_folder}")
        return
    
    logger.info(f"{'DRY RUN: ' if args.dry_run else ''}Processing PDFs in {aip_folder}")
    
    results = analyze_and_rename_aip_folder(aip_folder, dry_run=args.dry_run)
    
    # Convert sets to lists for JSON serialization
    airport_codes_dict = {}
    for prefix, data in results['airport_codes'].items():
        airport_codes_dict[prefix] = {
            'country': data['country'],
            'region': data['region'],
            'airports': sorted(list(data['airports']))
        }
    
    logger.info(f"\n{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Countries processed: {len(results['page_mapping'])}")
    logger.info(f"Countries with airport codes: {len(airport_codes_dict)}")
    for prefix, data in sorted(airport_codes_dict.items()):
        logger.info(f"  {prefix} ({data['country']}): {len(data['airports'])} airports")
    logger.info(f"Files renamed: {len(results['renamed_files'])}")
    
    # Update airport_codes.json
    if not args.dry_run:
        update_airport_codes_json(airport_codes_dict, output_file)
        save_page_mapping_report(results['page_mapping'], report_file)
        logger.info("\nDone!")
    else:
        logger.info("\nDry run complete. Use without --dry-run to apply changes.")

if __name__ == '__main__':
    main()

