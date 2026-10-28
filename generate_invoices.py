"""
generate_invoices.py
Generates 6 realistic fake invoices for Indian small businesses in INR (₹).
Includes a mix of upcoming, overdue (friendly, firm, final notice buckets), and paid invoices.
"""

import os
import sys
from datetime import date, timedelta

# Ensure UTF-8 output on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

INVOICES_DIR = os.path.join(os.path.dirname(__file__), "invoices")

def get_sample_invoices():
    today = date.today()
    
    invoices = [
        {
            "filename": "INV-2026-001.txt",
            "invoice_number": "INV-2026-001",
            "vendor_name": "NovaTech Digital Solutions Pvt Ltd",
            "vendor_address": "402, 5th Block, Koramangala, Bengaluru, Karnataka 560034",
            "vendor_gstin": "29AABCU9603R1ZM",
            "client_name": "Shanti Silk Emporium",
            "client_email": "accounts@shantisilk.in",
            "client_address": "Shop 14-16, Textile Market Ring Road, Surat, Gujarat 395002",
            "issue_date": (today - timedelta(days=20)).strftime("%Y-%m-%d"),
            "due_date": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
            "status_note": "Payment Pending - Due in 10 days",
            "items": [
                ("E-Commerce Portal Maintenance & Cloud Hosting (Quarterly)", 1, 30000, 30000),
                ("Payment Gateway Integration & SSL Setup", 1, 15000, 15000),
            ],
            "subtotal": 45000,
            "tax_rate": "18% GST (CGST 9% + SGST 9%)",
            "tax_amount": 8100,
            "total_amount": 53100,
            "currency": "INR",
            "bank_details": "HDFC Bank | A/C: 50200034891102 | IFSC: HDFC0000523",
        },
        {
            "filename": "INV-2026-002.txt",
            "invoice_number": "INV-2026-002",
            "vendor_name": "CloudKite Systems & Services",
            "vendor_address": "Office 12B, Cyber City, Magarpatta, Pune, Maharashtra 411028",
            "vendor_gstin": "27AAECK1298P1ZX",
            "client_name": "Deshmukh Logistics Pvt Ltd",
            "client_email": "billing@deshmukhlogistics.com",
            "client_address": "Plot 88, Sector 19A, Vashi, Navi Mumbai, Maharashtra 400703",
            "issue_date": (today - timedelta(days=35)).strftime("%Y-%m-%d"),
            "due_date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
            "status_note": "OVERDUE (5 days past due)",
            "items": [
                ("Fleet Tracking FleetOps API Integration", 1, 65000, 65000),
                ("Dedicated Server Infrastructure & Backup Setup", 1, 35000, 35000),
            ],
            "subtotal": 100000,
            "tax_rate": "18% GST (IGST 18%)",
            "tax_amount": 18000,
            "total_amount": 118000,
            "currency": "INR",
            "bank_details": "ICICI Bank | A/C: 004705012398 | IFSC: ICIC0000047",
        },
        {
            "filename": "INV-2026-003.txt",
            "invoice_number": "INV-2026-003",
            "vendor_name": "PixelCraft Media & Marketing",
            "vendor_address": "Level 3, Golf Course Extension Road, Gurugram, Haryana 122018",
            "vendor_gstin": "06AABCP7741K1ZT",
            "client_name": "ChaiShala Franchises India",
            "client_email": "finance@chaishala.co.in",
            "client_address": "Flat 3A, Connaught Place Outer Circle, New Delhi 110001",
            "issue_date": (today - timedelta(days=46)).strftime("%Y-%m-%d"),
            "due_date": (today - timedelta(days=16)).strftime("%Y-%m-%d"),
            "status_note": "OVERDUE (16 days past due)",
            "items": [
                ("Social Media Brand Campaign & Festive Ad Creatives", 1, 45000, 45000),
                ("Local Search Engine Optimization & Store Locator Setup", 1, 20000, 20000),
            ],
            "subtotal": 65000,
            "tax_rate": "18% GST (IGST 18%)",
            "tax_amount": 11700,
            "total_amount": 76700,
            "currency": "INR",
            "bank_details": "Axis Bank | A/C: 918020045612398 | IFSC: UTIB0000214",
        },
        {
            "filename": "INV-2026-004.txt",
            "invoice_number": "INV-2026-004",
            "vendor_name": "Bharat Industrial Systems LLP",
            "vendor_address": "Phase II, Guindy Industrial Estate, Chennai, Tamil Nadu 600032",
            "vendor_gstin": "33AAJFB4521M1ZN",
            "client_name": "Surya Solar Renewable Ltd",
            "client_email": "payments@suryasolar.in",
            "client_address": "Avinashi Road, Peelamedu, Coimbatore, Tamil Nadu 641004",
            "issue_date": (today - timedelta(days=62)).strftime("%Y-%m-%d"),
            "due_date": (today - timedelta(days=32)).strftime("%Y-%m-%d"),
            "status_note": "CRITICAL OVERDUE (32 days past due - Final Warning)",
            "items": [
                ("Industrial Solar Inverter Monitoring Hardware (4 Units)", 4, 38000, 152000),
                ("On-site Sensor Calibration & Commissioning Services", 1, 48000, 48000),
            ],
            "subtotal": 200000,
            "tax_rate": "18% GST (CGST 9% + SGST 9%)",
            "tax_amount": 36000,
            "total_amount": 236000,
            "currency": "INR",
            "bank_details": "State Bank of India | A/C: 38920144521 | IFSC: SBIN0001856",
        },
        {
            "filename": "INV-2026-005.txt",
            "invoice_number": "INV-2026-005",
            "vendor_name": "FinTrack Business Advisory LLP",
            "vendor_address": "B-Wing, Mondeal Heights, SG Highway, Ahmedabad, Gujarat 380015",
            "vendor_gstin": "24AAOFF6312L1ZP",
            "client_name": "Anand Steel Fabrication",
            "client_email": "accounts@anandsteel.com",
            "client_address": "GIDC Lodhika Industrial Area, Metoda, Rajkot, Gujarat 360021",
            "issue_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
            "due_date": (today + timedelta(days=20)).strftime("%Y-%m-%d"),
            "status_note": "Payment Pending - Due in 20 days",
            "items": [
                ("ERP Tally Cloud Migration & Annual Maintenance Contract", 1, 55000, 55000),
                ("Corporate GST Audit Filing Assistance", 1, 20000, 20000),
            ],
            "subtotal": 75000,
            "tax_rate": "18% GST (CGST 9% + SGST 9%)",
            "tax_amount": 13500,
            "total_amount": 88500,
            "currency": "INR",
            "bank_details": "Kotak Mahindra Bank | A/C: 2811440932 | IFSC: KKBK0000812",
        },
        {
            "filename": "INV-2026-006.txt",
            "invoice_number": "INV-2026-006",
            "vendor_name": "Vani Creative Agency",
            "vendor_address": "Road No. 36, Jubilee Hills, Hyderabad, Telangana 500033",
            "vendor_gstin": "36AAQFV8901N1ZY",
            "client_name": "Royal Spices Exports",
            "client_email": "info@royalspicesexports.com",
            "client_address": "Willingdon Island Port Area, Kochi, Kerala 682003",
            "issue_date": (today - timedelta(days=40)).strftime("%Y-%m-%d"),
            "due_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
            "status_note": f"PAID - Received in full on {(today - timedelta(days=3)).strftime('%Y-%m-%d')} via NEFT Ref: N1029481726",
            "items": [
                ("Export Packaging Label Redesign & Multilingual Translation", 1, 35000, 35000),
                ("Product Catalog Photography & High-res Retouching", 1, 15000, 15000),
            ],
            "subtotal": 50000,
            "tax_rate": "18% GST (IGST 18%)",
            "tax_amount": 9000,
            "total_amount": 59000,
            "currency": "INR",
            "bank_details": "HDFC Bank | A/C: 50100234199841 | IFSC: HDFC0001629",
        },
    ]
    return invoices


