#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class SwedenAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://aro.lfv.se/content/eaip/AIRAC AIP AMDT 6-2025_2025_10_30\index-v2.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = SwedenAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
