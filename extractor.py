"""
extractor.py
Agent 1: Invoice Data Extractor
Reads invoices (text or PDF) from the invoices/ folder, calls Google Gemini API (google-generativeai),
extracts key fields into structured JSON, and validates with Pydantic.
"""

import json
import os
import re
import sys
from datetime import date
from typing import List, Optional

import dotenv
from pydantic import BaseModel, EmailStr, Field, field_validator
import google.generativeai as genai
from pypdf import PdfReader

# Configure UTF-8 for console output on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load environment variables
dotenv.load_dotenv()

CANDIDATE_MODELS = [
    os.getenv("GEMINI_MODEL", "").strip(),
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-flash-latest",
]
CANDIDATE_MODELS = [m for m in CANDIDATE_MODELS if m]
DEFAULT_MODEL = CANDIDATE_MODELS[0] if CANDIDATE_MODELS else "gemini-3.1-flash-lite"
INVOICES_DIR = os.path.join(os.path.dirname(__file__), "invoices")


class InvoiceSchema(BaseModel):
    """Pydantic model to validate extracted invoice data."""
    client_name: str = Field(..., description="Name of the client or billed company")
    client_email: str = Field(..., description="Email address of the client")
    invoice_number: str = Field(..., description="Unique invoice identifier, e.g. INV-2026-001")
    amount: float = Field(..., description="Total invoice amount as a numeric float")
    currency: str = Field(..., description="Currency code or symbol, e.g. INR or Rs")
    issue_date: str = Field(..., description="Date of issue in YYYY-MM-DD format")
    due_date: str = Field(..., description="Payment due date in YYYY-MM-DD format")
    is_paid: bool = Field(default=False, description="Whether the invoice explicitly states it is paid/cleared")
    source_file: Optional[str] = Field(default=None, description="Filename of the source invoice")

    @field_validator("issue_date", "due_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        # Validate or normalize to YYYY-MM-DD
        v = v.strip()
        match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", v)
        if match:
            year, month, day = match.groups()
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        return v

    @field_validator("amount", mode="before")
    @classmethod
    def clean_amount(cls, v):
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            # Strip currency symbols, commas, and spaces
            cleaned = re.sub(r"[^\d.]", "", v)
            return float(cleaned) if cleaned else 0.0
        return v


def configure_gemini():
    """Configures the Gemini API client using the GEMINI_API_KEY from environment."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found in environment or .env file. "
            "Please add your API key to .env."
        )
    genai.configure(api_key=api_key)


def read_invoice_file(file_path: str) -> str:
    """Reads raw text from either a .txt or .pdf file."""
    _, ext = os.path.splitext(file_path.lower())
    if ext == ".pdf":
        reader = PdfReader(file_path)
        pages_text = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                pages_text.append(extracted)
        return "\n".join(pages_text)
    else:
        # Default text file reader
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()


import time

def extract_invoice_data(file_path: str, model_name: Optional[str] = None) -> InvoiceSchema:
    """
    Extracts structured invoice details using Gemini and validates with Pydantic.
    Attempts fallback across candidate models if rate limits occur.
    """
    configure_gemini()
    raw_text = read_invoice_file(file_path)
    filename = os.path.basename(file_path)

    prompt = f"""
You are an expert financial document extractor.
Extract the key invoice fields from the following invoice document.

Return ONLY a valid JSON object with EXACTLY these keys:
- "client_name": string (the name of the billed company or individual client)
- "client_email": string (the email address of the client)
- "invoice_number": string (e.g., INV-2026-001)
- "amount": number (the total final amount payable, e.g. 53100)
- "currency": string (e.g., "INR" or "₹")
- "issue_date": string in "YYYY-MM-DD" format
- "due_date": string in "YYYY-MM-DD" format
- "is_paid": boolean (true if the invoice explicitly mentions PAID or payment received, otherwise false)

Invoice Document:
\"\"\"
{raw_text}
\"\"\"
"""

    models_to_try = [model_name] if model_name else CANDIDATE_MODELS
    last_err = None

    for m in models_to_try:
        try:
            model = genai.GenerativeModel(
                model_name=m,
                generation_config={"response_mime_type": "application/json"}
            )
            response = model.generate_content(prompt)
            response_text = response.text.strip()

            # Strip code block fences if present
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                response_text = "\n".join(lines).strip()

            parsed_json = json.loads(response_text)
            parsed_json["source_file"] = filename

            # Validate against Pydantic schema
            validated_data = InvoiceSchema(**parsed_json)
            return validated_data
        except Exception as e:
            last_err = e
            time.sleep(2)
            continue

    raise RuntimeError(f"All candidate models failed for {filename}. Last error: {last_err}")


def extract_all_invoices(folder_path: str = INVOICES_DIR, model_name: Optional[str] = None) -> List[InvoiceSchema]:
    """
    Extracts and validates all invoices found in the specified folder.
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Invoices folder not found at: {folder_path}")

    files = [
        f for f in os.listdir(folder_path)
        if f.lower().endswith((".txt", ".pdf", ".text"))
    ]
    files.sort()

    if not files:
        print(f"No invoice files found in {folder_path}")
        return []

    print(f"Agent 1 (Extractor): Processing {len(files)} invoices from '{folder_path}' using Gemini...")
    extracted_invoices: List[InvoiceSchema] = []

    for i, f in enumerate(files):
        full_path = os.path.join(folder_path, f)
        print(f" -> Extracting: {f}...", end=" ", flush=True)
        try:
            invoice_data = extract_invoice_data(full_path, model_name=model_name)
            extracted_invoices.append(invoice_data)
            status_desc = "PAID" if invoice_data.is_paid else f"Due: {invoice_data.due_date}"
            print(f"✓ Validated [{invoice_data.invoice_number} | {invoice_data.client_name} | {invoice_data.currency} {invoice_data.amount:,.2f} | {status_desc}]")
        except Exception as e:
            print(f"✗ Failed: {e}")

        if i < len(files) - 1:
            time.sleep(2)

    return extracted_invoices


if __name__ == "__main__":
    results = extract_all_invoices()
    print(f"\nExtracted & validated {len(results)} invoices successfully.\n")
    for r in results:
        print(r.model_dump_json(indent=2))
