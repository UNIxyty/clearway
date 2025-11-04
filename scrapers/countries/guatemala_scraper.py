#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class GuatemalaAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://www.dgac.gob.gt/home/aip_e/AIP_2508/Eurocontrol/GUATEMALA/2025-05-15-DOUBLE AIRAC/html/index-es-ES.html")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = GuatemalaAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
