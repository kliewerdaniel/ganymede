# Ganymede — Adversarial Test Fixtures

"""Create adversarial test fixtures for ingestion testing.

These are synthetic, clearly labeled, and kept OUTSIDE the frozen corpus.
They test: corrupt files, duplicates, rotated pages, DOCX tables.
"""

import os
import io
import hashlib

FIXTURES_DIR = "/Users/danielkliewer/Projects/ganymede/testdata/fixtures"
os.makedirs(FIXTURES_DIR, exist_ok=True)


def create_corrupt_pdf():
    """Create a corrupt PDF file (invalid header)."""
    filepath = os.path.join(FIXTURES_DIR, "adversarial-corrupt.pdf")
    with open(filepath, "wb") as f:
        # Write garbage bytes that look like a PDF but are invalid
        f.write(b"%PDF-1.4\n")
        f.write(b"%\xe2\xe3\xcf\xd3\n")
        f.write(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        f.write(b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n")
        f.write(b"%%EOF\n")
        # Add garbage to make it corrupt
        f.write(b"\x00\x01\x02\x03\xff\xfe\xfd" * 100)
    print(f"Created: {filepath}")
    return filepath


def create_rotated_page_pdf():
    """Create a PDF with a rotated page (90 degrees)."""
    import fitz  # PyMuPDF

    filepath = os.path.join(FIXTURES_DIR, "adversarial-rotated.pdf")
    doc = fitz.open()

    # Page 1: Normal text
    page1 = doc.new_page()
    page1.insert_text((100, 100), "This is normal text on page 1.")

    # Page 2: Rotated 90 degrees
    page2 = doc.new_page()
    page2.set_rotation(90)
    page2.insert_text((100, 100), "This text is rotated 90 degrees on page 2.")

    # Page 3: Rotated 180 degrees
    page3 = doc.new_page()
    page3.set_rotation(180)
    page3.insert_text((100, 100), "This text is rotated 180 degrees on page 3.")

    doc.save(filepath)
    doc.close()
    print(f"Created: {filepath}")
    return filepath


def create_docx_with_tables():
    """Create a DOCX file with tables."""
    import docx

    filepath = os.path.join(FIXTURES_DIR, "adversarial-tables.docx")
    doc = docx.Document()

    # Add some text
    doc.add_heading("Adversarial Test Document", level=1)
    doc.add_paragraph("This document contains tables for testing.")

    # Add a table
    doc.add_heading("Table 1: Invoice Data", level=2)
    table = doc.add_table(rows=4, cols=3)
    table.style = "Table Grid"

    # Header row
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Invoice #"
    hdr_cells[1].text = "Amount"
    hdr_cells[2].text = "Date"

    # Data rows
    row1 = table.rows[1].cells
    row1[0].text = "1001"
    row1[1].text = "$5,000.00"
    row1[2].text = "2025-01-15"

    row2 = table.rows[2].cells
    row2[0].text = "1002"
    row2[1].text = "$7,500.00"
    row2[2].text = "2025-02-15"

    row3 = table.rows[3].cells
    row3[0].text = "1003"
    row3[1].text = "$3,200.00"
    row3[2].text = "2025-03-15"

    # Add another table
    doc.add_heading("Table 2: Party Information", level=2)
    table2 = doc.add_table(rows=3, cols=2)
    table2.style = "Table Grid"

    hdr2 = table2.rows[0].cells
    hdr2[0].text = "Party"
    hdr2[1].text = "Role"

    r1 = table2.rows[1].cells
    r1[0].text = "Acme Corp"
    r1[1].text = "Plaintiff"

    r2 = table2.rows[2].cells
    r2[0].text = "John Doe"
    r2[1].text = "Defendant"

    doc.save(filepath)
    print(f"Created: {filepath}")
    return filepath


def create_duplicate_file():
    """Create a duplicate of a frozen corpus file (for duplicate detection test)."""
    import shutil

    # Copy a file from Matter A
    src = "/Users/danielkliewer/Projects/ganymede/testdata/corpus-v0.1/DOC-001-Complaint.pdf"
    dst = os.path.join(FIXTURES_DIR, "adversarial-duplicate.pdf")

    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"Created: {dst} (copy of DOC-001-Complaint.pdf)")
        return dst
    else:
        print("Source file not found, creating dummy")
        with open(dst, "wb") as f:
            f.write(b"%PDF-1.4\n%test\n%%EOF\n")
        return dst


def create_oversized_file():
    """Create a file that exceeds the size limit."""
    filepath = os.path.join(FIXTURES_DIR, "adversarial-oversized.pdf")
    # Create a 101 MB file (limit is 100 MB)
    with open(filepath, "wb") as f:
        f.write(b"%PDF-1.4\n")
        # Write 101 MB of zeros
        f.write(b"\x00" * (101 * 1024 * 1024))
        f.write(b"\n%%EOF\n")
    print(f"Created: {filepath} (101 MB)")
    return filepath


def main():
    print("Creating adversarial test fixtures...")
    print(f"Output directory: {FIXTURES_DIR}\n")

    create_corrupt_pdf()
    create_rotated_page_pdf()
    create_docx_with_tables()
    create_duplicate_file()
    # create_oversized_file()  # Uncomment to test size limits (slow)

    print(f"\nFixtures created in: {FIXTURES_DIR}")
    print("These files are NOT part of the frozen corpus.")


if __name__ == "__main__":
    main()
