"""
Convert AIP PDFs to text files for easier parsing
Keeps original PDFs as backups
"""

import PyPDF2
from pathlib import Path

def convert_pdfs_to_txt():
    """Convert all AIP PDFs to .txt files"""
    aips_dir = Path(__file__).parent.parent / "AIP's"
    txt_dir = aips_dir / "txt_versions"
    txt_dir.mkdir(exist_ok=True)

    pdf_files = list(aips_dir.glob("*.pdf"))

    print(f"Converting {len(pdf_files)} PDF files to text...")
    print(f"Text files will be saved to: {txt_dir}")
    print(f"Original PDFs remain in: {aips_dir}\n")

    converted = 0
    failed = 0

    for pdf_file in pdf_files:
        txt_file = txt_dir / f"{pdf_file.stem}.txt"

        try:
            with open(pdf_file, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ""

                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text += f"\n{'='*80}\n"
                    text += f"PAGE {page_num + 1}\n"
                    text += f"{'='*80}\n"
                    text += page_text + "\n"

                with open(txt_file, 'w', encoding='utf-8') as txt_f:
                    txt_f.write(text)

                print(f"✓ {pdf_file.name} -> {txt_file.name} ({len(pdf_reader.pages)} pages)")
                converted += 1

        except Exception as e:
            print(f"✗ {pdf_file.name}: {e}")
            failed += 1

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"✓ Converted: {converted}")
    print(f"✗ Failed: {failed}")
    print(f"✓ Text files location: {txt_dir}")
    print(f"✓ Original PDFs backed up in: {aips_dir}")

if __name__ == "__main__":
    convert_pdfs_to_txt()
