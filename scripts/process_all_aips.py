#!/usr/bin/env python3
"""
Master script to process all AIP PDFs:
1. Convert PDFs to TXT format (keeping PDFs as backups)
2. Extract airport codes by searching for AD 2.1 sections
3. Extract AIP sections (AD 2.2, AD 2.3, AD 2.6) from TXT files
"""

import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_script(script_path: Path, description: str):
    """Run a Python script and handle errors"""
    logger.info(f"\n{'='*60}")
    logger.info(f"STEP: {description}")
    logger.info(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=Path(__file__).parent.parent,
            check=True,
            capture_output=False
        )
        logger.info(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} failed with error: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ {description} failed with error: {e}")
        return False

def main():
    """Main function to run all processing steps"""
    scripts_dir = Path(__file__).parent
    
    steps = [
        (scripts_dir / 'convert_pdfs_to_txt.py', 'Convert PDFs to TXT format'),
        (scripts_dir / 'extract_airport_codes_from_txt.py', 'Extract airport codes from TXT files'),
        (scripts_dir / 'extract_aip_sections.py', 'Extract AIP sections (AD 2.2, AD 2.3, AD 2.6)'),
    ]
    
    logger.info("Starting AIP processing pipeline...")
    logger.info("This will:")
    logger.info("  1. Convert all PDFs to TXT (backups will be created)")
    logger.info("  2. Extract airport codes by searching for AD 2.1 sections")
    logger.info("  3. Extract AIP information from AD 2.2, AD 2.3, and AD 2.6 sections")
    
    success_count = 0
    for script_path, description in steps:
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            continue
        
        if run_script(script_path, description):
            success_count += 1
        else:
            logger.error(f"Pipeline stopped due to error in: {description}")
            return False
    
    logger.info(f"\n{'='*60}")
    logger.info("PIPELINE SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Completed: {success_count}/{len(steps)} steps")
    
    if success_count == len(steps):
        logger.info("✓ All steps completed successfully!")
        logger.info("\nNext steps:")
        logger.info("  - Review the extracted data in assets/aip_extracted_data.json")
        logger.info("  - Restart the Flask app to load the new data")
        return True
    else:
        logger.error("✗ Pipeline completed with errors")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

