# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Clearway is a web-based airport information scraper that fetches operational hours, contact information, and administrative data from aviation AIP (Aeronautical Information Publication) websites. The system consists of:

- **Backend**: Python Flask API with country-specific web scrapers
- **Frontend**: Next.js 16 React application with TypeScript and Tailwind CSS
- **Architecture**: Modular scraper system supporting 40+ countries with automatic country detection

## Development Commands

### Backend (Python)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Flask backend server
python run.py
# Or directly:
python app.py

# The backend runs on http://localhost:8080 by default
# Can be configured via PORT environment variable
```

### Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint
npm run lint
```

### Testing Individual Scrapers

```bash
# Test USA scraper
python airport_scraper.py

# Test unified scraper (auto-detects country)
python unified_scraper.py

# Test specific country scrapers
python scrapers/estonia_aip_scraper_playwright.py
python scrapers/france_aip_scraper.py
```

## Architecture Overview

### Backend Structure

The backend uses a **dynamic scraper registry pattern** that automatically routes airport codes to country-specific scrapers:

1. **Country Detection** (`country_detector.py`):
   - Maps ICAO prefixes to countries (e.g., K→USA, LF→France, EE→Estonia)
   - Supports 40+ countries with prefix mapping
   - Provides country flags and region information

2. **Scraper Registry** (`scrapers/scraper_registry.py`):
   - Central registry mapping country names to scraper modules
   - Dynamic class loading via `importlib` to reduce memory footprint
   - Caches scraper instances in thread-safe dictionary

3. **Base Scrapers**:
   - `BaseEAIPScraperPlaywright`: Generic eAIP scraper for Eurocontrol-style Web Table Based AIP systems
   - `airport_scraper.py`: USA-specific FAA scraper (Selenium-based)
   - Country-specific scrapers inherit from base classes

4. **Flask API** (`app.py`):
   - `/api/airport` - POST - Get airport information
   - `/api/countries` - GET - List all supported countries with prefixes
   - `/api/country` - POST - Detect country from airport code
   - `/api/health` - GET - Health check with supported countries count
   - Thread-safe scraper instance management

### Frontend Structure

Next.js 16 App Router application (`frontend/app/`):

- **page.tsx**: Main airport search interface with world map selector
- **Components**:
  - Radix UI primitives (Dialog, Label, Separator, etc.)
  - Custom components in `components/` directory
  - `WorldMapSelector`: Interactive map for country/airport selection
- **Styling**: Tailwind CSS 4 with custom animations
- **API Integration**: Hardcoded Railway deployment URL for production

### Data Flow

```
User Input (KJFK)
  ↓
Frontend (page.tsx)
  ↓
POST /api/airport {"airportCode": "KJFK"}
  ↓
Flask app.py → detect_country()
  ↓
scraper_registry.get_country_from_code() → "USA"
  ↓
scraper_registry.get_scraper_instance("USA") → AirportScraper()
  ↓
scraper.get_airport_info("KJFK")
  ↓
Returns: {airportCode, airportName, adAdministration, adOperator, customsAndImmigration, ats, operationalRemarks, trafficTypes}
```

### Scraper Implementation Patterns

**USA (Selenium-based)**:
- Navigates FAA website
- Extracts data from HTML tables
- Parses tower hours and contact information

**Eurocontrol eAIP (Playwright-based)**:
- Navigates frame-based eAIP interfaces
- Clicks through navigation: Part 3 → AERODROMES → AD 2 → airport code
- Extracts data from sections: AD 2.2 (geographical/admin), AD 2.3 (operational hours)
- Used by: Estonia, Finland, Latvia, France, and 30+ other European countries

**PDF-based**:
- For countries with PDF-only AIPs (e.g., Lithuania)
- Extracts text from specific sections using PyPDF

### Key Technical Details

**Thread Safety**: The Flask app uses a global `scraper_instances` dictionary protected by `scraper_lock` to ensure thread-safe access to scraper instances across concurrent requests.

**Lazy Loading**: Scrapers are instantiated on-demand and cached. The first request for a country initializes its scraper; subsequent requests reuse the instance.

**Browser Automation**:
- **Selenium**: Used for USA FAA website (requires ChromeDriver)
- **Playwright**: Used for most international eAIP sites (auto-installs browsers)
- Headless mode by default for performance

**Error Handling**: The unified scraper falls back to USA scraper if country detection fails or scraper not found.

## Adding New Country Scrapers

To add support for a new country:

1. **Determine the scraper type**:
   - Eurocontrol eAIP → Extend `BaseEAIPScraperPlaywright`
   - Custom website → Implement custom scraper with Playwright/Selenium
   - PDF-only → Use PyPDF extraction

2. **Create scraper file** in `scrapers/`:
   ```python
   # scrapers/newcountry_aip_scraper_playwright.py
   from scrapers.base_eaip_scraper import BaseEAIPScraperPlaywright

   class NewCountryAIPScraperPlaywright(BaseEAIPScraperPlaywright):
       def __init__(self):
           super().__init__(index_url='https://eaip.newcountry.com/index.html')
   ```

3. **Register in scraper_registry.py**:
   ```python
   AIRPORT_CODE_PREFIXES = {
       'XX': ('NEW_COUNTRY', 'newcountry_aip_scraper_playwright', 'NewCountryAIPScraperPlaywright'),
   }
   ```

4. **Update country_detector.py** with ICAO prefix mapping

5. **Test the scraper**:
   ```bash
   python -c "from scrapers.newcountry_aip_scraper_playwright import NewCountryAIPScraperPlaywright; s = NewCountryAIPScraperPlaywright(); print(s.get_airport_info('XXXX'))"
   ```

## Database/Caching

The project includes optional Supabase caching (`database.py`):
- Caches airport data by date to reduce scraping load
- Configure via `SUPABASE_URL` and `SUPABASE_ANON_KEY` environment variables
- Gracefully degrades if credentials not provided

## Deployment

- **Backend**: Deployed on Railway (https://web-production-e7af.up.railway.app)
- **Frontend**: Next.js deployment (references Railway URL)
- **Environment Variables**: `PORT` for Flask, `FLASK_DEBUG` for debug mode

## Common Patterns

**Parsing Operational Hours**: All scrapers return a consistent format:
```python
{
    'adAdministration': 'H24' | 'NIL' | time range,
    'adOperator': 'H24' | 'NIL' | time range,
    'customsAndImmigration': 'H24' | 'NIL' | 'On request',
    'ats': 'H24' | 'NIL' | time range
}
```

**Airport Name Format**: `{CODE} — {Full Name}` (e.g., "KJFK — John F Kennedy International Airport")

**Error Responses**: Always include `{'error': 'descriptive message'}` for failed requests

## Important Files

- `app.py` - Flask API server and route handlers
- `scrapers/scraper_registry.py` - Central scraper registry and country detection
- `scrapers/base_eaip_scraper.py` - Base class for Eurocontrol eAIP scrapers
- `country_detector.py` - ICAO prefix to country mapping with flags
- `frontend/app/page.tsx` - Main React component with search interface
- `requirements.txt` - Python dependencies (Selenium, Playwright, Flask, etc.)
