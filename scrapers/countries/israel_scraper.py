#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class IsraelAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://e-aip.azurefd.net/2025-10-02-AIRAC/html/index.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = IsraelAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
