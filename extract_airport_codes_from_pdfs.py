#!/usr/bin/env python3
"""
Extract ICAO airport codes from PDF AIP files and update airport_codes.json
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, Set, Optional, List
from collections import defaultdict

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        raise ImportError("Please install pypdf: pip install pypdf")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Reverse mapping: country name -> ICAO prefix
# Based on country_detector.py ICAO_PREFIXES
COUNTRY_TO_PREFIX = {
    'Afghanistan': 'OA',
    'Albania': 'LA',
    'Algeria': 'DA',
    'Andorra': 'LE',
    'Angola': 'FN',
    'Antigua and Barbuda': 'TAPA',
    'Argentina': 'SA',
    'Armenia': 'UD',
    'Australia': 'Y',
    'Austria': 'LO',
    'Azerbaijan': 'UB',
    'Bahamas': 'MY',
    'Bahrain': 'OB',
    'Bangladesh': 'VG',
    'Barbados': 'TBPB',
    'Belarus': 'UM',
    'Belgium': 'EB',
    'Belize': 'MZ',
    'Benin': 'DB',
    'Bhutan': 'VQ',
    'Bolivia': 'SL',
    'Bosnia and Herzegovina': 'LQ',
    'Brazil': 'SB',
    'Brunei': 'WBA',
    'Bulgaria': 'LZ',
    'Burkina Faso': 'DF',
    'Cabo Verde': 'GV',
    'Cambodia': 'VDP',
    'Cameroon': 'FK',
    'Canada': 'C',
    'Central African Republic': 'FE',
    'Chad': 'FT',
    'Chile': 'SC',
    'China': 'ZB',
    'Colombia': 'SK',
    'Comoros': 'FM',
    'Congo': 'FC',
    'Costa Rica': 'MR',
    'Croatia': 'LD',
    'Cuba': 'MU',
    'Cyprus': 'LC',
    'Czech Republic': 'LK',
    'Denmark': 'EK',
    'Djibouti': 'HD',
    'Dominica': 'TD',
    'Dominican Republic': 'MD',
    'East Timor (Timor-Leste)': 'WP',
    'Timor': 'WP',
    'Timor-Leste': 'WP',
    'Ecuador': 'SE',
    'Egypt': 'HE',
    'El Salvador': 'MS',
    'Equatorial Guinea': 'FG',
    'Eritrea': 'HH',
    'Estonia': 'EE',
    'Eswatini': 'FD',
    'Ethiopia': 'HA',
    'Fiji': 'NF',
    'Finland': 'EF',
    'France': 'LF',
    'Gabon': 'FO',
    'Gambia': 'GB',
    'Georgia': 'UG',
    'Germany': 'ED',
    'Ghana': 'DG',
    'Greece': 'LG',
    'Grenada': 'TGPY',
    'Guatemala': 'MG',
    'Guinea': 'GU',
    'Guinea-Bissau': 'GG',
    'Guyana': 'SY',
    'Haiti': 'MT',
    'Honduras': 'MH',
    'Hong Kong': 'VH',
    'Hungary': 'LH',
    'Iceland': 'BI',
    'India': 'VI',
    'Indonesia': 'WI',
    'Iran': 'OI',
    'Iraq': 'OR',
    'Ireland': 'EI',
    'Israel': 'LL',
    'Italy': 'LI',
    'Ivory Coast (Côte d\'Ivoire)': 'DI',
    'Jamaica': 'MK',
    'Japan': 'RJ',
    'Jordan': 'OJ',
    'Kazakhstan': 'UA',
    'Kenya': 'HK',
    'Kiribati': 'NG',
    'Kosovo': 'BK',
    'Kuwait': 'OK',
    'Kyrgyzstan': 'UO',
    'Laos': 'VL',
    'Latvia': 'EV',
    'Lebanon': 'OL',
    'Lesotho': 'FX',
    'Liberia': 'GL',
    'Libya': 'HL',
    'Lybia': 'HL',  # Common misspelling
    'Liechtenstein': 'LS',
    'Lithuania': 'EY',
    'Luxembourg': 'EL',
    'Macau': 'VM',
    'Macao': 'VM',  # Alternative spelling
    'Madagascar': 'FM',
    'Malawi': 'FW',
    'Malaysia': 'WM',
    'Maldives': 'VR',
    'Mali': 'GA',
    'Malta': 'LM',
    'Marshall Islands': 'PK',
    'Mauritania': 'GQ',
    'Mauritius': 'FI',
    'Mexico': 'MM',
    'Micronesia': 'PT',
    'Moldova': 'LU',
    'Monaco': 'LF',
    'Mongolia': 'ZM',
    'Montenegro': 'LY',
    'Morocco': 'GM',
    'Mozambique': 'FQ',
    'Myanmar (Burma)': 'VY',
    'Namibia': 'FY',
    'Nauru': 'AN',
    'Nepal': 'VN',
    'Netherlands': 'EH',
    'New Zealand': 'NZ',
    'Nicaragua': 'MN',
    'Niger': 'DR',
    'Nigeria': 'DN',
    'North Macedonia': 'LW',
    'Norway': 'EN',
    'Oman': 'OO',
    'Pakistan': 'OP',
    'Palau': 'PT',
    'Panama': 'MP',
    'Papua New Guinea': 'AY',
    'Paraguay': 'SG',
    'Peru': 'SP',
    'Philippines': 'RP',
    'Poland': 'EP',
    'Portugal': 'LP',
    'Qatar': 'OT',
    'Romania': 'LR',
    'Russia': 'UU',
    'Rwanda': 'HR',
    'Saint Kitts and Nevis': 'TK',
    'Saint Lucia': 'TL',
    'Saint Vincent and the Grenadines': 'TV',
    'Samoa': 'NS',
    'San Marino': 'LID',
    'Saudi Arabia': 'OE',
    'Serbia': 'LY',
    'Seychelles': 'FS',
    'Sierra Leone': 'GF',
    'Singapore': 'WS',
    'Slovakia': 'LZ',
    'Slovenia': 'LJ',
    'Solomon Islands': 'AG',
    'Somalia': 'HC',
    'South Africa': 'FA',
    'South Korea': 'RK',
    'South Sudan': 'HSS',
    'South Sudam': 'HSS',  # Common misspelling
    'Spain': 'LE',
    'Sri Lanka': 'VC',
    'Sudan': 'HS',
    'Suriname': 'SM',
    'Sweden': 'ES',
    'Switzerland': 'LS',
    'Syria': 'OS',
    'São Tomé and Príncipe': 'FP',
    'Taiwan': 'RC',
    'Tajikistan': 'UT',
    'Tanzania': 'HT',
    'Thailand': 'VT',
    'Togo': 'DX',
    'Tonga': 'NT',
    'Trinidad and Tobago': 'TT',
    'Tunisia': 'DT',
    'Turkey': 'LT',
    'Turkmenistan': 'UT',
    'Tuvalu': 'NG',
    'Uganda': 'HU',
    'Ukraine': 'UK',
    'United Arab Emirates': 'OM',
    'United Kingdom': 'EG',
    'United States of America': 'K',
    'USA': 'K',
    'Uruguay': 'SU',
    'Uzbekistan': 'UZ',
    'Vanuatu': 'NI',
    'Vatican City': 'LV',
    'Venezuela': 'SV',
    'Vietnam': 'VV',
    'Yemen': 'OY',
    'Zambia': 'FL',
    'Zimbabwe': 'FV',
}

# Region mapping
REGION_MAPPING = {
    'ASIA': ['Afghanistan', 'Armenia', 'Azerbaijan', 'Bahrain', 'Bangladesh', 'Bhutan', 'Brunei', 'Cambodia', 'China', 'Cyprus', 'East Timor (Timor-Leste)', 'Georgia', 'Hong Kong', 'India', 'Indonesia', 'Iran', 'Iraq', 'Israel', 'Japan', 'Jordan', 'Kazakhstan', 'Kuwait', 'Kyrgyzstan', 'Laos', 'Lebanon', 'Macau', 'Malaysia', 'Maldives', 'Mongolia', 'Myanmar (Burma)', 'Nepal', 'North Korea', 'Oman', 'Pakistan', 'Philippines', 'Qatar', 'Saudi Arabia', 'Singapore', 'South Korea', 'Sri Lanka', 'Syria', 'Taiwan', 'Tajikistan', 'Thailand', 'Turkmenistan', 'United Arab Emirates', 'Uzbekistan', 'Vietnam', 'Yemen'],
    'EUROPE': ['Albania', 'Andorra', 'Austria', 'Belarus', 'Belgium', 'Bosnia and Herzegovina', 'Bulgaria', 'Croatia', 'Czech Republic', 'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Iceland', 'Ireland', 'Italy', 'Kosovo', 'Latvia', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Malta', 'Moldova', 'Monaco', 'Montenegro', 'Netherlands', 'North Macedonia', 'Norway', 'Poland', 'Portugal', 'Romania', 'Russia', 'San Marino', 'Serbia', 'Slovakia', 'Slovenia', 'Spain', 'Sweden', 'Switzerland', 'Turkey', 'Ukraine', 'United Kingdom', 'Vatican City'],
    'AFRICA': ['Algeria', 'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi', 'Cabo Verde', 'Cameroon', 'Central African Republic', 'Chad', 'Comoros', 'Congo', 'Djibouti', 'Egypt', 'Equatorial Guinea', 'Eritrea', 'Eswatini', 'Ethiopia', 'Gabon', 'Gambia', 'Ghana', 'Guinea', 'Guinea-Bissau', 'Ivory Coast (Côte d\'Ivoire)', 'Kenya', 'Lesotho', 'Liberia', 'Libya', 'Madagascar', 'Malawi', 'Mali', 'Mauritania', 'Mauritius', 'Morocco', 'Mozambique', 'Namibia', 'Niger', 'Nigeria', 'Rwanda', 'São Tomé and Príncipe', 'Senegal', 'Seychelles', 'Sierra Leone', 'Somalia', 'South Africa', 'South Sudan', 'Sudan', 'Tanzania', 'Togo', 'Tunisia', 'Uganda', 'Zambia', 'Zimbabwe'],
    'NORTH_AMERICA': ['Antigua and Barbuda', 'Bahamas', 'Barbados', 'Belize', 'Canada', 'Costa Rica', 'Cuba', 'Dominica', 'Dominican Republic', 'El Salvador', 'Grenada', 'Guatemala', 'Haiti', 'Honduras', 'Jamaica', 'Mexico', 'Nicaragua', 'Panama', 'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines', 'Trinidad and Tobago', 'United States of America'],
    'SOUTH_AMERICA': ['Argentina', 'Bolivia', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Guyana', 'Paraguay', 'Peru', 'Suriname', 'Uruguay', 'Venezuela'],
    'OCEANIA': ['Australia', 'Fiji', 'Kiribati', 'Marshall Islands', 'Micronesia', 'Nauru', 'New Zealand', 'Palau', 'Papua New Guinea', 'Samoa', 'Solomon Islands', 'Tonga', 'Tuvalu', 'Vanuatu'],
}

def get_region(country: str) -> str:
    """Get region for a country"""
    for region, countries in REGION_MAPPING.items():
        if country in countries:
            return region
    return 'UNKNOWN'

def normalize_country_name(filename: str) -> Optional[str]:
    """Extract and normalize country name from filename or folder name"""
    # Remove common suffixes
    name = filename.replace(' AIP.pdf', '').replace(' Aip.pdf', '').replace(' AIP', '').replace(' Aip', '').replace('.pdf', '').replace('AIP-', '').replace('AIP ', '').strip()
    
    # Handle special cases
    if 'Afhanistan' in name or 'Afghanistan' in name:
        return 'Afghanistan'
    if 'Sudam' in name:
        return 'South Sudan'
    if 'Azeirbaijan' in name:
        return 'Azerbaijan'
    
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

def extract_icao_codes(text: str) -> Set[str]:
    """Extract ICAO airport codes from text"""
    codes = set()
    
    # Pattern 1: 4 uppercase letters (ICAO code pattern)
    # Make sure it's not part of a longer word
    pattern1 = r'\b([A-Z]{4})\b'
    matches = re.findall(pattern1, text)
    for match in matches:
        # Filter out common false positives
        if match not in ['PAGE', 'DATE', 'TIME', 'NOTE', 'LIST', 'AD 2', 'AD 1', 'GEN ', 'GEN1', 'GEN2', 'GEN3', 'GEN4', 'GEN5', 'GEN6', 'GEN7', 'GEN8', 'GEN9', 'ENR ', 'ENR1', 'ENR2', 'ENR3', 'ENR4', 'ENR5', 'ENR6', 'PART', 'SECT', 'TEXT', 'CONT', 'COPY', 'PAGE', 'REV ', 'REV1', 'REV2', 'REV3', 'REV4', 'REV5', 'REV6', 'REV7', 'REV8', 'REV9', 'AMDT', 'AMDT1', 'AMDT2', 'AMDT3', 'AMDT4', 'AMDT5', 'AMDT6', 'AMDT7', 'AMDT8', 'AMDT9', 'AIP ', 'AIP1', 'AIP2', 'AIP3', 'AIP4', 'AIP5', 'AIP6', 'AIP7', 'AIP8', 'AIP9', 'ICAO', 'INFO', 'DOC ', 'DOC1', 'DOC2', 'DOC3', 'DOC4', 'DOC5', 'DOC6', 'DOC7', 'DOC8', 'DOC9']:
            codes.add(match)
    
    # Pattern 2: AD 2.1 CODE or similar patterns
    pattern2 = r'AD\s*2\.\d+\s*([A-Z]{4})'
    matches = re.findall(pattern2, text, re.IGNORECASE)
    codes.update(matches)
    
    # Pattern 3: CODE — NAME pattern
    pattern3 = r'\b([A-Z]{4})\s*[—–-]\s*[A-Z]'
    matches = re.findall(pattern3, text)
    codes.update(matches)
    
    # Pattern 4: Location indicator patterns
    pattern4 = r'LOCATION\s*INDICATOR[:\s]+([A-Z]{4})'
    matches = re.findall(pattern4, text, re.IGNORECASE)
    codes.update(matches)
    
    return codes

def read_pdf_text(filepath: Path) -> str:
    """Extract text from PDF file"""
    try:
        reader = PdfReader(str(filepath))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error reading PDF {filepath}: {e}")
        return ""

def process_pdf(filepath: Path, country: Optional[str] = None) -> Set[str]:
    """Process a single PDF and extract ICAO codes"""
    logger.info(f"Processing: {filepath.name}")
    
    # If country not provided, try to extract from filename
    if not country:
        country = normalize_country_name(filepath.stem)
    
    # Extract text from PDF
    text = read_pdf_text(filepath)
    if not text:
        logger.warning(f"Could not extract text from {filepath.name}")
        return set()
    
    # Extract ICAO codes
    codes = extract_icao_codes(text)
    
    # Filter codes by country prefix if country is known
    if country and country in COUNTRY_TO_PREFIX:
        prefix = COUNTRY_TO_PREFIX[country]
        # Filter codes that start with the country's ICAO prefix
        filtered_codes = {code for code in codes if code.upper().startswith(prefix.upper())}
        if filtered_codes:
            logger.info(f"Found {len(filtered_codes)} codes for {country} in {filepath.name}")
            return filtered_codes
        else:
            # If no codes match the prefix, return all codes (might be a multi-country AIP)
            logger.warning(f"No codes found matching prefix {prefix} for {country} in {filepath.name}, returning all codes")
            return codes
    
    logger.info(f"Found {len(codes)} codes in {filepath.name}")
    return codes

def process_aip_folder(folder_path: Path) -> Dict[str, Dict[str, any]]:
    """Process all PDFs in the AIP folder"""
    results = defaultdict(lambda: {'country': '', 'region': 'UNKNOWN', 'airports': set()})
    
    # Process single PDF files in root
    for pdf_file in folder_path.glob('*.pdf'):
        country = normalize_country_name(pdf_file.stem)
        if country:
            prefix = COUNTRY_TO_PREFIX[country]
            codes = process_pdf(pdf_file, country)
            if codes:
                results[prefix]['country'] = country
                results[prefix]['region'] = get_region(country)
                results[prefix]['airports'].update(codes)
        else:
            logger.warning(f"Could not determine country for {pdf_file.name}")
            # Try to extract codes anyway and infer country from codes
            codes = process_pdf(pdf_file)
            if codes:
                # Group codes by prefix
                prefix_groups = defaultdict(set)
                for code in codes:
                    # Try to find prefix (2-3 letters)
                    for prefix_len in [3, 2, 1]:
                        prefix = code[:prefix_len]
                        if prefix in COUNTRY_TO_PREFIX.values():
                            prefix_groups[prefix].add(code)
                            break
                
                # Add to results
                for prefix, prefix_codes in prefix_groups.items():
                    # Find country for this prefix
                    country = next((c for c, p in COUNTRY_TO_PREFIX.items() if p == prefix), None)
                    if country:
                        results[prefix]['country'] = country
                        results[prefix]['region'] = get_region(country)
                        results[prefix]['airports'].update(prefix_codes)
    
    # Process country folders
    for country_folder in folder_path.iterdir():
        if country_folder.is_dir():
            country = normalize_country_name(country_folder.name)
            if not country:
                logger.warning(f"Could not determine country for folder {country_folder.name}")
                continue
            
            prefix = COUNTRY_TO_PREFIX[country]
            logger.info(f"Processing folder: {country_folder.name} ({country}, prefix: {prefix})")
            
            # Process all PDFs in this folder
            for pdf_file in country_folder.glob('*.pdf'):
                codes = process_pdf(pdf_file, country)
                if codes:
                    results[prefix]['country'] = country
                    results[prefix]['region'] = get_region(country)
                    results[prefix]['airports'].update(codes)
    
    # Convert sets to sorted lists
    output = {}
    for prefix, data in results.items():
        if data['airports']:
            output[prefix] = {
                'country': data['country'],
                'region': data['region'],
                'airports': sorted(list(data['airports']))
            }
    
    return output

def update_airport_codes_json(extracted_codes: Dict[str, Dict[str, any]], output_path: Path):
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
            existing_codes[prefix] = data
    
    # Update metadata
    from datetime import datetime
    existing_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    existing_data['codes'] = existing_codes
    
    # Write updated data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Updated {output_path} with {len(existing_codes)} country prefixes")

def main():
    """Main function"""
    aip_folder = Path('AIP\'s')
    output_file = Path('assets/airport_codes.json')
    
    if not aip_folder.exists():
        logger.error(f"AIP folder not found: {aip_folder}")
        return
    
    logger.info(f"Processing PDFs in {aip_folder}")
    extracted_codes = process_aip_folder(aip_folder)
    
    logger.info(f"Extracted codes for {len(extracted_codes)} countries")
    for prefix, data in extracted_codes.items():
        logger.info(f"  {prefix} ({data['country']}): {len(data['airports'])} airports")
    
    # Update airport_codes.json
    update_airport_codes_json(extracted_codes, output_file)
    logger.info("Done!")

if __name__ == '__main__':
    main()

