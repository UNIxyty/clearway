#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class UnitedArabEmiratesAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://www.gcaa.gov.ae/en/ais")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = UnitedArabEmiratesAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
