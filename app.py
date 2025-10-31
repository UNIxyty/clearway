#!/usr/bin/env python3
"""
Flask web application for Airport AIP Information Lookup
Provides API endpoint and serves the frontend
"""

import json
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from scrapers.airport_scraper import AirportScraper
from scrapers.france_aip_scraper import FranceAIPScraper
from scrapers.estonia_aip_scraper_playwright import EstoniaAIPScraperPlaywright
from scrapers.finland_aip_scraper_playwright import FinlandAIPScraperPlaywright
from scrapers.lithuania_aip_scraper_pdf import LithuaniaAIPScraperPDF
from scrapers.latvia_aip_scraper_playwright import LatviaAIPScraperPlaywright
from database import airport_cache
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global scraper instances (thread-safe)
usa_scraper_instance = None
france_scraper_instance = None
estonia_scraper_instance = None
finland_scraper_instance = None
lithuania_scraper_instance = None
latvia_scraper_instance = None
scraper_lock = threading.Lock()

def get_scraper(country='USA'):
    """Get or create appropriate scraper instance based on country (thread-safe)"""
    global usa_scraper_instance, france_scraper_instance, estonia_scraper_instance, finland_scraper_instance, lithuania_scraper_instance, latvia_scraper_instance
    
    with scraper_lock:
        if country == 'USA':
            if usa_scraper_instance is None:
                usa_scraper_instance = AirportScraper()
            return usa_scraper_instance
        elif country == 'FRANCE':
            if france_scraper_instance is None:
                france_scraper_instance = FranceAIPScraper()
            return france_scraper_instance
        elif country == 'ESTONIA':
            if estonia_scraper_instance is None:
                estonia_scraper_instance = EstoniaAIPScraperPlaywright()
            return estonia_scraper_instance
        elif country == 'FINLAND':
            # Create new instance for each request to avoid threading issues
            return FinlandAIPScraperPlaywright()
        elif country == 'LITHUANIA':
            if lithuania_scraper_instance is None:
                lithuania_scraper_instance = LithuaniaAIPScraperPDF()
            return lithuania_scraper_instance
        elif country == 'LATVIA':
            # Create new instance for each request to avoid threading issues
            return LatviaAIPScraperPlaywright()
        else:
            # Default to USA
            if usa_scraper_instance is None:
                usa_scraper_instance = AirportScraper()
            return usa_scraper_instance

def detect_country(airport_code):
    """Detect country from airport code"""
    airport_code = airport_code.upper().strip()
    if airport_code.startswith('K'):
        return 'USA'
    elif airport_code.startswith('LF'):
        return 'FRANCE'
    elif airport_code.startswith('EE'):
        return 'ESTONIA'
    elif airport_code.startswith('EF'):
        return 'FINLAND'
    elif airport_code.startswith('EY'):
        return 'LITHUANIA'
    elif airport_code.startswith('EV'):
        return 'LATVIA'
    else:
        return 'USA'  # Default to USA

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('assets', 'index.html')

@app.route('/api/airport', methods=['POST'])
def get_airport_info():
    """API endpoint to get airport information"""
    try:
        # Get airport code from request
        data = request.get_json()
        if not data or 'airportCode' not in data:
            return jsonify({'error': 'Airport code is required'}), 400
        
        airport_code = data['airportCode'].strip().upper()
        
        # Validate airport code
        if not airport_code or len(airport_code) < 3:
            return jsonify({'error': 'Invalid airport code'}), 400
        
        logger.info(f"Processing request for airport: {airport_code}")
        
        # Check cache first
        cached_data = airport_cache.get_cached_airport(airport_code)
        if cached_data:
            logger.info(f"Returning cached data for {airport_code}")
            return jsonify(cached_data)
        
        # Detect country and get appropriate scraper
        country = detect_country(airport_code)
        logger.info(f"Detected country: {country} for airport {airport_code}")
        
        # Get appropriate scraper instance
        scraper = get_scraper(country)
        
        # Scrape airport information
        start_time = time.time()
        airport_info = scraper.get_airport_info(airport_code)
        end_time = time.time()
        
        logger.info(f"Scraped airport info for {airport_code} in {end_time - start_time:.2f} seconds")
        
        # Cache the result
        airport_cache.cache_airport(airport_code, airport_info)
        
        return jsonify(airport_info)
        
    except Exception as e:
        logger.error(f"Error processing airport request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'Airport AIP Lookup'})

@app.route('/api/airports/test', methods=['GET'])
def test_airports():
    """Test endpoint with sample airports"""
    test_codes = ['KJFK', 'KLAX', 'KORD', 'KDFW', 'KATL']
    
    results = []
    scraper = get_scraper()
    
    for code in test_codes:
        try:
            start_time = time.time()
            info = scraper.get_airport_info(code)
            end_time = time.time()
            
            results.append({
                'code': code,
                'name': info.get('airportName', 'Unknown'),
                'response_time': f"{end_time - start_time:.2f}s",
                'status': 'success'
            })
        except Exception as e:
            results.append({
                'code': code,
                'name': 'Error',
                'response_time': 'N/A',
                'status': 'error',
                'error': str(e)
            })
    
    return jsonify({'test_results': results})

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

def cleanup_scraper():
    """Cleanup scraper instances on shutdown"""
    global usa_scraper_instance, france_scraper_instance, estonia_scraper_instance, finland_scraper_instance, lithuania_scraper_instance, latvia_scraper_instance
    with scraper_lock:
        try:
            if usa_scraper_instance:
                usa_scraper_instance.close()
                usa_scraper_instance = None
        except Exception as e:
            logger.warning(f"Error closing USA scraper: {e}")
        
        try:
            if france_scraper_instance:
                france_scraper_instance.close()
                france_scraper_instance = None
        except Exception as e:
            logger.warning(f"Error closing France scraper: {e}")
        
        try:
            if estonia_scraper_instance:
                estonia_scraper_instance.close()
                estonia_scraper_instance = None
        except Exception as e:
            logger.warning(f"Error closing Estonia scraper: {e}")
        
        try:
            if finland_scraper_instance:
                finland_scraper_instance.close()
                finland_scraper_instance = None
        except Exception as e:
            logger.warning(f"Error closing Finland scraper: {e}")
        
        try:
            if lithuania_scraper_instance:
                lithuania_scraper_instance.close()
                lithuania_scraper_instance = None
        except Exception as e:
            logger.warning(f"Error closing Lithuania scraper: {e}")
        
        try:
            if latvia_scraper_instance:
                latvia_scraper_instance.close()
                latvia_scraper_instance = None
        except Exception as e:
            logger.warning(f"Error closing Latvia scraper: {e}")
        
        # Clean up daily cache
        try:
            airport_cache.cleanup_daily()
        except Exception as e:
            logger.warning(f"Error cleaning up cache: {e}")

@app.teardown_appcontext
def close_scraper(error):
    """Close scraper on app context teardown"""
    pass  # Keep scraper alive for reuse

if __name__ == '__main__':
    try:
        logger.info("Starting Airport AIP Lookup Service")
        logger.info("Available endpoints:")
        logger.info("  GET  / - Main webpage")
        logger.info("  POST /api/airport - Get airport information")
        logger.info("  GET  /api/health - Health check")
        logger.info("  GET  /api/airports/test - Test multiple airports")
        
        # Run the Flask app
        app.run(
            host='0.0.0.0',
            port=8080,
            debug=True,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        cleanup_scraper()
