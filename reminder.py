"""
reminder.py
Agent 3: Payment Reminder Email Drafter
Drafts personalized payment reminder emails using Google Gemini API (google-generativeai).
Escalates tone automatically based on days overdue:
  - 1 to 7 days  : Friendly reminder
  - 8 to 21 days : Firm but polite
  - > 21 days    : Formal final notice
Always includes invoice number, amount, due date, and client details.
"""

import json
import os
import sys
from typing import Dict, List, Optional

import dotenv
import google.generativeai as genai

# Configure UTF-8 for console output on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

dotenv.load_dotenv()

# Candidate models ordered by stability and availability
CANDIDATE_MODELS = [
    os.getenv("GEMINI_MODEL", "").strip(),
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-flash-latest",
]
CANDIDATE_MODELS = [m for m in CANDIDATE_MODELS if m]
DEFAULT_MODEL = CANDIDATE_MODELS[0] if CANDIDATE_MODELS else "gemini-3.1-flash-lite"


def configure_gemini():
    """Configures the Gemini API client using GEMINI_API_KEY from environment."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found in environment or .env file. "
            "Please add your API key to .env."
        )
    genai.configure(api_key=api_key)


def get_escalation_tier(days_overdue: int) -> tuple[str, str]:
    """
    Returns the tone tier label and specific guidance for Gemini.
    """
    if days_overdue <= 7:
        tier_label = "Friendly Reminder (1-7 days overdue)"
        instructions = (
            "Tone: Warm, friendly, polite, and helpful.\n"
            "Guidance: Assume this was a simple oversight or busy schedule. Express appreciation "
            "for their ongoing partnership. Politely inquire if they need any assistance, an updated invoice copy, "
            "or confirmation of bank details."
        )
    elif days_overdue <= 21:
        tier_label = "Firm but Polite Reminder (8-21 days overdue)"
        instructions = (
            "Tone: Professional, direct, firm yet respectful.\n"
            "Guidance: Clearly state that the invoice is now overdue by the specified number of days. "
            "Reference that previous payment terms have elapsed and request an immediate confirmation "
            "of the payment transfer or an expected date of payment."
        )
    else:
        tier_label = "Formal Final Notice (>21 days overdue)"
        instructions = (
            "Tone: Formal, urgent, assertive, and serious.\n"
            "Guidance: This is a critical final notice. Highlight that the account is severely past due. "
            "Request immediate remittance within 48 to 72 hours to avoid potential suspension of services, "
            "late fees, or further administrative escalation. Provide clear payment settlement urgency."
        )
    return tier_label, instructions


import time

def draft_reminder_email(invoice: Dict, model_name: Optional[str] = None) -> Dict:
    """
    Uses Gemini to draft a single payment reminder email for an overdue invoice.
    Attempts fallback across candidate models if rate limits or unavailability occurs.
    """
    configure_gemini()

    inv_num = invoice["invoice_number"]
    client_name = invoice["client_name"]
    client_email = invoice["client_email"]
    amount = invoice["amount"]
    currency = invoice.get("currency", "INR")
    due_date = invoice["due_date"]
    days_overdue = int(invoice.get("days_overdue", 0))

    tier_label, tone_instructions = get_escalation_tier(days_overdue)

    prompt = f"""
You are an expert accounts receivable and business communications specialist for Indian B2B companies.
Draft a professional payment reminder email to a client for an overdue invoice.

INVOICE DETAILS:
- Client Name    : {client_name}
- Client Email   : {client_email}
- Invoice Number : {inv_num}
- Total Amount   : ₹{amount:,.2f} {currency}
- Due Date       : {due_date}
- Days Overdue   : {days_overdue} days

ESCALATION TIER:
{tier_label}

TONE AND STYLE INSTRUCTIONS:
{tone_instructions}

MANDATORY REQUIREMENTS:
1. You MUST explicitly state the Invoice Number ({inv_num}), the Total Amount (₹{amount:,.2f} {currency}), and the Due Date ({due_date}).
2. Include a compelling, clear Subject line appropriate for the escalation tier.
3. Keep the email concise, professional, and natural for Indian corporate communication.
4. Conclude with a placeholder sign-off for Finance & Accounts Team.

Return your response as a valid JSON object with EXACTLY two keys:
{{
  "subject": "The drafted email subject line",
  "body": "The complete drafted email body text"
}}
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
            resp_text = response.text.strip()

            # Strip markdown fences if present
            if resp_text.startswith("```"):
                lines = resp_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                resp_text = "\n".join(lines).strip()

            parsed = json.loads(resp_text)

            return {
                "invoice_number": inv_num,
                "client_name": client_name,
                "client_email": client_email,
                "amount": amount,
                "currency": currency,
                "due_date": due_date,
                "days_overdue": days_overdue,
                "escalation_tier": tier_label,
                "subject": parsed.get("subject", f"Payment Reminder: Invoice {inv_num}"),
                "body": parsed.get("body", ""),
            }
        except Exception as e:
            last_err = e
            # If rate limited, sleep briefly before trying fallback
            time.sleep(2)
            continue

    raise RuntimeError(f"All candidate models failed for invoice {inv_num}. Last error: {last_err}")


def draft_all_reminders(overdue_invoices: List[Dict], model_name: Optional[str] = None) -> List[Dict]:
    """
    Drafts payment reminders for all overdue invoices.
    """
    if not overdue_invoices:
        print("No overdue invoices to process.")
        return []

    print(f"\nAgent 3 (Reminder): Drafting payment reminders for {len(overdue_invoices)} overdue invoices...")
    drafts = []

    for i, inv in enumerate(overdue_invoices):
        inv_num = inv["invoice_number"]
        days = inv.get("days_overdue", 0)
        tier_label, _ = get_escalation_tier(days)
        print(f" -> Drafting for {inv_num} ({inv['client_name']}) | Overdue: {days}d | Tier: {tier_label}...", end=" ", flush=True)
        try:
            draft = draft_reminder_email(inv, model_name=model_name)
            drafts.append(draft)
            print("✓ Drafted")
        except Exception as e:
            print(f"✗ Failed: {e}")

        # Add brief pause between calls to respect rate limits
        if i < len(overdue_invoices) - 1:
            time.sleep(2)

    return drafts


if __name__ == "__main__":
    from tracker import get_overdue_invoices

    overdue = get_overdue_invoices()
    print(f"Found {len(overdue)} overdue invoices in database.")
    drafts = draft_all_reminders(overdue)
    for d in drafts:
        print("\n" + "=" * 70)
        print(f"INVOICE       : {d['invoice_number']} ({d['client_name']})")
        print(f"RECIPIENT     : {d['client_email']}")
        print(f"TIER          : {d['escalation_tier']}")
        print(f"SUBJECT       : {d['subject']}")
        print("-" * 70)
        print(d["body"])
