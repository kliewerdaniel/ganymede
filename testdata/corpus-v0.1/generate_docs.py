#!/usr/bin/env python3
"""Generate proper PDF documents for blank OCR test files.

The original DOC-009, DOC-011, DOC-013, DOC-020 are empty white PDFs.
This script generates PDFs with the text content described in corpus-facts.md.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
import os

CORPUS_DIR = "/Users/danielkliewer/Projects/ganymede/testdata/corpus-v0.1"

def create_notice_of_default():
    """DOC-009: Notice of Default and Demand for Payment"""
    filepath = os.path.join(CORPUS_DIR, "DOC-009-Notice-of-Default.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Header
    story.append(Paragraph("HENSLEY & ASSOCIATES, PLLC", styles['Title']))
    story.append(Paragraph("Attorneys at Law", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("VIA EMAIL AND CERTIFIED MAIL", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Date: January 28, 2025", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("TO:", styles['Normal']))
    story.append(Paragraph("Marcus T. Duvall", styles['Normal']))
    story.append(Paragraph("Duvall & Weber, LLP", styles['Normal']))
    story.append(Paragraph("100 Congress Avenue, Suite 1500", styles['Normal']))
    story.append(Paragraph("Austin, Texas 78701", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("RE: Notice of Default and Demand for Payment", styles['Heading2']))
    story.append(Paragraph("Our Client: Meridian Logistics Solutions, LLC", styles['Normal']))
    story.append(Paragraph("Matter: Outstanding Invoices #1044 and #1045", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Dear Mr. Duvall:", styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    body = """We represent Meridian Logistics Solutions, LLC ("Meridian") in connection with the above-referenced matter. This letter serves as formal notice of default and demand for payment pursuant to Section 9.2 of the Master Services Agreement dated March 15, 2023 (the "MSA"), as amended by Amendment No. 1 dated January 22, 2024."""
    story.append(Paragraph(body, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    body2 = """Our client has informed us that Cascade Retail Group, Inc. ("Cascade") has failed to pay Invoices #1044 ($52,300.00) and #1045 ($49,800.00), totaling $102,100.00, for services rendered under the MSA. Payment was due within thirty (30) days of invoice date. As of the date of this letter, payment has not been received."""
    story.append(Paragraph(body2, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    body3 = """Pursuant to Section 9.2 of the MSA, Cascade has fifteen (15) days from receipt of this notice to cure the default by remitting payment of $102,100.00. If Cascade fails to cure within such fifteen (15) day period, Meridian reserves the right to pursue all available remedies, including but not limited to termination of the MSA, acceleration of all amounts due, and pursuit of pre- and post-judgment interest and attorneys' fees."""
    story.append(Paragraph(body3, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    body4 = """This letter serves as formal notice that Cascade is in default under the MSA. The cure period expires on February 12, 2025."""
    story.append(Paragraph(body4, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Sincerely,", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("/s/ Victoria K. Hensley", styles['Normal']))
    story.append(Paragraph("Victoria K. Hensley", styles['Normal']))
    story.append(Paragraph("Hensley & Associates, PLLC", styles['Normal']))
    story.append(Paragraph("2200 Commerce Street, Suite 1100", styles['Normal']))
    story.append(Paragraph("Dallas, Texas 75201", styles['Normal']))
    story.append(Paragraph("Tel: (214) 555-0100", styles['Normal']))
    story.append(Paragraph("Email: vhensley@henslaw.com", styles['Normal']))
    
    doc.build(story)
    print(f"Created: {filepath}")

def create_demand_letter():
    """DOC-011: Demand Letter"""
    filepath = os.path.join(CORPUS_DIR, "DOC-011-Demand-Letter.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph("HENSLEY & ASSOCIATES, PLLC", styles['Title']))
    story.append(Paragraph("Attorneys at Law", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("VIA EMAIL AND CERTIFIED MAIL", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Date: March 3, 2025", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("TO:", styles['Normal']))
    story.append(Paragraph("Marcus T. Duvall", styles['Normal']))
    story.append(Paragraph("Duvall & Weber, LLP", styles['Normal']))
    story.append(Paragraph("100 Congress Avenue, Suite 1500", styles['Normal']))
    story.append(Paragraph("Austin, Texas 78701", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("RE: Final Demand for Payment", styles['Heading2']))
    story.append(Paragraph("Our Client: Meridian Logistics Solutions, LLC", styles['Normal']))
    story.append(Paragraph("Matter: Outstanding Invoices #1044 and #1045 — $102,100.00", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Dear Mr. Duvall:", styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    body = """This letter serves as final demand for payment of outstanding invoices totaling $102,100.00. Despite our client's prior notice dated January 28, 2025, Cascade Retail Group, Inc. has failed to remit payment or cure the default under the Master Services Agreement dated March 15, 2023 (the "MSA")."""
    story.append(Paragraph(body, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    body2 = """As of the date of this letter, the following amounts remain outstanding and due:"""
    story.append(Paragraph(body2, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    # Invoice table
    data = [['Invoice', 'Date', 'Amount'], ['#1044', 'January 10, 2025', '$52,300.00'], ['#1045', 'January 10, 2025', '$49,800.00'], ['TOTAL', '', '$102,100.00']]
    t = Table(data, colWidths=[2*inch, 2*inch, 2*inch])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
    story.append(t)
    story.append(Spacer(1, 0.1*inch))
    
    body3 = """Pursuant to Meridian's demand letter dated January 28, 2025, interest accrues on the unpaid balance at the rate of 1.5% per month (18% per annum). As of March 3, 2025, accrued interest totals approximately $1,531.50."""
    story.append(Paragraph(body3, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    body4 = """If payment in full of $102,100.00, plus accrued interest, is not received within ten (10) days of this letter, our client reserves the right to file suit and pursue all available remedies under the MSA, including pre- and post-judgment interest and attorneys' fees."""
    story.append(Paragraph(body4, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Sincerely,", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("/s/ Victoria K. Hensley", styles['Normal']))
    story.append(Paragraph("Victoria K. Hensley", styles['Normal']))
    story.append(Paragraph("Hensley & Associates, PLLC", styles['Normal']))
    
    doc.build(story)
    print(f"Created: {filepath}")

def create_deposition_notice():
    """DOC-013: Deposition Notice"""
    filepath = os.path.join(CORPUS_DIR, "DOC-013-Deposition-Notice.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph("IN THE DISTRICT COURT OF", styles['Title']))
    story.append(Paragraph("TRAVIS COUNTY, TEXAS", styles['Title']))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("MERIDIAN LOGISTICS SOLUTIONS, LLC,", styles['Normal']))
    story.append(Paragraph("Plaintiff,", styles['Normal']))
    story.append(Paragraph("v.", styles['Normal']))
    story.append(Paragraph("CASCADE RETAIL GROUP, INC.,", styles['Normal']))
    story.append(Paragraph("Defendant.", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Cause No. D-2025-00418", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("NOTICE OF ORAL DEPOSITION", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    
    body = """TO: Marcus T. Duvall, Duvall & Weber, LLP, attorneys of record for Defendant Cascade Retail Group, Inc."""
    story.append(Paragraph(body, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    body2 = """NOTICE IS HEREBY GIVEN that pursuant to the Texas Rules of Civil Procedure, Plaintiff Meridian Logistics Solutions, LLC will take the oral deposition of James Okafor, Chief Financial Officer of Cascade Retail Group, Inc., on July 22, 2025, at 10:00 a.m., at the offices of Hensley & Associates, PLLC, 2200 Commerce Street, Suite 1100, Dallas, Texas 75201."""
    story.append(Paragraph(body2, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    body3 = """The deposition will be recorded stenographically by a certified court reporter. The court reporter will be Linda M. Castellano of Reliable court reporting services. The deposition will continue from day to day until completed."""
    story.append(Paragraph(body3, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    body4 = """The deponent is requested to bring to the deposition all documents and materials in his possession, custody, or control relating to the subject matter of this litigation, including but not limited to: (1) all invoices from Meridian Logistics Solutions, LLC; (2) all correspondence regarding the Master Services Agreement dated March 15, 2023; (3) all documents regarding the Service Level Addendum; and (4) all documents relating to the approval and payment of Invoices #1044 and #1045."""
    story.append(Paragraph(body4, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Dated: June 15, 2025", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Respectfully submitted,", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("/s/ Victoria K. Hensley", styles['Normal']))
    story.append(Paragraph("Victoria K. Hensley", styles['Normal']))
    story.append(Paragraph("Hensley & Associates, PLLC", styles['Normal']))
    story.append(Paragraph("2200 Commerce Street, Suite 1100", styles['Normal']))
    story.append(Paragraph("Dallas, Texas 75201", styles['Normal']))
    story.append(Paragraph("Tel: (214) 555-0100", styles['Normal']))
    story.append(Paragraph("Email: vhensley@henslaw.com", styles['Normal']))
    story.append(Paragraph("ATTORNEYS FOR PLAINTIFF", styles['Normal']))
    
    doc.build(story)
    print(f"Created: {filepath}")

def create_docket():
    """DOC-020: Court Docket"""
    filepath = os.path.join(CORPUS_DIR, "DOC-020-Docket.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph("TRAVIS COUNTY DISTRICT COURT", styles['Title']))
    story.append(Paragraph("DOCKET EXCERPT", styles['Title']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Cause No. D-2025-00418", styles['Normal']))
    story.append(Paragraph("MERIDIAN LOGISTICS SOLUTIONS, LLC v. CASCADE RETAIL GROUP, INC.", styles['Normal']))
    story.append(Paragraph("Judge: Hon. Patricia M. Alvarez (pretrial)", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Docket entries
    data = [
        ['Date', 'Event', 'Document'],
        ['April 2, 2025', 'Plaintiff files Original Answer', 'Complaint (DOC-001)'],
        ['April 10, 2025', 'Citation served on Defendant', 'Proof of Service'],
        ['May 1, 2025', 'Defendant files Original Answer', 'Answer (DOC-002)'],
        ['May 15, 2025', 'Coordinated discovery request filed', 'Discovery Request'],
        ['June 15, 2025', 'Deposition notice served', 'Deposition Notice (DOC-013)'],
    ]
    
    t = Table(data, colWidths=[1.5*inch, 2.5*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t)
    
    doc.build(story)
    print(f"Created: {filepath}")

if __name__ == "__main__":
    create_notice_of_default()
    create_demand_letter()
    create_deposition_notice()
    create_docket()
    print("\nAll documents created successfully.")
