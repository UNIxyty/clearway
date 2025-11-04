#!/usr/bin/env python3
from typing import Dict
from .base_eaip_scraper import BaseEAIPScraperPlaywright


class SingaporeAIPScraper(BaseEAIPScraperPlaywright):
	def __init__(self, headless: bool = True):
		super().__init__(index_url="https://aim-sg.caas.gov.sg/aim-content/uploads/aip/02-OCT-2025/AIP-2/2025-10-02-000000/pdf/SG-AIP.pdf?s=248D1A35B654129A22988D502DA75B236FA1C90A")


def get_airport_info(airport_code: str, headless: bool = True) -> Dict:
	scraper = SingaporeAIPScraper(headless=headless)
	return scraper.get_airport_info(airport_code, headless=headless)
