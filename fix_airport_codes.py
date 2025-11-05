#!/usr/bin/env python3
"""
Fix airport codes:
1. France - keep only valid LF** codes
2. Japan - ensure all RJ** and RO** codes are included
"""

import json
from pathlib import Path

# Load the airport codes
json_path = Path('assets/airport_codes.json')
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Fix France - keep only LF** codes
if 'LF' in data['codes']:
    existing_airports = set(data['codes']['LF']['airports'])
    # Only keep codes that start with LF and are 4 characters
    valid_france = {code for code in existing_airports if code.startswith('LF') and len(code) == 4}
    data['codes']['LF']['airports'] = sorted(list(valid_france))
    print(f"France: Filtered from {len(existing_airports)} to {len(valid_france)} valid codes")

# Fix Japan - ensure all RJ** and RO** codes from PDFs are included
japan_pdf_dir = Path("AIP's/Japan")
actual_japan_codes = set()

if japan_pdf_dir.exists():
    for pdf_file in japan_pdf_dir.glob('*.pdf'):
        code = pdf_file.stem.replace('_full', '').replace('.pdf', '').upper()
        if len(code) == 4 and (code.startswith('RJ') or code.startswith('RO')):
            actual_japan_codes.add(code)

print(f"Found {len(actual_japan_codes)} actual Japan airport codes from PDFs")

if 'RJ' in data['codes']:
    existing_airports = set(data['codes']['RJ']['airports'])
    # Filter to only include codes that start with RJ or RO
    valid_japan = {code for code in existing_airports if (code.startswith('RJ') or code.startswith('RO')) and len(code) == 4}
    # Merge with actual codes from PDFs
    valid_japan.update(actual_japan_codes)
    data['codes']['RJ']['airports'] = sorted(list(valid_japan))
    print(f"Japan: Updated to {len(valid_japan)} valid codes")
    print(f"Sample codes: {sorted(list(valid_japan))[:10]}")

# Save the updated JSON
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Updated {json_path}")

