#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class AlbaniaAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://www.albcontrol.al/al/aip/AIRAC%20AMDT%20004_2025/30-OCT-2025-A/2025-10-30-AIRAC/html%20")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = AlbaniaAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
