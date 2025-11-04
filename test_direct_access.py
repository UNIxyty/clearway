#!/usr/bin/env python3
"""
Test direct access to France AIP content
"""

import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_direct_access():
    """Test direct access to the AIP content"""
    
    # The href you provided
    href = "AIRAC-2025-10-02/html/index-fr-FR.html"
    
    # The base URL pattern you provided
    base_url = "https://www.sia.aviation-civile.gouv.fr/media/dvd/eAIP_02_OCT_2025/FRANCE/"
    
    # Try different URL patterns
    urls_to_try = [
        base_url + href,
        base_url + "AIRAC-2025-10-02/html/FR-AD-2-LFBA-fr-FR.html",  # Try airport-specific page
        base_url + "AIRAC-2025-10-02/html/FR-AD-2-fr-FR.html",  # Try AD-2 section
        base_url + "AIRAC-2025-10-02/html/FR-AD-2.2-LFBA-fr-FR.html",  # Try AD-2.2 section
    ]
    
    for i, full_url in enumerate(urls_to_try):
        logger.info(f"\n=== Testing URL {i+1}: {full_url} ===")
        test_url(full_url, base_url)

def test_url(full_url, base_url):
    
    logger.info(f"Testing direct access to: {full_url}")
    
    try:
        # Create session with proper headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Try to access the URL
        response = session.get(full_url, timeout=30)
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        logger.info(f"Content length: {len(response.text)}")
        logger.info(f"Content preview: {response.text[:500]}")
        
        if response.status_code == 200:
            logger.info("SUCCESS: Direct access worked!")
            
            # Parse the frameset to find frame sources
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for frames
            frames = soup.find_all('frame')
            logger.info(f"Found {len(frames)} frames")
            
            for i, frame in enumerate(frames):
                src = frame.get('src', '')
                name = frame.get('name', '')
                logger.info(f"Frame {i}: name='{name}', src='{src}'")
                
                if src:
                    # Try to access the frame content
                    frame_url = base_url + src
                    logger.info(f"Trying to access frame content: {frame_url}")
                    
                    try:
                        frame_response = session.get(frame_url, timeout=30)
                        logger.info(f"Frame response status: {frame_response.status_code}")
                        logger.info(f"Frame content length: {len(frame_response.text)}")
                        logger.info(f"Frame content preview: {frame_response.text[:500]}")
                        
                        # Look for airport information in frame
                        if 'LFBA' in frame_response.text:
                            logger.info("Found LFBA in frame content!")
                        
                        if 'OPERATIONAL HOURS' in frame_response.text or 'HORAIRES' in frame_response.text:
                            logger.info("Found operational hours section in frame!")
                        
                        if 'CONTACTS' in frame_response.text or 'CONTACT' in frame_response.text:
                            logger.info("Found contacts section in frame!")
                            
                    except Exception as e:
                        logger.error(f"Error accessing frame {i}: {e}")
                
        else:
            logger.error(f"Failed to access URL: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error accessing URL: {e}")

if __name__ == "__main__":
    test_direct_access()
