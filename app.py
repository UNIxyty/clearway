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
    get_country_from_code as get_scraper_country,
    get_scraper_instance,
    get_available_countries
)
from country_detector import get_country_from_code

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
                    if scraper is not None:
                        scraper_instances[country] = scraper
            else:
                scraper_instances[country] = scraper

        result = scraper_instances.get(country)
        if result is None:
            logger.error(f"Failed to load scraper for {country}")
            raise Exception(f"Scraper not available for {country}")
        return result

def detect_country(airport_code):
    """Detect country from airport code using registry"""
    country = get_scraper_country(airport_code)
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
        
        # Add country information to response
        country_info = get_country_from_code(airport_code)
        if country_info:
            airport_info['country'] = country_info.get('country')
            airport_info['region'] = country_info.get('region')
        
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

@app.route('/api/countries', methods=['GET'])
def get_all_countries():
    """API endpoint to get all available countries with prefixes and flags"""
    try:
        from country_detector import ICAO_PREFIXES, COUNTRY_FLAGS, load_countries_data
        import json
        from pathlib import Path
        
        countries_data = load_countries_data()
        countries_dict = {}  # Use dict to avoid duplicates by prefix
        
        # First, load countries from airport_codes.json (extracted from PDFs)
        airport_codes_path = Path('assets') / 'airport_codes.json'
        if airport_codes_path.exists():
            try:
                with open(airport_codes_path, 'r', encoding='utf-8') as f:
                    airport_codes_data = json.load(f)
                    codes = airport_codes_data.get('codes', {})
                    
                    for prefix, country_data in codes.items():
                        country_name = country_data.get('country', '')
                        if country_name:
                            # Get flag from COUNTRY_FLAGS
                            flag = COUNTRY_FLAGS.get(country_name, '🏳️')
                            if flag == '🏳️':
                                # Try normalized match
                                country_normalized = country_name.replace('\u2019', "'").replace('\u2018', "'")
                                flag = COUNTRY_FLAGS.get(country_normalized, '🏳️')
                            
                            countries_dict[prefix] = {
                                'country': country_name,
                                'prefix': prefix,
                                'flag': flag,
                                'region': country_data.get('region', 'UNKNOWN'),
                                'airport_count': len(country_data.get('airports', []))
                            }
            except Exception as e:
                logger.warning(f"Error loading airport_codes.json: {e}")
        
        # Also add countries from aip_countries_full.json (if not already in dict)
        prefix_to_country = {}
        for prefix, country in ICAO_PREFIXES.items():
            if country not in prefix_to_country:
                prefix_to_country[country] = []
            prefix_to_country[country].append(prefix)
        
        seen_countries = set()
        for country_data in countries_data:
            country_name = country_data.get('country', '').strip()
            if country_name and country_name not in seen_countries:
                seen_countries.add(country_name)
                
                # Get prefixes for this country
                prefixes = prefix_to_country.get(country_name, [])
                if not prefixes:
                    continue
                
                # Get flag
                flag = COUNTRY_FLAGS.get(country_name, '🏳️')
                if flag == '🏳️':
                    country_normalized = country_name.replace('\u2019', "'").replace('\u2018', "'")
                    flag = COUNTRY_FLAGS.get(country_normalized, '🏳️')
                if flag == '🏳️':
                    country_upper = country_name.upper()
                    for key, value in COUNTRY_FLAGS.items():
                        key_normalized = key.replace('\u2019', "'").replace('\u2018', "'")
                        if key_normalized.upper() == country_upper or key.upper() == country_upper:
                            flag = value
                            break
                        if country_upper in key.upper() or key.upper() in country_upper:
                            flag = value
                            break
                
                # Use the most common/representative prefix
                main_prefix = min(prefixes, key=len) if prefixes else ''
                
                # Only add if not already in dict (airport_codes.json takes precedence)
                if main_prefix not in countries_dict:
                    countries_dict[main_prefix] = {
                        'country': country_name,
                        'prefix': main_prefix,
                        'flag': flag,
                        'region': country_data.get('region', 'UNKNOWN'),
                        'airport_count': 0
                    }
        
        # Convert to list and sort by country name
        countries_list = list(countries_dict.values())
        countries_list.sort(key=lambda x: x['country'])
        
        return jsonify({
            'success': True,
            'count': len(countries_list),
            'countries': countries_list
        })
        
    except Exception as e:
        logger.error(f"Error getting countries list: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/country', methods=['POST'])
def detect_country_info():
    """API endpoint to detect country from airport code"""
    try:
        data = request.get_json()
        if not data or 'airportCode' not in data:
            return jsonify({'error': 'Airport code is required'}), 400
        
        airport_code = data['airportCode'].strip().upper()
        
        if not airport_code or len(airport_code) < 3:
            return jsonify({'error': 'Invalid airport code'}), 400
        
        country_info = get_country_from_code(airport_code)
        
        if country_info:
            return jsonify({
                'success': True,
                'airportCode': airport_code,
                'country': country_info.get('country'),
                'region': country_info.get('region'),
                'code': country_info.get('code'),
                'type': country_info.get('type', 'Unknown'),
                'flag': country_info.get('flag', '🏳️')
            })
        else:
            return jsonify({
                'success': False,
                'airportCode': airport_code,
                'message': 'Country not found for this airport code'
            })
            
    except Exception as e:
        logger.error(f"Error detecting country: {e}")
        return jsonify({'error': str(e)}), 500

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
