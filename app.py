#!/usr/bin/env python3
"""
Flask web application for Airport AIP Information Lookup
Provides API endpoint and serves the frontend
"""

import json
import logging
import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import time

# Add scrapers directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.scraper_registry import (
    get_country_from_code,
    get_scraper_instance,
    get_available_countries
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global scraper instances dictionary (thread-safe)
# Format: {country_name: scraper_instance}
scraper_instances = {}
scraper_lock = threading.Lock()

def get_scraper(country='USA'):
    """Get or create appropriate scraper instance based on country (thread-safe)"""
    global scraper_instances
    
    with scraper_lock:
        if country not in scraper_instances:
            scraper = get_scraper_instance(country)
            if scraper is None:
                logger.warning(f"Scraper not found for {country}, falling back to USA")
                country = 'USA'
                if country not in scraper_instances:
                    scraper = get_scraper_instance(country)
            scraper_instances[country] = scraper
        return scraper_instances.get(country)

def detect_country(airport_code):
    """Detect country from airport code using registry"""
    country = get_country_from_code(airport_code)
    if country is None:
        logger.warning(f"Could not detect country for {airport_code}, defaulting to USA")
        return 'USA'
    return country

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

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
        
        return jsonify(airport_info)
        
    except Exception as e:
        logger.error(f"Error processing airport request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    available_countries = get_available_countries()
    return jsonify({
        'status': 'healthy', 
        'service': 'Airport AIP Lookup',
        'supported_countries': len(available_countries),
        'countries': available_countries
    })

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
    """Cleanup all scraper instances on shutdown"""
    global scraper_instances
    with scraper_lock:
        for country, scraper in scraper_instances.items():
            try:
                if scraper and hasattr(scraper, 'close'):
                    scraper.close()
                    logger.info(f"Closed scraper for {country}")
            except Exception as e:
                logger.error(f"Error closing scraper for {country}: {e}")
        scraper_instances.clear()

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
        
        # Log available countries
        available_countries = get_available_countries()
        logger.info(f"Supported countries: {len(available_countries)}")
        logger.info(f"Countries: {', '.join(sorted(available_countries))}")
        
        # Get port from environment variable (for Railway/Vercel) or default to 8080
        port = int(os.environ.get('PORT', 8080))
        debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        
        # Run the Flask app
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        cleanup_scraper()
