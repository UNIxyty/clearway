#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class CaboVerdeAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://eaip.asa.cv/2024-04-18-AIRAC/html/index-en-GB.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = CaboVerdeAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
