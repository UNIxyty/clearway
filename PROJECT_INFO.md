# Clearway - Airport AIP Information System

## Project Overview

**Clearway** is a modern web application that provides real-time access to Aeronautical Information Publication (AIP) data from multiple countries. The system scrapes official AIP websites and PDF documents to extract critical airport operational information including hours, contacts, fire fighting categories, and traffic type permissions.

### Key Features

- **Multi-Country Support**: Currently supports USA, France, Estonia, Finland, Lithuania, and Latvia
- **Real-Time Data**: Live scraping from official AIP sources
- **Modern UI**: Built with Next.js, TypeScript, and shadcn/ui components
- **Fixed Data Structure**: Consistent 9-field output across all sources
- **Professional Deployment**: Backend on Railway, Frontend on Vercel

---

## Architecture

### Tech Stack

**Backend:**
- Python 3.11
- Flask (REST API)
- Playwright (web scraping)
- PyPDF2 (PDF parsing)
- Gunicorn (production server)

**Frontend:**
- Next.js 16
- TypeScript
- React
- Tailwind CSS
- shadcn/ui components
- Lucide React icons

**Deployment:**
- Railway (backend - Flask + Playwright)
- Vercel (frontend - Next.js)

### Project Structure

```
Clearway/
├── scrapers/                    # All scraper implementations
│   ├── airport_scraper.py      # USA scraper (base)
│   ├── france_aip_scraper.py   # France scraper
│   ├── estonia_aip_scraper_playwright.py  # Estonia (Playwright)
│   ├── finland_aip_scraper_playwright.py  # Finland (Playwright)
│   ├── lithuania_aip_scraper_pdf.py       # Lithuania (PDF-based)
│   └── latvia_aip_scraper_playwright.py   # Latvia (Playwright)
├── frontend/                    # Next.js application
│   ├── app/
│   │   ├── page.tsx            # Main UI component
│   │   ├── layout.tsx          # Root layout
│   │   └── globals.css         # Styles
│   ├── components/ui/          # shadcn/ui components
│   └── public/                 # Static assets
├── assets/                      # PDF files for Lithuania
│   ├── EY-AD-2-EYKA.pdf
│   ├── EY-AD-2-EYPA.pdf
│   ├── EY-AD-2-EYSA.pdf
│   └── EY-AD-2-EYVI.pdf
├── app.py                       # Flask API server
├── database.py                  # Airport cache
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker config for Railway
├── railway.toml                 # Railway configuration
├── .dockerignore                # Docker ignore rules
└── README.md                    # General documentation
```

---

## Fixed Data Structure

All scrapers return a **fixed 9-field structure** to ensure consistency across different AIP sources:

### AD 2.3 OPERATIONAL HOURS Section
1. **adAdministration** - AD Administration hours (H24/NIL/time range)
2. **adOperator** - AD Operator hours (H24/NIL/time range)
3. **customsAndImmigration** - Customs and Immigration hours (H24/NIL/On request)
4. **ats** - ATS hours (H24/NIL)
5. **operationalRemarks** - Remarks from operational hours section (NIL if empty)

### AD 2.2 AERODROME GEOGRAPHICAL AND ADMINISTRATIVE DATA Section
6. **trafficTypes** - Types of traffic permitted (IFR/VFR/Not specified)
7. **administrativeRemarks** - Remarks from AD 2.2 section (NIL if empty)

### AD 2.6 RESCUE AND FIRE FIGHTING SERVICES Section
8. **fireFightingCategory** - AD Category for fire fighting (1-9/Not specified)

### Additional Fields
9. **airportCode** - ICAO airport code (e.g., EVRA, EYKA, EETN)
10. **airportName** - Full airport name with location
11. **contacts** - Array of contact information (phone, email)

**Important**: All fields are ALWAYS returned. Missing values are shown as:
- `"NIL"` for empty hours or remarks
- `"Not specified"` for missing traffic types or fire category

---

## Scraper Logic by Country

### 1. Latvia (EV prefix)
**Scraper**: `latvia_aip_scraper_playwright.py`
**Source**: Live web scraping from `https://ais.lgs.lv/aiseaip`
**Technology**: Playwright headless browser

