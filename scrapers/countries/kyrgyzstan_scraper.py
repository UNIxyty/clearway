#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class KyrgyzstanAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="http://kan.kg/ais/eaip/2025-10-30-AIRAC/html/index_commands.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = KyrgyzstanAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