def render_invoice_text(inv: dict) -> str:
    item_rows = []
    for desc, qty, rate, amt in inv["items"]:
        item_rows.append(f"  - {desc:<60} | Qty: {qty} | Rate: ₹{rate:>7,d} | Amt: ₹{amt:>8,d}")
    item_lines = "\n".join(item_rows)
    
    content = f"""================================================================================
TAX INVOICE - {inv['vendor_name'].upper()}
================================================================================
Vendor Details:
  Company: {inv['vendor_name']}
  Address: {inv['vendor_address']}
  GSTIN:   {inv['vendor_gstin']}

--------------------------------------------------------------------------------
INVOICE DETAILS:
  Invoice Number : {inv['invoice_number']}
  Issue Date     : {inv['issue_date']}
  Due Date       : {inv['due_date']}
  Currency       : {inv['currency']} (Indian Rupee - ₹)
  Status / Note  : {inv['status_note']}

BILLED TO (CLIENT):
  Client Name    : {inv['client_name']}
  Client Email   : {inv['client_email']}
  Client Address : {inv['client_address']}
--------------------------------------------------------------------------------
LINE ITEMS:
{item_lines}
--------------------------------------------------------------------------------
FINANCIAL SUMMARY:
  Subtotal       : ₹{inv['subtotal']:,d}
  Tax Details    : {inv['tax_rate']} -> ₹{inv['tax_amount']:,d}
  TOTAL AMOUNT   : ₹{inv['total_amount']:,d} {inv['currency']}
--------------------------------------------------------------------------------
REMITTANCE INSTRUCTIONS:
  Please transfer funds directly to:
  {inv['bank_details']}
  Kindly email payment confirmation to accounts@{inv['vendor_name'].split()[0].lower()}.com

Thank you for your business!
================================================================================
"""
    return content


def generate_all_invoices():
    os.makedirs(INVOICES_DIR, exist_ok=True)
    invoices = get_sample_invoices()
    
    print(f"Generating {len(invoices)} realistic Indian business invoices in: {INVOICES_DIR}\n")
    for inv in invoices:
        file_path = os.path.join(INVOICES_DIR, inv["filename"])
        content = render_invoice_text(inv)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f" [+] Created: {inv['filename']}")
        print(f"     Client   : {inv['client_name']} ({inv['client_email']})")
        print(f"     Amount   : ₹{inv['total_amount']:,d} {inv['currency']}")
        print(f"     Due Date : {inv['due_date']} ({inv['status_note']})")
        print("-" * 60)

    print("\nAll 6 invoices generated successfully!")


if __name__ == "__main__":
    generate_all_invoices()