**Workflow**:
1. Navigate to Latvia AIP page
2. Find "CURRENT ISSUE" button with AIRAC date
3. Extract base URL dynamically (e.g., `https://ais.lgs.lv/eAIPfiles/2025_007_30-OCT-2025/...`)
4. Navigate to Part 3 AERODROMES → AD 2
5. Click on specific airport code or use direct navigation
6. Parse operational hours from AD 2.3 section
7. Extract remarks from appropriate sections
8. Parse fire fighting category from AD 2.6

**Key Patterns**:
- Operational hours in structured table format
- AD Operator labeled as "AD Operator" or "1AD"
- Frameset navigation with `eAISNavigation` and `eAISContent` frames

### 2. Lithuania (EY prefix)
**Scraper**: `lithuania_aip_scraper_pdf.py`
**Source**: Local PDF files in `assets/` directory
**Technology**: PyPDF2 PDF parsing

**Why PDF?**: Cloudflare Turnstile blocks web scraping with interactive verification

**Workflow**:
1. Load PDF files from assets directory
2. Map airport codes to PDF filenames (e.g., EYKA → EY-AD-2-EYKA.pdf)
3. Extract text from PDF using PyPDF2
4. Parse Lithuanian-specific formatting:
   - Services numbered: 1AD (Administration), 2 (Customs), 7 (ATS)
   - DAY patterns: MON-THU, FRI, MON-FRI with time ranges
5. Apply same field extraction as other scrapers

**PDF Files**:
- EYKA - Kaunas
- EYPA - Palanga
- EYSA - Šiauliai
- EYVI - Vilnius

### 3. Estonia (EE prefix)
**Scraper**: `estonia_aip_scraper_playwright.py`
**Source**: Live web scraping from `https://eaip.eans.ee`
**Technology**: Playwright headless browser

**Workflow**:
1. Navigate to Estonia eAIP main page
2. Access frameset navigation
3. Navigate to Part 3 AERODROMES
4. Select airport from navigation menu
5. Parse operational hours from structured table
6. Extract all required fields

**Key Patterns**:
- Similar structure to Latvia
- Services may have different numbering
- Estonian/English bilingual content

### 4. Finland (EF prefix)
**Scraper**: `finland_aip_scraper_playwright.py`
**Status**: **Partially implemented** (not actively used in production)
**Notes**: Complex Finnish AIP structure with extensive field extraction

### 5. France (LF prefix)
**Scraper**: `france_aip_scraper.py`
**Status**: Implemented but **requires updates** to new 9-field structure
**Notes**: Legacy scraper, needs refactoring

### 6. USA (K prefix)
**Scraper**: `airport_scraper.py`
**Status**: Base scraper for USA airports
**Notes**: Requires updates to match new field structure

---

## Frontend Components

### Main Page (`frontend/app/page.tsx`)

**Features**:
- Airport code input with validation
- Country detection based on ICAO code prefix
- Loading animation with flying plane icon
- Progress bar simulation
- Real-time error handling
- Responsive card-based UI

**Sections**:
1. **AD 2.3 OPERATIONAL HOURS** - Fixed display of 4 fields + remarks
2. **Contacts** - Phone and email with clickable links
3. **AD 2.2 GEOGRAPHICAL DATA** - Traffic types + administrative remarks
4. **AD 2.6 FIRE FIGHTING** - Category display

**State Management**:
- `airportCode` - User input
- `loading` - Request status
- `progress` - Loading bar percentage
- `airportInfo` - Response data
- `error` - Error messages

**API Integration**:
- Hardcoded Railway URL: `https://web-production-e7af.up.railway.app`
- POST request to `/api/airport`
- JSON response with fixed structure

### UI Components

All using shadcn/ui library:
- `Button` - Primary actions
- `Card` - Container components
- `Badge` - Status indicators
- `Input` - Text input fields
- `Separator` - Visual dividers
- `Plane`, `Search`, `Clock`, `Phone`, `Mail`, `Flame`, `PlaneTakeoff`, `FileText` icons

---

## API Endpoints

### Backend API (Flask - Railway)

**Base URL**: `https://web-production-e7af.up.railway.app`

#### POST `/api/airport`
Get airport information for given ICAO code

**Request**:
```json
{
  "airportCode": "EVRA"
}
```

