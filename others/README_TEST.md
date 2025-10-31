# 🛩️ Airport AIP Information Lookup - Test Version

A fast, headless web application that scrapes airport information from the USA FAA database. Enter an airport code and get tower hours and contact information instantly.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python run.py
```

### 3. Open Your Browser
Go to: **http://localhost:8080**

## ✨ Features

- **Fast Headless Scraping**: No browser window opens, maximum speed
- **Real-time Data**: Direct from FAA database
- **Beautiful UI**: Modern, responsive design
- **Error Handling**: Graceful handling of invalid codes
- **Loading States**: Visual feedback during scraping

## 🎯 How It Works

1. **Enter Airport Code**: Type any 3-4 letter airport code (e.g., KJFK, LAX, KORD)
2. **Press Enter**: The system automatically searches
3. **Get Results**: View tower hours and contact information

## 📊 Data Retrieved

### Tower Hours
- Operating hours for each day
- Parsed from the "Operations" section
- Structured format for easy reading

### Contact Information
- Phone numbers (clickable links)
- Email addresses
- Manager/Owner contact details
- Extracted from "Contacts" section

## 🔧 Technical Details

### Fast Scraping Optimizations
- **Headless Chrome**: No GUI overhead
- **Disabled Images**: Faster page loads
- **Optimized Timeouts**: Minimal waiting
- **Eager Page Loading**: Don't wait for all resources

### API Endpoints
- `POST /api/airport` - Get airport information
- `GET /api/health` - Health check
- `GET /api/airports/test` - Test multiple airports

## 🧪 Testing

### Test Individual Airports
```bash
curl -X POST http://localhost:8080/api/airport \
  -H "Content-Type: application/json" \
  -d '{"airportCode": "KJFK"}'
```

### Test Multiple Airports
```bash
curl http://localhost:8080/api/airports/test
```

## 📝 Example Airport Codes

| Code | Airport | Location |
|------|---------|----------|
| KJFK | John F. Kennedy | New York |
| KLAX | Los Angeles | California |
| KORD | O'Hare | Chicago |
| KDFW | Dallas/Fort Worth | Texas |
| KATL | Hartsfield-Jackson | Atlanta |

## 🛠️ Troubleshooting

### Chrome WebDriver Issues
```bash
# Install ChromeDriver
brew install chromedriver  # macOS
# or download from https://chromedriver.chromium.org/
```

### Dependencies Issues
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Port Already in Use
```bash
# Kill process on port 8080
lsof -ti:8080 | xargs kill -9
```

## 🔍 How the Scraping Works

1. **URL Construction**: `https://nfdc.faa.gov/nfdcApps/services/ajv5/airportDisplay.jsp?airportId={code}`
2. **Page Navigation**: Headless Chrome loads the page
3. **Section Detection**: Finds "Operations" and "Contacts" sections
4. **Data Extraction**: Parses tower hours and contact information
5. **Structured Output**: Returns JSON with organized data

## 📈 Performance

- **Average Response Time**: 2-5 seconds
- **Memory Usage**: ~50MB
- **Concurrent Requests**: Thread-safe design
- **Error Recovery**: Automatic retry logic

## 🔒 Security

- **Input Validation**: Airport codes are validated
- **CORS Enabled**: Cross-origin requests allowed
- **Error Sanitization**: No sensitive data in error messages

## 🎨 UI Features

- **Responsive Design**: Works on desktop and mobile
- **Loading Animation**: Visual feedback during scraping
- **Error Messages**: Clear error reporting
- **Clickable Phone Numbers**: Direct calling capability
- **Auto-formatting**: Airport codes automatically uppercase

## 🚀 Production Deployment

For production deployment:

1. Set `debug=False` in `app.py`
2. Use a production WSGI server (gunicorn)
3. Set up proper logging
4. Configure reverse proxy (nginx)

```bash
# Production example
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

## 📞 Support

If you encounter issues:
1. Check the console logs
2. Verify Chrome/ChromeDriver installation
3. Test with the health check endpoint
4. Try different airport codes

---

**Note**: This is a test version focused on speed and functionality. The scraper is optimized for the USA FAA database structure and may need adjustments for other countries' AIP systems.
