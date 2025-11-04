#!/usr/bin/env python3
import json
import logging
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from playwright.sync_api import sync_playwright, Page

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _to_absolute_url(base: str, href: str) -> str:
    if not href:
        return ''
    if href.startswith('http://') or href.startswith('https://'):
        return href
    if href.startswith('/'):
        # Extract scheme+host from base
        m = re.match(r'^(https?://[^/]+)', base)
        if m:
            return m.group(1) + href
        return href
    # relative path
    if base.endswith('/'):
        return base + href
    return base.rsplit('/', 1)[0] + '/' + href


def _extract_first_href_from_html_snippet(snippet_html: str) -> Optional[str]:
    if not snippet_html:
        return None
    m = re.search(r'href\s*=\s*"([^"]+)"', snippet_html)
    if not m:
        m = re.search(r"href\s*=\s*'([^']+)'", snippet_html)
    return m.group(1) if m else None


def _best_effort_find_current_issue_href(page: Page, snippet_html: str) -> Optional[str]:
    # 1) If snippet already contains an href, prefer that path shape to find a matching anchor on live page
    hinted_href = _extract_first_href_from_html_snippet(snippet_html)
    if hinted_href:
        last_segment = hinted_href.split('/')[-1]
        if last_segment:
            try:
                loc = page.locator(f"a[href*='{last_segment}']").first
                if loc and loc.count() > 0 and loc.is_visible():
                    href = loc.get_attribute('href')
                    if href:
                        return href
            except Exception:
                pass
        # Fallback: any anchor that contains a substantial piece of the hinted href
        key = None
        # choose a mid path token likely stable like 'AIRAC' or date fragment
        for token in ['AIRAC', '2025', '2024', 'index', 'html', 'AIP', 'eAIP']:
            if token in hinted_href:
                key = token
                break
        if key:
            try:
                loc = page.locator(f"a[href*='{key}']")
                if loc and loc.count() > 0:
                    for i in range(min(10, loc.count())):
                        href = loc.nth(i).get_attribute('href')
                        if href and ('html' in href or 'index' in href or 'eAIP' in href):
                            return href
            except Exception:
                pass

    # 2) Generic heuristics by common AIP platforms
    # Look for links that clearly point to current issue roots
    candidates: List[str] = []
    try:
        anchors = page.locator('a').all()
        for a in anchors[:500]:
            try:
                t = (a.text_content() or '').strip().upper()
                h = a.get_attribute('href') or ''
                if not h:
                    continue
                if any(k in h for k in ['AIP', 'EAIP', 'AIRAC']):
                    candidates.append(h)
                elif any(k in t for k in ['CURRENT', 'AIRAC', 'ISSUE', 'AIP']):
                    candidates.append(h)
            except Exception:
                continue
    except Exception:
        pass

    # Prefer ones that end with index*.html
    for h in candidates:
        if re.search(r'index.*\.html$', h):
            return h
    # Else any html
    for h in candidates:
        if h.endswith('.html'):
            return h
    # Else first candidate
    return candidates[0] if candidates else None


def _resolve_base_dir_from_index(href: str) -> Tuple[str, str]:
    # Returns (index_url, base_dir_url)
    if not href:
        return '', ''
    # Normalize common patterns to a base directory
    if href.endswith('.html'):
        base = href.rsplit('/', 1)[0]
        return href, base
    return href, href.rstrip('/')


class WebTableAIPResolver:
    def __init__(self, headless: bool = True):
        self.playwright = None
        self.browser = None
        self.page = None
        self.headless = headless

    def _setup(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless, args=['--window-size=1600,1000'])
        self.page = self.browser.new_page()
        self.page.set_default_timeout(30000)

    def _teardown(self):
        try:
            if self.browser:
                self.browser.close()
        finally:
            if self.playwright:
                self.playwright.stop()

    def resolve_country(self, link: str, snippet_html: str) -> Dict[str, str]:
        result = {"indexUrl": "", "baseUrl": ""}
        logger.info(f"Opening: {link}")
        self.page.goto(link, wait_until="domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle")
        except Exception:
            time.sleep(2)

        href = _best_effort_find_current_issue_href(self.page, snippet_html)
        if not href:
            logger.warning("Could not detect current issue href via heuristics")
            return result

        abs_href = _to_absolute_url(self.page.url, href)
        index_url, base_url = _resolve_base_dir_from_index(abs_href)
        result["indexUrl"] = index_url
        result["baseUrl"] = base_url
        logger.info(f"Resolved index: {index_url}")
        logger.info(f"Resolved base:  {base_url}")
        return result

    def run(self, json_path: Path) -> List[Dict[str, str]]:
        data = json.loads(json_path.read_text(encoding='utf-8'))
        results: List[Dict[str, str]] = []
        try:
            self._setup()
            for entry in data:
                try:
                    if (entry.get('type') or '').strip().lower() != 'web table based':
                        continue
                    country = entry.get('country') or ''
                    link = entry.get('link') or ''
                    snippet = entry.get('Effective Date Button Div') or ''
                    if not link:
                        logger.info(f"Skipping {country}: empty link")
                        continue
                    logger.info(f"Resolving {country}")
                    resolved = self.resolve_country(link, snippet)
                    results.append({
                        'country': country,
                        'link': link,
                        'indexUrl': resolved.get('indexUrl', ''),
                        'baseUrl': resolved.get('baseUrl', ''),
                    })
                except Exception as e:
                    logger.warning(f"Failed to resolve {entry.get('country')}: {e}")
                    results.append({
                        'country': entry.get('country') or '',
                        'link': entry.get('link') or '',
                        'indexUrl': '',
                        'baseUrl': '',
                        'error': str(e),
                    })
        finally:
            self._teardown()
        return results


def _save_json(path: Path, results: List[Dict[str, str]]):
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    logger.info(f"Saved JSON report to {path}")


def _save_csv(path: Path, results: List[Dict[str, str]]):
    import csv
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['country', 'link', 'indexUrl', 'baseUrl', 'error'])
        for r in results:
            writer.writerow([
                r.get('country', ''),
                r.get('link', ''),
                r.get('indexUrl', ''),
                r.get('baseUrl', ''),
                r.get('error', ''),
            ])
    logger.info(f"Saved CSV report to {path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Resolve current eAIP index/base URLs for Web Table Based countries')
    parser.add_argument('--aip-json', default=str(Path(__file__).resolve().parents[1] / 'assets' / 'aip_countries_full.json'))
    parser.add_argument('--out-json', default='')
    parser.add_argument('--out-csv', default='')
    parser.add_argument('--headful', action='store_true', help='Run non-headless for debugging')
    args = parser.parse_args()

    json_path = Path(args.aip_json)
    resolver = WebTableAIPResolver(headless=not args.headful)
    results = resolver.run(json_path)

    # Summary
    successes = [r for r in results if r.get('baseUrl')]
    failures = [r for r in results if not r.get('baseUrl')]
    print(f"Resolved: {len(successes)} succeeded, {len(failures)} failed")
    if failures:
        print("Failed countries:")
        for r in failures:
            print(f"- {r.get('country','')} ({r.get('link','')}) {r.get('error','')}")

    # Detailed list
    for r in successes:
        country = r.get('country', '')
        base = r.get('baseUrl', '')
        index_url = r.get('indexUrl', '')
        print(f"{country}: base={base} index={index_url}")

    if args.out_json:
        _save_json(Path(args.out_json), results)
    if args.out_csv:
        _save_csv(Path(args.out_csv), results)


if __name__ == '__main__':
    main()


