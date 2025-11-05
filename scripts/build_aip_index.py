"""
Build comprehensive index of AIP PDFs with page numbers for each section
This allows fast, accurate extraction
"""

import json
import re
import PyPDF2
from pathlib import Path
from typing import Dict, List, Tuple

def analyze_pdf(pdf_path: Path) -> Dict:
    """Analyze a single PDF and build index of airports and sections"""

    print(f"\n{'='*80}")
    print(f"Analyzing: {pdf_path.name}")
    print(f"{'='*80}")

    result = {
        'filename': pdf_path.name,
        'country': pdf_path.stem.replace('_aip', '').replace('_', ' ').title(),
        'airports': {}
    }

    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            print(f"Total pages: {total_pages}")

            # Scan all pages
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()

                # Look for airport codes (4-letter ICAO codes)
                airport_codes = re.findall(r'\b([A-Z]{2}[A-Z]{2})\b', text)

                # Look for section markers
                has_ad_22 = bool(re.search(r'AD\s*2\.2', text, re.IGNORECASE))
                has_ad_23 = bool(re.search(r'AD\s*2\.3', text, re.IGNORECASE))
                has_ad_26 = bool(re.search(r'AD\s*2\.6', text, re.IGNORECASE))

                # Look for operational hours keywords
                has_operational_hours = bool(re.search(r'OPERATIONAL\s+HOURS', text, re.IGNORECASE))

                # Look for specific content
                has_ad_administration = bool(re.search(r'AD\s+Administration', text, re.IGNORECASE))
                has_customs = bool(re.search(r'Customs\s+(?:and\s+)?Immigration', text, re.IGNORECASE))
                has_ats = bool(re.search(r'\bATS\b', text, re.IGNORECASE))
                has_traffic_types = bool(re.search(r'[Tt]ypes?\s+of\s+traffic', text, re.IGNORECASE))
                has_fire_fighting = bool(re.search(r'[Ff]ire\s+[Ff]ighting|[Rr]escue', text, re.IGNORECASE))

                # For each airport code found on this page
                for code in set(airport_codes):
                    # Filter out common false positives
                    if code in ['ICAO', 'CODE', 'TYPE', 'DATA', 'INTL', 'PAGE', 'AMDT', 'INFO']:
                        continue

                    # Check if this code appears with airport name format
                    code_pattern = rf'{code}\s*[—\-]'
                    has_airport_header = bool(re.search(code_pattern, text))

                    if code not in result['airports']:
                        result['airports'][code] = {
                            'pages_found': [],
                            'ad_22_pages': [],
                            'ad_23_pages': [],
                            'ad_26_pages': [],
                            'first_page': page_num + 1,
                            'has_header': has_airport_header
                        }

                    result['airports'][code]['pages_found'].append(page_num + 1)

                    if has_ad_22:
                        result['airports'][code]['ad_22_pages'].append(page_num + 1)
                    if has_ad_23 or has_operational_hours:
                        result['airports'][code]['ad_23_pages'].append(page_num + 1)
                    if has_ad_26 or has_fire_fighting:
                        result['airports'][code]['ad_26_pages'].append(page_num + 1)

            # Filter airports - keep only those with multiple pages or section markers
            filtered_airports = {}
            for code, data in result['airports'].items():
                # Keep if: appears on multiple pages OR has section markers OR has airport header
                if (len(data['pages_found']) >= 2 or
                    data['ad_22_pages'] or
                    data['ad_23_pages'] or
                    data['ad_26_pages'] or
                    data['has_header']):
                    filtered_airports[code] = data
                    print(f"  ✓ {code}: Found on pages {data['pages_found'][:5]}" +
                          (f"... (+{len(data['pages_found'])-5} more)" if len(data['pages_found']) > 5 else ""))
                    if data['ad_23_pages']:
                        print(f"    → AD 2.3 (Operational Hours) on pages: {data['ad_23_pages'][:3]}")

            result['airports'] = filtered_airports
            print(f"\nFound {len(filtered_airports)} valid airports")

    except Exception as e:
        print(f"Error analyzing {pdf_path.name}: {e}")
        result['error'] = str(e)

    return result

def build_index():
    """Build index for all AIP PDFs"""
    aips_dir = Path(__file__).parent.parent / "AIP's"
    pdf_files = sorted(aips_dir.glob("*.pdf"))

    print(f"\n{'='*80}")
    print(f"BUILDING AIP INDEX")
    print(f"{'='*80}")
    print(f"Found {len(pdf_files)} PDF files\n")

    index = {
        'description': 'AIP PDF Index with page numbers for fast extraction',
        'last_updated': '2025-11-05',
        'pdfs': {}
    }

    for pdf_file in pdf_files:
        result = analyze_pdf(pdf_file)
        if result['airports']:
            index['pdfs'][pdf_file.stem] = result

    # Save index
    index_path = Path(__file__).parent.parent / "assets" / "aip_index.json"
    index_path.parent.mkdir(exist_ok=True)

    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"INDEX SAVED")
    print(f"{'='*80}")
    print(f"Location: {index_path}")
    print(f"Total PDFs indexed: {len(index['pdfs'])}")

    total_airports = sum(len(data['airports']) for data in index['pdfs'].values())
    print(f"Total airports found: {total_airports}")

    return index

if __name__ == "__main__":
    index = build_index()
