#!/usr/bin/env python3
"""
Convert all PDF AIP files to TXT format while keeping PDFs as backups
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, List
from pypdf import PdfReader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_pdf_to_txt(pdf_path: Path, txt_path: Path) -> bool:
    """Convert a single PDF file to TXT format"""
    try:
        reader = PdfReader(str(pdf_path))
        text_content = []
        
        for page_num, page in enumerate(reader.pages, 1):
            try:
                text = page.extract_text()
                if text:
                    text_content.append(f"=== Page {page_num} ===\n{text}\n")
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num} of {pdf_path.name}: {e}")
                continue
        
        if text_content:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(text_content))
            logger.info(f"Converted: {pdf_path.name} -> {txt_path.name} ({len(reader.pages)} pages)")
            return True
        else:
            logger.warning(f"No text extracted from {pdf_path.name}")
            return False
            
    except Exception as e:
        logger.error(f"Error converting {pdf_path.name}: {e}")
        return False

def backup_pdf(pdf_path: Path, backup_dir: Path) -> Path:
    """Copy PDF to backup directory, preserving directory structure"""
    # Get relative path from AIP's directory
    relative_path = pdf_path.relative_to(pdf_path.parents[1] if pdf_path.parent.name != "AIP's" else pdf_path.parent)
    
    # Create backup path
    backup_path = backup_dir / relative_path
    
    # Create parent directories if needed
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy file
    shutil.copy2(pdf_path, backup_path)
    return backup_path

def process_aip_directory(aip_dir: Path, backup_dir: Path, txt_dir: Path):
    """Process all PDFs in AIP directory structure"""
    stats = {
        'converted': 0,
        'failed': 0,
        'skipped': 0,
        'backed_up': 0
    }
    
    # Create backup and txt directories
    backup_dir.mkdir(parents=True, exist_ok=True)
    txt_dir.mkdir(parents=True, exist_ok=True)
    
    # Process single PDF files in root
    for pdf_file in sorted(aip_dir.glob('*.pdf')):
        if pdf_file.name.startswith('.'):
            continue
        
        # Create corresponding txt path
        txt_file = txt_dir / f"{pdf_file.stem}.txt"
        
        # Skip if already converted
        if txt_file.exists():
            logger.info(f"Skipping (already exists): {txt_file.name}")
            stats['skipped'] += 1
            continue
        
        # Backup PDF
        try:
            backup_pdf(pdf_file, backup_dir)
            stats['backed_up'] += 1
        except Exception as e:
            logger.warning(f"Failed to backup {pdf_file.name}: {e}")
        
        # Convert to TXT
        if convert_pdf_to_txt(pdf_file, txt_file):
            stats['converted'] += 1
        else:
            stats['failed'] += 1
    
    # Process country folders
    for country_folder in sorted(aip_dir.iterdir()):
        if not country_folder.is_dir() or country_folder.name.startswith('.') or country_folder.name == 'html':
            continue
        
        logger.info(f"\nProcessing folder: {country_folder.name}")
        
        # Create corresponding txt folder
        txt_folder = txt_dir / country_folder.name
        txt_folder.mkdir(parents=True, exist_ok=True)
        
        # Process PDFs in folder
        for pdf_file in sorted(country_folder.glob('*.pdf')):
            if pdf_file.name.startswith('.'):
                continue
            
            # Create corresponding txt path
            txt_file = txt_folder / f"{pdf_file.stem}.txt"
            
            # Skip if already converted
            if txt_file.exists():
                logger.info(f"  Skipping (already exists): {pdf_file.name}")
                stats['skipped'] += 1
                continue
            
            # Backup PDF
            try:
                backup_pdf(pdf_file, backup_dir)
                stats['backed_up'] += 1
            except Exception as e:
                logger.warning(f"  Failed to backup {pdf_file.name}: {e}")
            
            # Convert to TXT
            if convert_pdf_to_txt(pdf_file, txt_file):
                stats['converted'] += 1
            else:
                stats['failed'] += 1
    
    return stats

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert PDF AIP files to TXT format')
    parser.add_argument('--aip-dir', type=str, default="AIP's", help='Path to AIP directory')
    parser.add_argument('--backup-dir', type=str, default="AIP's/backups", help='Path to backup directory')
    parser.add_argument('--txt-dir', type=str, default="AIP's/txt_versions", help='Path to TXT output directory')
    args = parser.parse_args()
    
    aip_dir = Path(args.aip_dir)
    backup_dir = Path(args.backup_dir)
    txt_dir = Path(args.txt_dir)
    
    if not aip_dir.exists():
        logger.error(f"AIP directory not found: {aip_dir}")
        return
    
    logger.info(f"Converting PDFs from {aip_dir} to TXT format")
    logger.info(f"Backups will be saved to: {backup_dir}")
    logger.info(f"TXT files will be saved to: {txt_dir}")
    
    stats = process_aip_directory(aip_dir, backup_dir, txt_dir)
    
    logger.info(f"\n{'='*60}")
    logger.info("CONVERSION SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Converted: {stats['converted']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Skipped (already exists): {stats['skipped']}")
    logger.info(f"Backed up: {stats['backed_up']}")
    logger.info(f"\nDone!")

if __name__ == '__main__':
    main()

