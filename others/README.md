# Airport Information Scraper

A web-based application for fetching airport operational hours and contact information from aviation AIP (Aeronautical Information Publication) websites.

## Current Status

✅ **USA Airports**: Fully working - Supports all USA airports (codes starting with 'K')  
🚧 **France Airports**: Not yet available - Coming soon

## Features

- Automatic country detection based on airport code
- Headless web scraping for fast performance  
- Real-time data extraction from official aviation sources
- Clean web interface for easy lookup

## Supported Airports

### USA (FAA)
- **Coverage**: All USA airports
- **Airport Code Format**: Codes starting with 'K' (e.g., KJFK, KLAX, KMIA)
- **Data Extracted**:
  - Airport name
  - Tower operational hours
  - Owner and manager contact information (phone numbers, names)

### France (Coming Soon)
- **Status**: Not yet available
- **Airport Code Format**: Codes starting with 'LF' (e.g., LFBA, LFPG, LFML)
- **Note**: France eAIP integration is in development

## Quick Start

### Prerequisites
- Python 3.7+
- Chrome browser
- ChromeDriver (automatically installed)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Clearway
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python run.py
```

4. Open your browser and navigate to:
```
http://localhost:8080
```

### Usage

1. Enter an airport code (e.g., `KJFK` for John F. Kennedy International Airport)
2. Press Enter or click Submit
3. View the extracted airport information including:
   - Airport name
   - Operational hours
   - Contact phone numbers

### API Usage

You can also use the API directly:

```bash
curl -X POST http://localhost:8080/api/airport \
  -H "Content-Type: application/json" \
  -d '{"airportCode": "KJFK"}'
```

Example response:
```json
{
  "airportCode": "KJFK",
  "airportName": "John F Kennedy International Airport",
  "towerHours": [
    {
      "day": "Tower",
      "hours": "24 Hours"
    }
  ],
  "contacts": [
    {
      "type": "OWNER",
      "phone": "+1 718-244-4444",
      "name": "Port Authority of New York and New Jersey",
      "email": "",
      "notes": ""
    }
  ]
}
```

## Project Structure

```
Clearway/
├── app.py                  # Flask web application
├── airport_scraper.py      # USA airport scraper
├── france_aip_scraper.py   # France airport scraper (in development)
├── unified_scraper.py      # Unified scraper routing
├── index.html             # Web interface
├── requirements.txt       # Python dependencies
├── run.py                # Startup script
└── README.md             # This file
```

## Troubleshooting

### Port Already in Use
If port 8080 is already in use:
```bash
# Find the process
lsof -i :8080

# Kill the process
kill -9 <PID>
```

### ChromeDriver Issues
If you encounter ChromeDriver errors:
```bash
# The run.py script automatically installs ChromeDriver
# If issues persist, update Chrome to the latest version
```

## Development Status

### Completed
- ✅ USA AIP integration (FAA)
- ✅ Automatic country detection
- ✅ Headless scraping
- ✅ Web interface
- ✅ API endpoints

### In Progress
- 🚧 France eAIP integration
- 🚧 Additional countries

### Planned
- 📋 Support for more countries (Canada, UK, Germany, etc.)
- 📋 Caching for improved performance
- 📋 Batch airport lookups

## License

This project is for informational purposes only. Please respect the terms of service of the source websites.

## Contributing

Contributions welcome! Please see the issue tracker for areas needing help.

## Support

For issues or questions, please open an issue on the GitHub repository.
