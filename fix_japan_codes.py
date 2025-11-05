#!/usr/bin/env python3
"""
Fix Japan airport codes in airport_codes.json
Remove false positives and keep only actual ICAO codes (RJ** and RO**)
"""

import json
from pathlib import Path

# Load the airport codes
json_path = Path('assets/airport_codes.json')
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get actual Japan airport codes from PDF filenames
japan_pdf_dir = Path("AIP's/Japan")
actual_codes = set()

if japan_pdf_dir.exists():
    for pdf_file in japan_pdf_dir.glob('*.pdf'):
        code = pdf_file.stem.replace('_full', '').replace('.pdf', '').upper()
        if len(code) == 4 and (code.startswith('RJ') or code.startswith('RO')):
            actual_codes.add(code)

print(f"Found {len(actual_codes)} actual Japan airport codes from PDFs")

# Update the RJ entry
if 'RJ' in data['codes']:
    # Filter to only include codes that start with RJ or RO
    existing_airports = set(data['codes']['RJ']['airports'])
    valid_codes = {code for code in existing_airports if code.startswith('RJ') or code.startswith('RO')}
    
    # Merge with actual codes from PDFs
    valid_codes.update(actual_codes)
    
    data['codes']['RJ']['airports'] = sorted(list(valid_codes))
    print(f"Updated Japan airports: {len(data['codes']['RJ']['airports'])} codes")
    print(f"Sample codes: {sorted(list(valid_codes))[:10]}")

# Save the updated JSON
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Updated {json_path}")

