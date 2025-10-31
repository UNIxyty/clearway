#!/usr/bin/env python3
"""
Startup script for Airport AIP Lookup Service
Handles setup and launches the web application
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import selenium
        import flask
        import flask_cors
        logger.info("✅ All dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        return False

def install_dependencies():
    """Install required dependencies"""
    logger.info("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False

def check_chrome():
    """Check if Chrome is available"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=options)
        driver.quit()
        logger.info("✅ Chrome WebDriver is working")
        return True
    except Exception as e:
        logger.error(f"❌ Chrome WebDriver issue: {e}")
        logger.error("Please install Chrome and ChromeDriver")
        return False

def main():
    """Main startup function"""
    logger.info("🛩️  Airport AIP Lookup Service - Starting up...")
    
    # Check if we're in the right directory
    if not os.path.exists("app.py"):
        logger.error("❌ Please run this script from the project directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        logger.info("Installing missing dependencies...")
        if not install_dependencies():
            logger.error("❌ Failed to install dependencies. Please install manually:")
            logger.error("pip install -r requirements.txt")
            sys.exit(1)
    
    # Check Chrome
    if not check_chrome():
        logger.error("❌ Chrome WebDriver is not working properly")
        logger.error("Please ensure Chrome browser and ChromeDriver are installed")
        sys.exit(1)
    
    # Start the application
    logger.info("🚀 Starting the web application...")
    logger.info("📱 Open your browser and go to: http://localhost:8080")
    logger.info("⏹️  Press Ctrl+C to stop the server")
    
    try:
        from app import app
        app.run(host='0.0.0.0', port=8080, debug=False)
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")
    except Exception as e:
        logger.error(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
