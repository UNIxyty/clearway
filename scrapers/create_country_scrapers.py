#!/usr/bin/env python3
"""
Generate per-country scraper stubs for Web Table Based countries.
Reads a JSON report produced by web_table_based_scraper.py (use --out-json),
and creates one file per country that plugs its resolved indexUrl into BaseEAIPScraperPlaywright.
"""
import json
import re
from pathlib import Path

TEMPLATE = """#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class {class_name}(BaseEAIPScraperPlaywright):
\tdef __init__(self, headless: bool = True):
\t\tsuper().__init__(index_url="{index_url}")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
\tscraper = {class_name}(headless=headless)
\treturn scraper.get_airport_info(airport_code, headless=headless)
"""


def _classify(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9]+", " ", name).strip()
    parts = [p.capitalize() for p in name.split() if p]
    return "".join(parts) + "AIPScraper"


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Create per-country scraper stubs')
    parser.add_argument('--report-json', required=True, help='JSON from web_table_based_scraper --out-json')
    parser.add_argument('--out-dir', default=str(Path(__file__).resolve().parent / 'countries'))
    args = parser.parse_args()

    report = json.loads(Path(args.report_json).read_text(encoding='utf-8'))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    for row in report:
        country = row.get('country') or ''
        index_url = row.get('indexUrl') or ''
        base_url = row.get('baseUrl') or ''
        if not base_url:
            # skip failures
            continue
        class_name = _classify(country)
        filename = re.sub(r"[^A-Za-z0-9]+", "_", country).lower() + "_scraper.py"
        content = TEMPLATE.format(class_name=class_name, index_url=index_url if index_url else base_url)
        (out_dir / filename).write_text(content, encoding='utf-8')
        created += 1

    print(f"Created {created} country scraper stubs at {out_dir}")


if __name__ == '__main__':
    main()