**Response** (Success):
```json
{
  "airportCode": "EVRA",
  "airportName": "EVRA — RIGA",
  "contacts": [
    {
      "type": "AD Operator Contact 1",
      "phone": "+371 67207135",
      "name": "",
      "email": "office@riga-airport.com"
    }
  ],
  "adAdministration": "NIL",
  "adOperator": "H24",
  "customsAndImmigration": "H24",
  "ats": "H24",
  "operationalRemarks": "NIL",
  "trafficTypes": "Not specified",
  "administrativeRemarks": "Aircraft stand guidance lights...",
  "fireFightingCategory": "9"
}
```

**Response** (Error):
```json
{
  "error": "Error message here"
}
```

#### GET `/api/health`
Health check endpoint
- Returns: `{"status": "ok"}`

#### GET `/`
Serves the main HTML page (not used with Vercel frontend)

---

## Deployment

### Backend - Railway

**Configuration**:
- **Dockerfile**: Python 3.11-slim base image
- **Build**: Installs Playwright and system dependencies
- **Runtime**: Gunicorn with 2 workers, 2 threads
- **Port**: Dynamic via `$PORT` environment variable
- **Health Check**: `/api/health`

**Environment Variables** (Railway):
- `FLASK_ENV=production`
- `FLASK_DEBUG=0`
- `PORT` (auto-set by Railway)

**Build Process**:
1. Install system dependencies (Playwright requirements)
2. Install Python packages from `requirements.txt`
3. Install Playwright Chromium browser
4. Copy application code
5. Expose port 8080 (default)
6. Run Gunicorn

**Key Files**:
- `Dockerfile` - Container definition
- `railway.toml` - Railway-specific config
- `.dockerignore` - Exclude frontend and other files
- `requirements.txt` - Python dependencies

### Frontend - Vercel

**Configuration**:
- **Framework**: Next.js 16
- **Build Command**: `npm run build` (auto-detected)
- **Output**: Standalone build
- **Node Version**: 18.x

**Environment Variables** (Vercel):
- `NEXT_PUBLIC_API_URL=https://web-production-e7af.up.railway.app`

**Key Files**:
- `frontend/package.json` - Dependencies
- `frontend/next.config.ts` - Next.js config
- `frontend/vercel.json` - Vercel deployment config

**Auto-Deployment**:
- Vercel watches GitHub `main` branch
- Automatic deploys on push
- Build cache for faster deployments

---

## Country Detection Logic

Located in `frontend/app/page.tsx` and `app.py`:

```typescript
EV = Latvia 🇱🇻
EE = Estonia 🇪🇪
EF = Finland 🇫🇮
EY = Lithuania 🇱🇹
LF = France 🇫🇷
K  = USA 🇺🇸
```

**Scraper Routing**:
- Automatic selection based on airport code prefix
- Fallback to USA scraper for unknown prefixes

---

## Key Algorithms

### 1. Operational Hours Extraction

All scrapers follow this pattern:

```python
def _parse_operational_hours(self, text: str) -> List[Dict]:
    # 1. Find AD 2.3 section
    # 2. Search for each field pattern
    # 3. Track found/unfound fields
    # 4. Always return all 4 fields (with NIL for missing)
    
    results = []
    ad_admin_found = False
    ad_operator_found = False
    customs_found = False
    ats_found = False
    
    # Extract patterns...
    
    # Guarantee all fields exist
    if not ad_admin_found:
        results.append({"day": "AD Administration", "hours": "NIL"})
    # ... repeat for all fields
    
    return results
```

### 2. Remarks Extraction

Two types of remarks:

**Operational Remarks** (AD 2.3):
- Extracted before OPERATIONAL HOURS section
- Stops at first AD section reference
- Cleaned of footer text

**Administrative Remarks** (AD 2.2):
- Between AD 2.2 and AD 2.3 sections
- Stops at next AD 2.X reference
- Removes copyright and AIP metadata

### 3. Fire Fighting Category

From AD 2.6 section:
- Searches for "Category X" or "AD CATEGORY X" patterns
- Returns single digit 1-9
- Default: "Not specified"

### 4. Traffic Types

From AD 2.2 section:
- Looks for IFR/VFR patterns
- Returns format: "IFR/VFR", "VFR/IFR", "IFR", or "VFR"
- Default: "Not specified"

---

## Error Handling

### Backend

**Scraper Level**:
- Try-except blocks around all parsing
- Logs warnings for failed extractions
- Returns safe defaults (NIL, Not specified)
- Never crashes on missing data

