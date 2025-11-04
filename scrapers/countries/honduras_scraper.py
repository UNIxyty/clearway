#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class HondurasAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://www.ahac.gob.hn/eAIP1/AIP_2528\Eurocontrol\HONDURAS\2025-08-07-AIRAC\html/index-es-ES.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = HondurasAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
