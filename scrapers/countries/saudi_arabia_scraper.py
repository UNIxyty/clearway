#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class SaudiArabiaAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://aimss.sans.com.sa/assets/FileManagerFiles/AIRAC AIP AMDT 05_24_2024_05_16/index.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = SaudiArabiaAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
