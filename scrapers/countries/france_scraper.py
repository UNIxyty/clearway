#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class FranceAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://aip.aero/fr/en/")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = FranceAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
