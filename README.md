# Clearway - Airport AIP Lookup System

A comprehensive Aeronautical Information Publication (AIP) lookup system for airports worldwide. Built with a Python Flask backend and a modern Next.js TypeScript frontend using shadcn/ui.

## 🚀 Features

- **Multi-Country Support**: Scrape AIP data from 6 countries
- **Modern Frontend**: Professional UI built with Next.js, TypeScript, and shadcn/ui
- **Real-time Data**: Live web scraping with Playwright
- **PDF Parsing**: Efficient PDF-based data extraction for Lithuania
- **Smart Caching**: Supabase-powered caching system
- **Responsive Design**: Works on all devices
- **Type-Safe**: Full TypeScript support

## 📊 Supported Countries

| Country | Code Prefix | Scraper Type | Airports |
|---------|-------------|--------------|----------|
| 🇺🇸 USA | K* | Web | KJFK, KLAX, KORD, KDFW, KATL, etc. |
| 🇫🇷 France | LF* | Web | LFPG, LFBO, etc. |
| 🇪🇪 Estonia | EE* | Web (Playwright) | EETN, etc. |
| 🇫🇮 Finland | EF* | Web (Playwright) | EFHK, EFJV, etc. |
| 🇱🇹 Lithuania | EY* | PDF | EYVI, EYSA, EYKA, EYPA |
| 🇱🇻 Latvia | EV* | Web (Playwright) | EVRA, EVLA, EVLI, EVCA, EVGA, EVPA, EVRS, EVVA |

## 🏗️ Architecture

### Backend (Python Flask)
- **Framework**: Flask
- **Scrapers**: Selenium, Playwright, PyPDF2
- **Database**: Supabase (caching)
- **Port**: 8080

### Frontend (Next.js)
- **Framework**: Next.js 16
- **Language**: TypeScript
- **UI**: shadcn/ui + Tailwind CSS
- **Icons**: Lucide React
- **Port**: 3000

## 📁 Project Structure

```
Clearway/
├── app.py                          # Flask API server
├── database.py                     # Cache management
├── requirements.txt                # Python dependencies
├── start.sh                        # Quick start script
├── .gitignore
├── README.md
│
├── scrapers/                       # Python scrapers
│   ├── __init__.py
│   ├── airport_scraper.py         # USA scraper
│   ├── france_aip_scraper.py      # France scraper
│   ├── estonia_aip_scraper_playwright.py
│   ├── finland_aip_scraper_playwright.py
│   ├── lithuania_aip_scraper_pdf.py  # PDF-based
│   └── latvia_aip_scraper_playwright.py
│
├── assets/                         # Resources
│   ├── index.html                  # Old frontend (legacy)
│   ├── EY-AD-2-EYVI.pdf
│   ├── EY-AD-2-EYSA.pdf
│   ├── EY-AD-2-EYKA.pdf
│   └── EY-AD-2-EYPA.pdf
│
├── frontend/                       # Next.js app
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx               # Main UI
│   │   └── globals.css
│   ├── components/
│   │   └── ui/                    # shadcn components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── input.tsx
│   │       ├── label.tsx
│   │       ├── badge.tsx
│   │       └── separator.tsx
│   ├── lib/
│   │   └── utils.ts
│   ├── package.json
│   └── README.md
│
└── others/                         # Config & docs
    ├── aip_config.json
    ├── README.md
    └── ...
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Node.js 18+**
- **Playwright** (installed automatically)
- **Supabase** credentials (optional, for caching)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/UNIxyty/clearway.git
   cd clearway
   ```

2. **Install Python dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

4. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials (optional)
   ```

### Running the Application

#### Quick Start
```bash
./start.sh
```

#### Manual Start

**Terminal 1 - Backend:**
```bash
python3 app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend && npm run dev
```

Then open [http://localhost:3000](http://localhost:3000) in your browser.

## 🔌 API Endpoints

### POST `/api/airport`
Get airport information by ICAO code.

**Request:**
```json
{
  "airportCode": "EVRA"
}
```

**Response:**
```json
{
  "airportCode": "EVRA",
  "airportName": "EVRA — RIGA",
  "towerHours": [
    {
      "day": "General",
      "hours": "H24"
    }
  ],
  "contacts": [
    {
      "type": "AD Operator Contact 1",
      "phone": "+371 67207135",
      "email": "office@riga-airport.com"
    }
  ]
}
```

### GET `/api/health`
Health check endpoint.

### GET `/api/airports/test`
Test multiple airports.

## 🧪 Development

### Backend Development
```bash
# Run with debug mode
python3 app.py

# Run tests
pytest
```

### Frontend Development
```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint
npm run lint
```

## 📦 Dependencies

### Backend
- Flask 2.3+
- Playwright 1.40+
- PyPDF2 3.0+
- Selenium 4.15+
- Supabase 2.0+
- BeautifulSoup4 4.12+

### Frontend
- Next.js 16
- React 19
- TypeScript 5
- Tailwind CSS 4
- shadcn/ui components
- Lucide React

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - See LICENSE file for details

## 👥 Authors

- UNIxyty

## 🙏 Acknowledgments

- AIP data sources from various national aviation authorities
- shadcn/ui for beautiful components
- Next.js team for the amazing framework

## 📞 Support

For issues or questions, please open an issue on GitHub.

---

Made with ❤️ for the aviation community

