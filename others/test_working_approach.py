#!/usr/bin/env python3
"""
Test the working approach for Finland AIP
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from finland_aip_scraper_playwright import FinlandAIPScraperPlaywright
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_working_approach():
    """Test the working approach"""
    scraper = FinlandAIPScraperPlaywright()
    
    try:
        # Step 1: Navigate to main AIP page
        logger.info("Step 1: Navigating to main AIP page")
        main_url = "https://www.ais.fi/eaip/"
        scraper.page.goto(main_url, wait_until="networkidle")
        scraper.page.wait_for_timeout(3000)
        logger.info(f"Main page URL: {scraper.page.url}")
        
        if "0.0.7.128" in scraper.page.url:
            logger.error("Main page redirected to IP")
            return
        
        # Step 2: Click effective day link
        logger.info("Step 2: Clicking effective day link")
        effective_day_link = scraper.page.locator("a:has-text('02 Oct 2025')").first
        if effective_day_link.is_visible():
            effective_day_link.click()
            scraper.page.wait_for_load_state("networkidle")
            scraper.page.wait_for_timeout(3000)
            logger.info(f"Effective day page URL: {scraper.page.url}")
            
            if "0.0.7.128" in scraper.page.url:
                logger.error("Effective day page redirected to IP")
                return
        else:
            logger.error("Could not find effective day link")
            return
        
        # Step 3: Find navigation frame and extract airport link
        logger.info("Step 3: Finding navigation frame")
        frames = scraper.page.frames
        logger.info(f"Found {len(frames)} frames")
        
        nav_frame = None
        for frame in frames:
            try:
                nav_div = frame.query_selector('#eAISNav')
                if nav_div:
                    nav_frame = frame
                    logger.info(f"Found navigation div in frame: {frame.name}")
                    break
            except Exception as e:
                logger.debug(f"Could not check frame: {e}")
                continue
        
        if not nav_frame:
            logger.error("Could not find navigation frame")
            return
        
        # Look for EFHK link
        airport_link = nav_frame.query_selector('#eAISNav a[href*="EFHK"][href*="eAIP"]')
        if airport_link:
            aip_url = airport_link.get_attribute('href')
            logger.info(f"Found EFHK AIP URL: {aip_url}")
            
            # Make it absolute
            if aip_url.startswith('/'):
                aip_url = f"https://www.ais.fi{aip_url}"
            elif not aip_url.startswith('http'):
                base_url = "https://www.ais.fi/eaip/005-2025_2025_10_02/"
                aip_url = base_url + aip_url.lstrip('/')
            
            logger.info(f"Absolute AIP URL: {aip_url}")
            
            # Step 4: Navigate to AIP page
            logger.info("Step 4: Navigating to AIP page")
            scraper.page.goto(aip_url, wait_until="networkidle")
            scraper.page.wait_for_timeout(3000)
            logger.info(f"AIP page URL: {scraper.page.url}")
            
            if "0.0.7.128" in scraper.page.url:
                logger.error("AIP page redirected to IP")
            else:
                logger.info("SUCCESS! AIP page loaded without IP redirect")
                
                # Test content extraction
                content = scraper.page.text_content()
                logger.info(f"Content length: {len(content)} characters")
                
                # Look for airport information
                if "EFHK" in content and "HELSINKI" in content.upper():
                    logger.info("SUCCESS! Found airport information in content")
                else:
                    logger.warning("Airport information not found in content")
        else:
            logger.error("Could not find EFHK link in navigation div")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    test_working_approach()
