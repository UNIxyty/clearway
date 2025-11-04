#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class IndiaAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://aim-india.aai.aero/eaip/eaip-v2-05-2025/index-en-GB.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = IndiaAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
