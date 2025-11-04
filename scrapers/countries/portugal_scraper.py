#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class PortugalAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://ais.nav.pt/wp-content/uploads/AIS_Files/eAIP_Current/eAIP_Online/eAIP/html/index.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = PortugalAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
