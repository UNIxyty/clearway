"""
Update airport_codes.json with codes extracted from AIP PDFs
"""

import json
import os
from pathlib import Path
from aip_pdf_extractor import AIPPDFExtractor


# Country name mappings
COUNTRY_MAPPINGS = {
    'Malta': {'prefix': 'LM', 'region': 'EUROPE'},
    'Afghanistan': {'prefix': 'OA', 'region': 'ASIA'},
    'Seychelles': {'prefix': 'FS', 'region': 'AFRICA'},
    'South Africa': {'prefix': 'FA', 'region': 'AFRICA'},
    'Sudan': {'prefix': 'HS', 'region': 'AFRICA'},
    'Djibouti': {'prefix': 'HD', 'region': 'AFRICA'},
    'Andorra': {'prefix': 'LE', 'region': 'EUROPE'},
    'Angola': {'prefix': 'FN', 'region': 'AFRICA'},
    'Ethiopia': {'prefix': 'HA', 'region': 'AFRICA'},
    'Greece': {'prefix': 'LG', 'region': 'EUROPE'},
    'Haiti': {'prefix': 'MT', 'region': 'NORTH_AMERICA'},
    'Macao': {'prefix': 'VM', 'region': 'ASIA'},
    'Antigua And Barbuda': {'prefix': 'TAPA', 'region': 'NORTH_AMERICA'},
    'Saint Vincent And The Grenadines': {'prefix': 'TV', 'region': 'CARIBBEAN'},
    'Trinidad And Tobago': {'prefix': 'TT', 'region': 'NORTH_AMERICA'},
    'Timor': {'prefix': 'WP', 'region': 'ASIA'},
    'Libya': {'prefix': 'HL', 'region': 'AFRICA'},
    'Austria': {'prefix': 'LO', 'region': 'EUROPE'},
    'Azerbaijan': {'prefix': 'UB', 'region': 'ASIA'},
    'Bhutan': {'prefix': 'VQ', 'region': 'ASIA'},
    'Bulgaria': {'prefix': 'LZ', 'region': 'EUROPE'},
    'Cuba': {'prefix': 'MU', 'region': 'NORTH_AMERICA'},
    'Czech Republic': {'prefix': 'LK', 'region': 'EUROPE'},
    'Denmark': {'prefix': 'EK', 'region': 'EUROPE'},
    'Iran': {'prefix': 'OI', 'region': 'ASIA'},
    'Ireland': {'prefix': 'EI', 'region': 'EUROPE'},
    'Italy': {'prefix': 'LI', 'region': 'EUROPE'},
    'Japan': {'prefix': 'RJ', 'region': 'ASIA'},
    'Maldives': {'prefix': 'VR', 'region': 'ASIA'},
    'Nepal': {'prefix': 'VN', 'region': 'ASIA'},
}


def load_airport_codes():
    """Load existing airport_codes.json"""
    codes_path = Path("/Users/whae/Downloads/Clearway/assets/airport_codes.json")
    with open(codes_path, 'r') as f:
        return json.load(f)


def save_airport_codes(codes):
    """Save updated airport_codes.json"""
    codes_path = Path("/Users/whae/Downloads/Clearway/assets/airport_codes.json")
    with open(codes_path, 'w') as f:
        json.dump(codes, f, indent=2)
    print(f"✓ Updated: {codes_path}")


def extract_all_codes():
    """Extract airport codes from all AIP PDFs"""
    aips_dir = Path("/Users/whae/Downloads/Clearway/AIP's")

    extracted_data = {}

    for pdf_file in aips_dir.glob("*.pdf"):
        print(f"\n📄 Processing: {pdf_file.name}")
        extractor = AIPPDFExtractor(str(pdf_file))

        # Extract codes
        codes = extractor.extract_airport_codes()
        country_name = extractor.country_name

        if codes:
            print(f"  ✓ Found {len(codes)} codes: {', '.join(codes)}")
            extracted_data[country_name] = codes
        else:
            print(f"  ⚠ No codes found")

    return extracted_data


def update_codes_file():
    """Update the airport_codes.json file with extracted codes"""
    print("=" * 60)
    print("UPDATING AIRPORT CODES FROM AIP PDFs")
    print("=" * 60)

    # Load existing codes
    existing_codes = load_airport_codes()
    print(f"\n📚 Loaded existing codes: {len(existing_codes['codes'])} countries")

    # Extract codes from PDFs
    extracted_data = extract_all_codes()

    # Update the codes structure
    updated_count = 0
    added_count = 0

    for country_name, codes in extracted_data.items():
        if not codes:
            continue

        # Find or create country mapping
        if country_name in COUNTRY_MAPPINGS:
            prefix = COUNTRY_MAPPINGS[country_name]['prefix']
            region = COUNTRY_MAPPINGS[country_name]['region']
        else:
            # Try to infer prefix from first code
            prefix = codes[0][:2] if codes else 'XX'
            region = 'UNKNOWN'
            print(f"\n⚠ No mapping for '{country_name}', using prefix: {prefix}")

        # Update or add to codes
        if prefix in existing_codes['codes']:
            old_codes = set(existing_codes['codes'][prefix]['airports'])
            new_codes = set(codes)
            combined = sorted(list(old_codes | new_codes))

            if len(combined) > len(old_codes):
                print(f"  ✓ Updated {country_name}: {len(old_codes)} -> {len(combined)} codes")
                updated_count += 1

            existing_codes['codes'][prefix]['airports'] = combined
        else:
            print(f"  + Added {country_name} with {len(codes)} codes")
            existing_codes['codes'][prefix] = {
                'country': country_name,
                'region': region,
                'airports': sorted(codes)
            }
            added_count += 1

    # Update timestamp
    from datetime import datetime
    existing_codes['last_updated'] = datetime.now().strftime('%Y-%m-%d')

    # Save updated codes
    save_airport_codes(existing_codes)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✓ Processed: {len(extracted_data)} PDF files")
    print(f"✓ Updated: {updated_count} countries")
    print(f"✓ Added: {added_count} new countries")
    print(f"✓ Total countries: {len(existing_codes['codes'])}")
    print("=" * 60)


if __name__ == "__main__":
    update_codes_file()
