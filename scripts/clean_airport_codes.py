"""
Clean airport_codes.json by removing false positive codes
that don't match the expected ICAO prefix for each country
"""

import json
from pathlib import Path

def clean_airport_codes():
    """Remove false positive airport codes"""
    codes_path = Path(__file__).parent.parent / "assets" / "airport_codes.json"

    with open(codes_path, 'r') as f:
        data = json.load(f)

    total_removed = 0

    for prefix, country_data in data['codes'].items():
        airports = country_data['airports']
        original_count = len(airports)

        # Filter: keep only codes that start with the expected prefix
        if len(prefix) == 2:
            # Two-letter prefix: codes should start with these 2 letters
            cleaned = [code for code in airports if code.startswith(prefix)]
        elif len(prefix) == 1:
            # One-letter prefix (like 'K' for USA)
            cleaned = [code for code in airports if code.startswith(prefix)]
        else:
            # Special cases like 'TAPA'
            cleaned = [code for code in airports if code.startswith(prefix[:2])]

        removed_count = original_count - len(cleaned)
        if removed_count > 0:
            print(f"✓ {country_data['country']}: Removed {removed_count} false positives ({original_count} -> {len(cleaned)})")
            removed_codes = set(airports) - set(cleaned)
            print(f"  Removed: {', '.join(list(removed_codes)[:10])}")
            total_removed += removed_count
            country_data['airports'] = sorted(cleaned)

    # Save cleaned data
    with open(codes_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✓ Total false positives removed: {total_removed}")
    print(f"✓ Cleaned airport_codes.json saved")

if __name__ == "__main__":
    clean_airport_codes()
