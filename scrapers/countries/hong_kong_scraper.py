#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class HongKongAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://www.ais.gov.hk/eaip_20251030/2025-10-30-000000/html/index-en-US.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = HongKongAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
