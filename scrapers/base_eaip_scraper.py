#!/usr/bin/env python3
import logging
import re
import time
from typing import Dict, List

from playwright.sync_api import sync_playwright, Page

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BaseEAIPScraperPlaywright:
    """Generic eAIP scraper for Web Table Based countries (Eurocontrol-style).
    Implements navigation via frames: Part 3 -> AERODROMES -> AD 2 -> airport code.
    """

    def __init__(self, index_url: str):
        self.index_url = index_url.rstrip('/')
        self.playwright = None
        self.browser = None
        self.page: Page | None = None

    def _setup(self, headless: bool = True):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless, args=['--window-size=1600,1000'])
        self.page = self.browser.new_page()
        self.page.set_default_timeout(30000)

    def _teardown(self):
        try:
            if self.browser:
                self.browser.close()
        finally:
            if self.playwright:
                self.playwright.stop()

    def _open_index(self):
        assert self.page is not None
        logger.info(f"Opening eAIP index: {self.index_url}")
        self.page.goto(self.index_url, wait_until="domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle")
        except Exception:
            time.sleep(2)

    def _navigate_to_airport(self, airport_code: str):
        assert self.page is not None
        airport_code = airport_code.upper().strip()
        # Try to find a navigation frame and click through
        nav_frame = None
        for frame in self.page.frames:
            name = (frame.name or '').lower()
            if 'navigation' in name or 'eaisnavigation' in name or 'toc' in name:
                nav_frame = frame
                break

        if not nav_frame:
            # Single-page variants: try direct anchor search
            logger.info("Navigation frame not found, trying direct anchor search on page")
            try:
                locator = self.page.locator(f"//a[contains(., '{airport_code}')] ").first
                if locator and locator.is_visible():
                    locator.click()
                    time.sleep(1.5)
                    return
            except Exception:
                pass
            raise Exception("Navigation frame not found and direct anchor search failed")

        try:
            nav_frame.wait_for_load_state("networkidle")
        except Exception:
            time.sleep(1)

        try:
            # Expand Part 3
            link = nav_frame.locator("//a[contains(., 'Part 3') or contains(., 'PART 3')]").first
            if link and link.is_visible():
                link.click(); time.sleep(0.5)
        except Exception:
            pass

        try:
            # Click AERODROMES
            link = nav_frame.locator("//a[contains(., 'AERODROMES') or contains(., 'Aerodromes')]").first
            if link and link.is_visible():
                link.click(); time.sleep(0.5)
        except Exception:
            pass

        # Click airport code in nav
        airport_link = nav_frame.locator(f"//a[contains(., '{airport_code}')]").first
        if airport_link and airport_link.is_visible():
            airport_link.click(); time.sleep(1.5)
            return

        raise Exception(f"Airport code {airport_code} not found in navigation")

    def _content_text(self) -> str:
        assert self.page is not None
        # Prefer content frame
        for frame in self.page.frames:
            name = (frame.name or '').lower()
            if 'content' in name or 'eaiscontent' in name:
                try:
                    return frame.text_content('body') or ''
                except Exception:
                    break
        return self.page.text_content('body') or ''

    def _parse_operational_hours(self, text: str) -> List[Dict]:
        results: List[Dict] = []
        upper = text.upper()
        start_idx = upper.find('AD 2.3 OPERATIONAL HOURS')
        if start_idx == -1:
            start_idx = upper.find('OPERATIONAL HOURS')
        end_idx = upper.find('AD 2.4') if start_idx != -1 else -1
        segment = text[start_idx:end_idx] if start_idx != -1 and end_idx != -1 else text

        def add(field: str, value: str):
            results.append({"day": field, "hours": value})

        def find(patterns: List[str], field: str) -> bool:
            for p in patterns:
                m = re.search(p, segment, re.IGNORECASE | re.DOTALL)
                if m:
                    hours = "H24" if 'H24' in m.group(0).upper() else (m.group(1) if m.lastindex else 'NIL')
                    add(field, hours if hours else 'NIL')
                    return True
            return False

        found_admin = find([r'(?:^|\s)AD\s+Administration.*?(H24|NIL)'], 'AD Administration')
        found_operator = find([r'(?:^|\s)AD\s+Operator.*?(H24|NIL)', r'1AD.*?(H24|NIL)'], 'AD Operator')

        cm = re.search(r'Customs.*?immigration.*?(H24|NIL|May be requested)', segment, re.IGNORECASE | re.DOTALL)
        if cm:
            add('Customs and immigration', 'On request' if 'May be requested' in cm.group(1) else ('H24' if 'H24' in cm.group(1).upper() else 'NIL'))
        else:
            add('Customs and immigration', 'NIL')

        am = re.search(r'(?<!Reporting )(?<!MET\s)ATS(?![A-Z]).*?(H24|NIL)', segment, re.IGNORECASE | re.DOTALL)
        if am:
            add('ATS', 'H24' if 'H24' in am.group(1).upper() else 'NIL')
        else:
            add('ATS', 'NIL')

        if not found_admin:
            add('AD Administration', 'NIL')
        if not found_operator:
            add('AD Operator', 'NIL')
        return results

    def _get_field_value(self, operational_hours: List[Dict], field_name: str) -> str:
        for hour in operational_hours:
            if hour.get('day') == field_name:
                return hour.get('hours', 'NIL')
        return 'NIL'

    def _extract_airport_name(self, text: str, airport_code: str) -> str:
        try:
            upper = text.upper()
            start_idx = upper.find('AERODROME LOCATION INDICATOR AND NAME')
            if start_idx == -1:
                start_idx = upper.find('AD 2.1')
            if start_idx != -1:
                end_idx = upper.find('AD 2.2', start_idx)
                if end_idx == -1:
                    end_idx = start_idx + 600
                section = text[start_idx:end_idx]
                code_upper = airport_code.upper()
                m = re.search(rf"{re.escape(code_upper)}\s*[—–-]\s*(.+?)(?=\s*{re.escape(code_upper)}|$)", section, re.IGNORECASE)
                if m:
                    name = re.sub(r'\s+', ' ', m.group(1)).strip()
                    name = re.sub(r'\s*AD\s*2\.\d+.*$', '', name, flags=re.IGNORECASE)
                    name = name.rstrip(' /').strip()
                    return f"{code_upper} — {name}"
            return airport_code.upper()
        except Exception:
            return airport_code.upper()

    def _extract_remarks(self, text: str) -> str:
        try:
            upper = text.upper()
            ad23_idx = upper.find('AD 2.3')
            if ad23_idx != -1:
                ad22_idx = upper.rfind('AD 2.2', 0, ad23_idx)
                if ad22_idx != -1:
                    remarks_idx = upper.find('REMARKS', ad22_idx, ad23_idx)
                    if remarks_idx != -1:
                        remarks_text = text[remarks_idx:min(ad23_idx, remarks_idx + 500)]
                        remarks_text = re.sub(r'^REMARKS[:\s]*', '', remarks_text, flags=re.IGNORECASE)
                        remarks_text = re.sub(r'AD\s+2\.3.*$', '', remarks_text, flags=re.IGNORECASE | re.DOTALL)
                        remarks_text = re.sub(r'\s+', ' ', remarks_text.strip())
                        if len(remarks_text) > 5:
                            return remarks_text[:200]
            return 'NIL'
        except Exception:
            return 'NIL'

    def _extract_traffic_types(self, text: str) -> str:
        try:
            upper = text.upper()
            start_idx = upper.find('AD 2.2')
            if start_idx == -1:
                start_idx = upper.find('AERODROME GEOGRAPHICAL')
            if start_idx != -1:
                end_idx = upper.find('AD 2.3', start_idx)
                if end_idx == -1:
                    end_idx = start_idx + 2000
                section = text[start_idx:end_idx]
                for pattern in [r'Types?\s+of\s+traffic.*?(IFR[/, ]VFR|VFR[/, ]IFR|IFR|VFR)', r'Traffic.*?(IFR[/, ]VFR|VFR[/, ]IFR|IFR|VFR)', r'(IFR/VFR|VFR/IFR)']:
                    m = re.search(pattern, section, re.IGNORECASE)
                    if m:
                        return m.group(1)
            return 'Not specified'
        except Exception:
            return 'Not specified'

    def get_airport_info(self, airport_code: str, headless: bool = True) -> Dict:
        self._setup(headless=headless)
        try:
            self._open_index()
            self._navigate_to_airport(airport_code)
            text = self._content_text()
            hours = self._parse_operational_hours(text)
            return {
                'airportCode': airport_code.upper(),
                'airportName': self._extract_airport_name(text, airport_code),
                'adAdministration': self._get_field_value(hours, 'AD Administration'),
                'adOperator': self._get_field_value(hours, 'AD Operator'),
                'customsAndImmigration': self._get_field_value(hours, 'Customs and immigration'),
                'ats': self._get_field_value(hours, 'ATS'),
                'operationalRemarks': self._extract_remarks(text),
                'trafficTypes': self._extract_traffic_types(text),
            }
        finally:
            self._teardown()


