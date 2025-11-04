#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class ThailandAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://aip.caat.or.th/2025-10-30-AIRAC/html/index-en-GB.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = ThailandAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
