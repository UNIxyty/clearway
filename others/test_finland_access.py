#!/usr/bin/env python3
"""
Test script to access Finland AIP and get a working airport link
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from finland_aip_scraper_playwright import FinlandAIPScraperPlaywright
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_page_access():
    """Test accessing the page and getting airport links"""
    scraper = FinlandAIPScraperPlaywright()
    
    try:
        # Step 1: Try accessing the main AIP page
        logger.info("Step 1: Accessing main AIP page")
        main_url = "https://www.ais.fi/eaip/"
        scraper.page.goto(main_url, wait_until="networkidle")
        scraper.page.wait_for_timeout(3000)
        logger.info(f"Main page URL: {scraper.page.url}")
        
        if "0.0.7.128" in scraper.page.url:
            logger.error("Main page redirected to IP address")
            return
        
        # Step 2: Look for effective day link
        logger.info("Step 2: Looking for effective day link")
        effective_day_link = scraper.page.locator("a:has-text('02 Oct 2025')").first
        if effective_day_link.is_visible():
            logger.info("Found effective day link, clicking...")
            effective_day_link.click()
            scraper.page.wait_for_load_state("networkidle")
            scraper.page.wait_for_timeout(3000)
            logger.info(f"Effective day page URL: {scraper.page.url}")
            
            if "0.0.7.128" in scraper.page.url:
                logger.error("Effective day page redirected to IP address")
                return
            
            # Step 3: Look for airport links in frames
            logger.info("Step 3: Looking for airport links in frames")
            frames = scraper.page.frames
            logger.info(f"Found {len(frames)} frames")
            
            for i, frame in enumerate(frames):
                try:
                    frame_name = frame.name
                    logger.info(f"Frame {i}: {frame_name}")
                    
                    # Look for EFHK links in this frame
                    efhk_links = frame.query_selector_all('a[href*="EFHK"]')
                    logger.info(f"  Found {len(efhk_links)} EFHK links in frame {i}")
                    
                    if efhk_links:
                        for j, link in enumerate(efhk_links[:3]):  # Show first 3
                            try:
                                href = link.get_attribute('href')
                                text = link.text_content()
                                logger.info(f"    Link {j}: {href} - '{text}'")
                                
                                # Try clicking this link
                                if j == 0:  # Try the first link
                                    logger.info(f"    Trying to click first EFHK link...")
                                    link.click()
                                    scraper.page.wait_for_timeout(3000)
                                    logger.info(f"    After click URL: {scraper.page.url}")
                                    
                                    if "0.0.7.128" in scraper.page.url:
                                        logger.warning(f"    Link {j} redirected to IP address")
                                    else:
                                        logger.info(f"    Link {j} worked! Final URL: {scraper.page.url}")
                                        return
                                        
                            except Exception as e:
                                logger.debug(f"    Error with link {j}: {e}")
                                continue
                                
                except Exception as e:
                    logger.debug(f"Error checking frame {i}: {e}")
                    continue
        else:
            logger.warning("Effective day link not found")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    test_page_access()
