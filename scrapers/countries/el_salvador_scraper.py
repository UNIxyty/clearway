#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class ElSalvadorAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://www.cocesna.org/aipca/AIPMS/AIP_2512/Eurocontrol/EL SALVADOR/2025-09-04-NON AIRAC/html/index-es-ES.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = ElSalvadorAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
