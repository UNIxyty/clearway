#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class TaiwanAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://ais.caa.gov.tw/eaip/AIRAC AIP AMDT 05-25_2025_09_04\index.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = TaiwanAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
