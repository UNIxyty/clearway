#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class UkraineAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://aip.rossiya-airlines.com/ukraine/bilingual_aip/vol_1/gen_0/GEN_0.2.pdf")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = UkraineAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
