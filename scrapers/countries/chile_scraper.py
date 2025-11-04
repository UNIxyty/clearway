#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class ChileAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://aipchile.dgac.gob.cl/aip/vol1/seccion/airac")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = ChileAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
