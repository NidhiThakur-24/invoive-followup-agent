"""
main.py
Invoice Follow-up Agent: Multi-Agent Orchestrator
Coordinates three specialized agents:
  1. Extractor (extractor.py): Ingests invoices and extracts structured data using Gemini.
  2. Tracker   (tracker.py)  : Stores in SQLite, flags overdue accounts, and calculates aging.
  3. Reminder  (reminder.py) : Uses Gemini to draft tone-escalated reminder emails.

Saves all drafted reminders to 'reminders.md' (DRAFTS ONLY - no emails are sent).
"""

import os
import sys
from datetime import datetime
from typing import Dict, List

# Configure UTF-8 for console output on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from extractor import extract_all_invoices
from tracker import (
    display_invoices_table,
    get_all_invoices,
    get_overdue_invoices,
    init_db,
    save_or_update_invoices,
)
from reminder import draft_all_reminders

REMINDERS_MD_PATH = os.path.join(os.path.dirname(__file__), "reminders.md")


def format_reminders_markdown(drafts: List[Dict], all_invoices: List[Dict]) -> str:
    """Formats the drafted reminder emails and pipeline statistics into clean Markdown."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total_tracked = len(all_invoices)
    paid_count = sum(1 for inv in all_invoices if inv["status"] == "paid")
    pending_count = sum(1 for inv in all_invoices if inv["status"] == "pending")
    overdue_count = sum(1 for inv in all_invoices if inv["status"] == "overdue")
    overdue_total_amt = sum(inv["amount"] for inv in all_invoices if inv["status"] == "overdue")

    md = []
    md.append("# 📬 Invoice Follow-up Agent — Drafted Payment Reminders")
    md.append("")
    md.append(f"> **Generated at:** `{now_str}`  ")
    md.append("> **Status:** **DRAFTS ONLY** — No emails have been sent. Review drafts below before transmission.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 📊 Accounts Receivable Portfolio Summary")
    md.append("")
    md.append("| Metric | Count / Amount |")
    md.append("| :--- | :--- |")
    md.append(f"| **Total Tracked Invoices** | `{total_tracked}` |")
    md.append(f"| **Pending (Upcoming)** | `{pending_count}` |")
    md.append(f"| **Paid / Settled** | `{paid_count}` |")
    md.append(f"| **Overdue Invoices** | **`{overdue_count}`** |")
    md.append(f"| **Total Overdue Balance** | **₹{overdue_total_amt:,.2f} INR** |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 📑 Overview of Drafted Reminders")
    md.append("")

    if not drafts:
        md.append("🎉 *No overdue invoices found! All accounts are currently paid or within their payment terms.*")
        md.append("")
        return "\n".join(md)

    md.append("| Invoice # | Client Name | Email | Amount | Due Date | Overdue | Escalation Tier |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for d in drafts:
        amt_str = f"₹{d['amount']:,.0f} {d.get('currency', 'INR')}"
        md.append(
            f"| `{d['invoice_number']}` | **{d['client_name']}** | `{d['client_email']}` | "
            f"{amt_str} | {d['due_date']} | `{d['days_overdue']} days` | *{d['escalation_tier']}* |"
        )
    md.append("")
    md.append("---")
    md.append("")
    md.append("## ✉️ Drafted Email Messages")
    md.append("")

    for i, d in enumerate(drafts, 1):
        md.append(f"### {i}. `{d['invoice_number']}` — {d['client_name']}")
        md.append("")
        md.append(f"- **To:** `{d['client_email']}`")
        md.append(f"- **Escalation Tier:** **{d['escalation_tier']}** (`{d['days_overdue']} days overdue`)")
        md.append(f"- **Amount Outstanding:** ₹{d['amount']:,.2f} {d.get('currency', 'INR')}")
        md.append(f"- **Due Date:** {d['due_date']}")
        md.append(f"- **Subject Line:** `{d['subject']}`")
        md.append("")
        md.append("**Email Body:**")
        md.append("")
        # Format body inside blockquote
        body_lines = d["body"].strip().splitlines()
        quoted_body = "\n".join(f"> {line}" if line.strip() else ">" for line in body_lines)
        md.append(quoted_body)
        md.append("")
        md.append("---")
        md.append("")

    return "\n".join(md)


def run_pipeline():
    """Executes the end-to-end multi-agent follow-up system."""
    print("=" * 75)
    print("🚀 INVOICE FOLLOW-UP AGENT — AUTONOMOUS MULTI-AGENT SYSTEM")
    print("=" * 75)
    print("Agents: [1] Extractor (Gemini) -> [2] Tracker (SQLite) -> [3] Reminder (Gemini)\n")

    # Step 1: Agent 1 - Extractor
    print("-" * 75)
    print("STEP 1: AGENT 1 (EXTRACTOR) — Ingesting & Validating Invoices")
    print("-" * 75)
    try:
        extracted = extract_all_invoices()
    except Exception as e:
        print(f"Extraction failed: {e}")
        return

    if not extracted:
        print("No invoices extracted. Exiting.")
        return

    print(f"\n✓ Successfully extracted & Pydantic-validated {len(extracted)} invoices.")

    # Step 2: Agent 2 - Tracker
    print("\n" + "-" * 75)
    print("STEP 2: AGENT 2 (TRACKER) — Updating SQLite Database & Aging")
    print("-" * 75)
    init_db()
    stats = save_or_update_invoices(extracted)
    print(f"✓ SQLite database updated: {stats['inserted']} new, {stats['updated']} updated.")
    print(f"  Summary: {stats['pending']} Pending | {stats['overdue']} Overdue | {stats['paid']} Paid\n")

    all_invoices = get_all_invoices()
    display_invoices_table(all_invoices)

    # Step 3: Fetch overdue invoices
    overdue_invoices = get_overdue_invoices()
    print(f"\nFound {len(overdue_invoices)} overdue invoices requiring follow-up.")

    # Step 4: Agent 3 - Reminder
    print("\n" + "-" * 75)
    print("STEP 3: AGENT 3 (REMINDER) — Generating Tone-Escalated Drafts")
    print("-" * 75)
    drafts = draft_all_reminders(overdue_invoices)
    print(f"\n✓ Successfully drafted {len(drafts)} reminder emails.")

    # Step 5: Save to reminders.md
    print("\n" + "-" * 75)
    print("STEP 4: SAVING DRAFTS — Generating reminders.md")
    print("-" * 75)
    markdown_content = format_reminders_markdown(drafts, all_invoices)
    with open(REMINDERS_MD_PATH, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"✓ All drafted reminder emails written to:")
    print(f"  --> {REMINDERS_MD_PATH}")
    print("\n⚠️  NOTE: No emails were sent. All generated communications are stored as drafts.")
    print(f"💡 TIP: To mark an invoice as paid, run: python tracker.py --pay <INVOICE_NUMBER>")
    print("=" * 75)
    print("🏁 PIPELINE EXECUTION COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    run_pipeline()
