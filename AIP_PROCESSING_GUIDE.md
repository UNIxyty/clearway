# AIP Processing Guide

This guide explains how to process AIP (Aeronautical Information Publication) PDF files and extract airport information.

## Overview

The system processes AIP PDFs in three main steps:

1. **Convert PDFs to TXT**: Converts all PDF files to text format while keeping PDFs as backups
2. **Extract Airport Codes**: Searches for "AD 2.1" sections to identify airport codes in each document
3. **Extract AIP Sections**: Extracts specific information from AD 2.2, AD 2.3, and AD 2.6 sections

## Quick Start

Run the master script to process all AIPs:

```bash
python scripts/process_all_aips.py
```

This will:
- Convert all PDFs to TXT (backups saved to `AIP's/backups/`)
- Extract airport codes (saved to `assets/airport_codes_from_txt.json`)
- Extract AIP sections (saved to `assets/aip_extracted_data.json`)

## What Gets Extracted

### AD 2.2 - Aerodrome Geographical and Administrative Data
- **Types of traffic permitted (IFR/VFR)**: What types of traffic are allowed
- **Remarks**: Additional administrative notes

### AD 2.3 - Operational Hours
- **AD Administrator**: Aerodrome administrator information
- **AD Operator**: Aerodrome operator information
- **Customs and immigration**: Customs and immigration services
- **ATS**: Air Traffic Services information
- **Remarks**: Operational remarks

### AD 2.6 - Rescue and Fire Fighting Services
- **AD Category for fire fighting**: Fire fighting category classification

## File Structure

### Input Files
- `AIP's/`: Directory containing PDF files
  - Single PDF files (e.g., `afghanistan_aip.pdf`) contain all airports for that country
  - Folders (e.g., `AIP's/austria/`) contain individual airport PDFs

### Output Files
- `AIP's/backups/`: Backup copies of all original PDF files
- `AIP's/txt_versions/`: TXT versions of all PDF files
- `assets/airport_codes_from_txt.json`: Airport codes extracted from TXT files
- `assets/aip_extracted_data.json`: Extracted AIP information (used by Flask app)

## Integration with Web Application

The Flask application (`app.py`) automatically loads the extracted data from `assets/aip_extracted_data.json` on startup. When a user searches for an airport:

1. The app first checks the extracted AIP data
2. If found, it uses that data (which takes precedence)
3. If not found, it falls back to web scraping (if available)

### Restarting the App

After running the extraction scripts, restart the Flask app to load the new data:

```bash
python app.py
```

## Individual Scripts

If you need to run scripts individually:

### 1. Convert PDFs to TXT
```bash
python scripts/convert_pdfs_to_txt.py
```

### 2. Extract Airport Codes
```bash
python scripts/extract_airport_codes_from_txt.py
```

### 3. Extract AIP Sections
```bash
python scripts/extract_aip_sections.py
```

## Understanding Airport Code Extraction

The script searches for "AD 2.1" sections in each document. Each occurrence of "AD 2.1" typically indicates one airport in the AIP. The script:

1. Finds all "AD 2.1" occurrences
2. Extracts nearby 4-letter ICAO codes
3. Filters out false positives (common words like "PAGE", "DATE", etc.)
4. Associates codes with countries based on file/folder names

### Country Detection

- **Single PDF files**: Country is detected from filename (e.g., `afghanistan_aip.pdf` → Afghanistan)
- **Folder structure**: Country is detected from folder name (e.g., `AIP's/austria/` → Austria)
- **Airport codes in folders**: If PDFs are in a folder, those are individual airport PDFs for that country

## Troubleshooting

### No airport codes found
- Check if "AD 2.1" appears in the TXT files
- Verify the PDF was converted correctly
- Check the country mapping in the script

### Missing AIP sections
- The extraction uses pattern matching - some AIPs may have different formatting
- Check the TXT file manually to see the actual format
- You may need to adjust the regex patterns in `extract_aip_sections.py`

### Import errors
- Make sure you're running scripts from the project root directory
- Ensure all dependencies are installed: `pip install -r requirements.txt`

## Next Steps

1. Run the processing pipeline: `python scripts/process_all_aips.py`
2. Review the extracted data in `assets/aip_extracted_data.json`
3. Restart the Flask app to load the new data
4. Test the web application with airport codes from the extracted data

## Notes

- PDFs are preserved as backups - the conversion process is non-destructive
- The extraction process may take some time depending on the number of PDFs
- Some AIPs may have different formatting - the scripts handle common variations but may need adjustments for edge cases

