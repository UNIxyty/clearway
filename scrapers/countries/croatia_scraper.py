#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class CroatiaAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://www.crocontrol.hr/UserDocsImages/AIS%20produkti/eAIP/2025-10-30-AIRAC\html\index-en-HR.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = CroatiaAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
