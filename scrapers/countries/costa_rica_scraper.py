#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class CostaRicaAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://www.cocesna.org/aipca/AIPMR/AIP_2504/Eurocontrol/COSTA RICA/2025-10-30-DOUBLE AIRAC/html/index-es-ES.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = CostaRicaAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
