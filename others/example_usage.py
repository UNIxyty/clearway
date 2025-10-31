#!/usr/bin/env python3
"""
Example usage of the AIP Automation System
Demonstrates different ways to use the system
"""

from aip_automation import AIPAutomation
import time

def example_single_country():
    """Example: Download AIP for a single country"""
    print("=== Single Country Example ===")
    
    automation = AIPAutomation()
    
    try:
        # Setup driver (set headless=True for background operation)
        automation.setup_driver(headless=False)
        
        # Download AIP for USA
        country_code = "USA"
        print(f"Downloading AIP for {country_code}...")
        
        if automation.download_aip(country_code):
            print(f"✅ Successfully initiated AIP download for {country_code}")
        else:
            print(f"❌ Failed to download AIP for {country_code}")
        
        # Wait to see the result
        time.sleep(3)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        automation.close()

def example_multiple_countries():
    """Example: Download AIP for multiple countries"""
    print("=== Multiple Countries Example ===")
    
    automation = AIPAutomation()
    
    try:
        automation.setup_driver(headless=False)
        
        # List of countries to process
        countries = ["USA", "UK", "Germany"]
        
        for country_code in countries:
            print(f"\nProcessing {country_code}...")
            
            if automation.download_aip(country_code):
                print(f"✅ Successfully processed {country_code}")
            else:
                print(f"❌ Failed to process {country_code}")
            
            # Wait between countries
            time.sleep(2)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        automation.close()

def example_list_available_countries():
    """Example: List all available countries"""
    print("=== Available Countries ===")
    
    automation = AIPAutomation()
    
    try:
        countries = automation.get_available_countries()
        
        print("Available countries:")
        for country_code in countries:
            country_info = automation.get_country_info(country_code)
            print(f"  {country_code}: {country_info['name']}")
            print(f"    URL: {country_info['aip_url']}")
            print(f"    Buttons: {list(country_info['button_selectors'].keys())}")
            print()
        
    except Exception as e:
        print(f"Error: {e}")

def example_custom_workflow():
    """Example: Custom workflow with manual steps"""
    print("=== Custom Workflow Example ===")
    
    automation = AIPAutomation()
    
    try:
        automation.setup_driver(headless=False)
        
        country_code = "France"
        
        # Navigate to the website
        if automation.navigate_to_aip(country_code):
            print(f"✅ Navigated to {country_code} AIP website")
            
            # Wait for page to load
            automation.wait_for_elements(country_code)
            print("✅ Page loaded")
            
            # Perform additional actions
            automation.perform_additional_actions(country_code)
            print("✅ Additional actions completed")
            
            # Manually click specific buttons
            if automation.click_button(country_code, "accept_terms"):
                print("✅ Terms accepted")
            
            if automation.click_button(country_code, "proceed_button"):
                print("✅ Proceeded")
            
            if automation.click_button(country_code, "download_button"):
                print("✅ Download initiated")
            else:
                print("❌ Download failed")
        
        time.sleep(3)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        automation.close()

def main():
    """Run all examples"""
    print("AIP Automation System - Examples")
    print("=" * 40)
    
    # List available countries
    example_list_available_countries()
    
    # Single country example
    example_single_country()
    
    # Multiple countries example (commented out to avoid opening too many browsers)
    # example_multiple_countries()
    
    # Custom workflow example
    # example_custom_workflow()

if __name__ == "__main__":
    main()
