#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class MalaysiaAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://aip.caam.gov.my/aip/eAIP/2025-09-09/html/index-en-MS.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = MalaysiaAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
