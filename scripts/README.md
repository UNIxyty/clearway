# AIP Processing Scripts

This directory contains scripts to process AIP (Aeronautical Information Publication) PDF files.

## Scripts Overview

### 1. `convert_pdfs_to_txt.py`
Converts all PDF AIP files to TXT format while keeping PDFs as backups.

**Usage:**
```bash
python scripts/convert_pdfs_to_txt.py
```

**Options:**
- `--aip-dir`: Path to AIP directory (default: `AIP's`)
- `--backup-dir`: Path to backup directory (default: `AIP's/backups`)
- `--txt-dir`: Path to TXT output directory (default: `AIP's/txt_versions`)

### 2. `extract_airport_codes_from_txt.py`
Searches each TXT document for "AD 2.1" sections to identify and extract airport codes.

**Usage:**
```bash
python scripts/extract_airport_codes_from_txt.py
```

**Options:**
- `--txt-dir`: Path to TXT directory (default: `AIP's/txt_versions`)
- `--aip-dir`: Path to AIP directory (default: `AIP's`)
- `--output`: Output JSON file (default: `assets/airport_codes_from_txt.json`)

### 3. `extract_aip_sections.py`
Extracts specific information from AIP TXT files:
- **AD 2.2**: Types of traffic permitted (IFR/VFR) and Remarks
- **AD 2.3**: AD Administrator/AD Operator, Customs and immigration, ATS, Remarks
- **AD 2.6**: AD Category for fire fighting

**Usage:**
```bash
python scripts/extract_aip_sections.py
```

**Options:**
- `--txt-dir`: Path to TXT directory (default: `AIP's/txt_versions`)
- `--aip-dir`: Path to AIP directory (default: `AIP's`)
- `--output`: Output JSON file (default: `assets/aip_extracted_data.json`)

### 4. `process_all_aips.py`
Master script that runs all processing steps in sequence.

**Usage:**
```bash
python scripts/process_all_aips.py
```

This script will:
1. Convert all PDFs to TXT format (creating backups)
2. Extract airport codes by searching for AD 2.1 sections
3. Extract AIP information from AD 2.2, AD 2.3, and AD 2.6 sections

## Processing Pipeline

The recommended workflow is to run the master script:

```bash
python scripts/process_all_aips.py
```

This will:
1. **Convert PDFs to TXT**: All PDF files in `AIP's/` will be converted to TXT format. Original PDFs are backed up to `AIP's/backups/`.
2. **Extract Airport Codes**: The script searches for "AD 2.1" sections in each TXT file to identify airport codes. Results are saved to `assets/airport_codes_from_txt.json`.
3. **Extract AIP Sections**: The script extracts information from:
   - AD 2.2: Types of traffic permitted and remarks
   - AD 2.3: AD Administrator/Operator, Customs, ATS, Remarks
   - AD 2.6: Fire fighting category
   
   Results are saved to `assets/aip_extracted_data.json`.

## Output Files

- `AIP's/backups/`: Backup copies of all original PDF files
- `AIP's/txt_versions/`: TXT versions of all PDF files
- `assets/airport_codes_from_txt.json`: Airport codes extracted from TXT files
- `assets/aip_extracted_data.json`: Extracted AIP information (used by the Flask app)

## Notes

- If PDFs are in a folder (e.g., `AIP's/austria/`), those are individual airport PDFs for that country
- If a PDF is in the root (e.g., `AIP's/afghanistan_aip.pdf`), it contains all airports for that country
- The extraction scripts automatically handle both cases

## Integration with Flask App

The Flask app (`app.py`) automatically loads the extracted data from `assets/aip_extracted_data.json` on startup. After running the extraction scripts, restart the Flask app to load the new data.