**API Level**:
- Catches all exceptions from scrapers
- Returns JSON error responses
- Logs to console for debugging
- Thread-safe scraper instances

### Frontend

**Request Level**:
- Validates input (min 3 characters)
- Timeout handling
- Network error messages
- Graceful degradation

**UI Level**:
- Loading states
- Error banners
- Empty state messages
- Progress indicators

---

## Testing

### Local Testing

**Backend**:
```bash
cd /path/to/Clearway
python3 app.py
# Runs on http://localhost:8080
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```

**Test Individual Scrapers**:
```bash
python3 -c "from scrapers.latvia_aip_scraper_playwright import LatviaAIPScraperPlaywright
s = LatviaAIPScraperPlaywright()
import json
result = s.get_airport_info('EVRA')
print(json.dumps(result, indent=2))"
```

### Production Testing

**Railway Health**: `https://web-production-e7af.up.railway.app/api/health`

**Full Flow**: Search airport on Vercel frontend

---

## Known Issues & Limitations

1. **Finland/FRANCE/USA Scrapers**: Not updated to new 9-field structure
2. **Playwright Setup**: Requires Chromium installation in Railway
3. **PDF Parsing**: Lithuania limited to 4 airports with provided PDFs
4. **Remarks Cleaning**: May occasionally include some footer text
5. **Hardcoded URLs**: Railway URL hardcoded in frontend

---

## Future Enhancements

- Update remaining scrapers to new structure
- Add more countries (Sweden, Norway, Denmark)
- Implement caching layer
- Add user authentication
- Export to PDF/CSV functionality
- Mobile app version
- Historical data tracking

---

## Git Workflow

**Branch**: `main` (always deployable)

**Deployment Flow**:
1. Make changes locally
2. Test with local scrapers
3. Commit: `git commit -m "Descriptive message"`
4. Push: `git push origin main`
5. Auto-deploy:
   - Railway rebuilds backend
   - Vercel rebuilds frontend
6. Verify on production URLs

---

## Important URLs

**Production**:
- Frontend: Vercel URL (from deployment dashboard)
- Backend: `https://web-production-e7af.up.railway.app`

**Repository**:
- GitHub: `https://github.com/UNIxyty/clearway.git`

**AIP Sources**:
- Latvia: `https://ais.lgs.lv/aiseaip`
- Estonia: `https://eaip.eans.ee`
- Lithuania: Local PDFs
- Finland: `https://ais.fi`

---

## Contact & Credits

**Created by**: Verxyl
**Logo**: `/frontend/public/verxyl-logo.png`

**Technologies**:
- Next.js + TypeScript + shadcn/ui
- Python + Flask + Playwright
- Railway + Vercel deployment

---

## Quick Start for New Developer

1. **Clone Repository**:
   ```bash
   git clone https://github.com/UNIxyty/clearway.git
   cd Clearway
   ```

2. **Backend Setup**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   python3 app.py
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Test**:
   - Open `http://localhost:3000`
   - Search for "EVRA" (Riga, Latvia)
   - Verify all 9 fields display correctly

5. **Deploy**:
   - Push to GitHub `main` branch
   - Railway and Vercel auto-deploy

---

## Critical Notes

1. **Always test scrapers locally** before pushing
2. **All scrapers MUST return 9 fields** (no exceptions)
3. **Use "NIL" for empty operational data** (not empty strings)
4. **Frontend expects exact field names** (see interface)
5. **Remove TowerHour interface** - replaced with direct fields
6. **Document any new AIP pattern** you encounter
7. **Keep remarks under 200 characters** for UI
8. **Never crash on parsing failures** - return safe defaults

---

## Maintenance

**When Adding New Country**:
1. Create scraper in `scrapers/` directory
2. Implement `get_airport_info()` returning 9 fields
3. Add country detection in `app.py` and `frontend/page.tsx`
4. Create instance in `app.py` get_scraper()
5. Test locally extensively
6. Update this document

**When Updating Fields**:
1. Update ALL scrapers simultaneously
2. Update frontend interface
3. Test all countries
4. Update PROJECT_INFO.md
5. Deploy together

---

**Last Updated**: November 1, 2025
**Version**: 2.0 (Fixed 9-Field Structure)



