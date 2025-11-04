#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class KosovoAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://www.ashna-ks.org/eAIP/AIRAC AMDT 01-2025_2025_10_30\index.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = KosovoAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
