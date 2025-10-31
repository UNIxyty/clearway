#!/usr/bin/env python3
"""
AIP (Aeronautical Information Publication) Automation Script
Handles different country AIP websites with their specific button structures
"""

import json
import time
import logging
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIPAutomation:
    def __init__(self, config_file: str = "aip_config.json"):
        """Initialize the AIP automation with configuration file"""
        self.config = self.load_config(config_file)
        self.driver = None
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def setup_driver(self, headless: bool = False) -> None:
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        logger.info("WebDriver initialized successfully")
    
    def navigate_to_aip(self, country_code: str) -> bool:
        """Navigate to the AIP website for the specified country"""
        if country_code not in self.config['countries']:
            logger.error(f"Country code '{country_code}' not found in configuration")
            return False
        
        country_config = self.config['countries'][country_code]
        url = country_config['aip_url']
        
        try:
            logger.info(f"Navigating to {country_config['name']} AIP: {url}")
            self.driver.get(url)
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            return False
    
    def wait_for_elements(self, country_code: str) -> bool:
        """Wait for loading elements to disappear"""
        country_config = self.config['countries'][country_code]
        wait_elements = country_config.get('wait_elements', [])
        
        for element_selector in wait_elements:
            try:
                # Wait for element to be present
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, element_selector))
                )
                # Wait for element to disappear
                WebDriverWait(self.driver, 10).until_not(
                    EC.presence_of_element_located((By.CSS_SELECTOR, element_selector))
                )
                logger.info(f"Loading element {element_selector} disappeared")
            except TimeoutException:
                logger.warning(f"Loading element {element_selector} did not disappear within timeout")
        
        return True
    
    def perform_additional_actions(self, country_code: str) -> bool:
        """Perform additional actions specific to the country's website"""
        country_config = self.config['countries'][country_code]
        additional_actions = country_config.get('additional_actions', [])
        
        for action in additional_actions:
            try:
                if action['type'] == 'click':
                    element = self.driver.find_element(By.CSS_SELECTOR, action['selector'])
                    element.click()
                    logger.info(f"Clicked element: {action['selector']}")
                    
                elif action['type'] == 'select':
                    select_element = Select(self.driver.find_element(By.CSS_SELECTOR, action['selector']))
                    select_element.select_by_value(action['value'])
                    logger.info(f"Selected value '{action['value']}' in {action['selector']}")
                    
                elif action['type'] == 'wait':
                    WebDriverWait(self.driver, action.get('timeout', 10)).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, action['selector']))
                    )
                    logger.info(f"Waited for element: {action['selector']}")
                
                time.sleep(1)  # Small delay between actions
                
            except (NoSuchElementException, TimeoutException) as e:
                if action.get('required', True):
                    logger.error(f"Failed to perform action {action}: {e}")
                    return False
                else:
                    logger.warning(f"Optional action failed: {action}: {e}")
        
        return True
    
    def click_button(self, country_code: str, button_type: str) -> bool:
        """Click a specific button type for the given country"""
        if country_code not in self.config['countries']:
            logger.error(f"Country code '{country_code}' not found")
            return False
        
        country_config = self.config['countries'][country_code]
        button_selectors = country_config.get('button_selectors', {})
        
        if button_type not in button_selectors:
            logger.error(f"Button type '{button_type}' not found for {country_code}")
            return False
        
        selector = button_selectors[button_type]
        
        try:
            # Wait for element to be clickable
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            logger.info(f"Successfully clicked {button_type} button for {country_code}")
            return True
            
        except TimeoutException:
            logger.error(f"Button {button_type} not found or not clickable for {country_code}")
            return False
        except Exception as e:
            logger.error(f"Error clicking button {button_type} for {country_code}: {e}")
            return False
    
    def download_aip(self, country_code: str) -> bool:
        """Complete AIP download process for a specific country"""
        logger.info(f"Starting AIP download process for {country_code}")
        
        # Navigate to the AIP website
        if not self.navigate_to_aip(country_code):
            return False
        
        # Wait for loading elements
        self.wait_for_elements(country_code)
        
        # Perform additional actions
        if not self.perform_additional_actions(country_code):
            return False
        
        # Click accept terms if available
        if self.click_button(country_code, 'accept_terms'):
            time.sleep(2)
        
        # Click proceed button if available
        if self.click_button(country_code, 'proceed_button'):
            time.sleep(2)
        
        # Click download button
        if not self.click_button(country_code, 'download_button'):
            return False
        
        logger.info(f"AIP download initiated for {country_code}")
        return True
    
    def get_available_countries(self) -> List[str]:
        """Get list of available country codes"""
        return list(self.config['countries'].keys())
    
    def get_country_info(self, country_code: str) -> Optional[Dict]:
        """Get information about a specific country"""
        return self.config['countries'].get(country_code)
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

def main():
    """Example usage of the AIP automation"""
    automation = AIPAutomation()
    
    try:
        # Setup driver
        automation.setup_driver(headless=False)  # Set to True for headless mode
        
        # List available countries
        print("Available countries:")
        for country in automation.get_available_countries():
            country_info = automation.get_country_info(country)
            print(f"  {country}: {country_info['name']}")
        
        # Example: Download AIP for USA
        country_code = "USA"
        if automation.download_aip(country_code):
            print(f"Successfully initiated AIP download for {country_code}")
        else:
            print(f"Failed to download AIP for {country_code}")
        
        # Keep browser open for a few seconds to see the result
        time.sleep(5)
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    finally:
        automation.close()

if __name__ == "__main__":
    main()

