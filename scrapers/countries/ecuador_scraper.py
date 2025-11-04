#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class EcuadorAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://www.ais.aviacioncivil.gob.ec/ifis3/")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = EcuadorAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
