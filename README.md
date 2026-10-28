# 🧾 Invoice Follow-up Agent

> An autonomous multi-agent system designed for small businesses to streamline accounts receivable: extracting invoice data with Google Gemini, tracking due dates and aging in SQLite, and drafting intelligent, tone-escalated payment reminders.

Built with **Python**, **Google Gemini API**, **Pydantic**, and **SQLite** — without heavy frameworks like LangChain or CrewAI.

---

## 🌟 Features

- **🤖 Three-Agent Architecture**: Clean separation of concerns into independent, composable Python agents (`extractor.py`, `tracker.py`, `reminder.py`).
- **📄 Multi-Format Ingestion**: Ingests both plain text (`.txt`) and PDF invoices from the `invoices/` directory.
- **🛡️ Pydantic Type Safety**: Every extracted invoice is validated against a strict Pydantic schema (`InvoiceSchema`) ensuring valid dates, positive amounts, and clean currency formats.
- **💾 Local SQLite Persistence**: Stores invoice status (`pending`, `paid`, `overdue`), calculates days overdue dynamically, and preserves manual payment entries.
- **📈 Tiered Tone Escalation**: Email reminders intelligently adjust their tone based on the days overdue:
  - **1 to 7 days**: Warm, friendly reminder assuming an innocent oversight.
  - **8 to 21 days**: Firm but polite notice requesting immediate settlement or date of transfer.
  - **> 21 days**: Formal final notice highlighting urgent settlement to prevent service disruption or escalation.
- **🔒 Safety-First (Drafts Only)**: Drafts are written to `reminders.md` for human review before sending. No emails are transmitted automatically.
- **🇮🇳 Localized for Indian B2B**: Ready-to-test sample invoices formatted in Indian Rupees (₹ INR) with GST rates, GSTINs, and realistic Indian B2B vendor/client profiles.

---

## 🏗️ Architecture

```
                       +-----------------------+
                       |   /invoices Folder    |
                       |  (Text / PDF Files)   |
                       +-----------+-----------+
                                   |
                                   v
+--------------------------------------------------------------------+
| Agent 1: EXTRACTOR (extractor.py)                                  |
| - Reads invoice files                                              |
| - Prompts Gemini API (google-generativeai) for structured JSON    |
| - Validates fields with Pydantic (client, email, amount, dates)    |
+----------------------------------+---------------------------------+
                                   |
                                   v
+--------------------------------------------------------------------+
| Agent 2: TRACKER (tracker.py)                                      |
| - Stores invoices in local SQLite DB (invoices.db)                 |
| - Computes days_overdue against today's date                       |
| - Flags status: 'pending', 'paid', 'overdue'                       |
| - CLI command to mark an invoice as paid (--pay)                   |
+----------------------------------+---------------------------------+
                                   |
                                   v
+--------------------------------------------------------------------+
| Agent 3: REMINDER (reminder.py)                                    |
| - Filters overdue invoices                                         |
| - Uses Gemini to draft contextual email reminders                  |
| - Escalates tone: Friendly -> Firm -> Formal Final Notice          |
+----------------------------------+---------------------------------+
                                   |
                                   v
                       +-----------------------+
                       |     reminders.md      |
                       | (Human Review Drafts) |
                       +-----------------------+
```

---

## 🚦 Escalation Tone Matrix

| Tier | Days Overdue | Tone | Goal & Content |
| :--- | :--- | :--- | :--- |
| **Tier 1** | **1 – 7 days** | Friendly & Warm | Assumes a busy schedule or minor oversight; politely provides invoice details and offers support. |
| **Tier 2** | **8 – 21 days** | Firm but Polite | States clearly that payment terms have passed; requests immediate payment or a confirmed transfer date. |
| **Tier 3** | **> 21 days** | Formal Final Notice | Urgent demand for payment within 48–72 hours; warns of service suspension and escalation. |

---

## 📁 Project Structure

```text
invoice_agent/
├── .env                  # Environment variables (GEMINI_API_KEY, GEMINI_MODEL)
├── .env.example          # Sample environment configuration template
├── requirements.txt      # Python dependencies
├── generate_invoices.py  # Script generating 6 realistic fake Indian invoices in INR
├── extractor.py          # Agent 1: Ingestion & Pydantic extraction using Gemini
├── tracker.py            # Agent 2: SQLite database & overdue status tracker
├── reminder.py           # Agent 3: Tone-escalated payment reminder email drafter
├── main.py               # Multi-agent pipeline orchestrator
├── reminders.md          # Output artifact containing all drafted reminder emails
└── invoices/             # Invoice repository folder (.txt and .pdf)
    ├── INV-2026-001.txt  # Pending (Due in 10 days)
    ├── INV-2026-002.txt  # Overdue (5 days -> Tier 1 Friendly)
    ├── INV-2026-003.txt  # Overdue (16 days -> Tier 2 Firm)
    ├── INV-2026-004.txt  # Overdue (32 days -> Tier 3 Final Notice)
    ├── INV-2026-005.txt  # Pending (Due in 20 days)
    └── INV-2026-006.txt  # Paid (Payment settled via NEFT)
```

---

## 🚀 Quickstart Guide

### 1. Clone & Set Up Environment

```bash
cd invoice_agent

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Your Gemini API Key

Copy `.env.example` to `.env` and add your Gemini API key (from [Google AI Studio](https://aistudio.google.com/app/apikey)):

```env
GEMINI_API_KEY=your_actual_gemini_api_key
```

*(Optional: Set `GEMINI_MODEL=gemini-3.1-flash-lite` or leave default for automatic multi-model fallback).*

### 3. Generate Realistic Sample Invoices

Run the invoice generator to populate `/invoices` with 6 Indian business invoices:

```bash
python generate_invoices.py
```

### 4. Run the Full Multi-Agent Pipeline

Execute all three agents with a single command:

```bash
python main.py
```

This will:
1. Extract invoice fields via **Extractor Agent**.
2. Update **Tracker Agent** SQLite database (`invoices.db`) and compute aging.
3. Identify overdue accounts.
4. Draft personalized reminder emails via **Reminder Agent**.
5. Save all drafts into **`reminders.md`**.

---

## 🛠️ CLI Operations & Individual Agent Usage

### Inspect the Invoices Database

```bash
python tracker.py --list
```

### Mark an Invoice as Paid

When a client pays an overdue bill, mark it as paid so reminders are no longer drafted:

```bash
python tracker.py --pay INV-2026-002
```

### Run Agents Individually

- **Test Extractor Agent only**:
  ```bash
  python extractor.py
  ```
- **Test Reminder Agent only** (drafts for current overdue DB rows):
  ```bash
  python reminder.py
  ```

---

## 💡 Why Zero-Framework Multi-Agent?

Many modern AI agent tutorials introduce heavyweight frameworks like LangChain, LangGraph, or CrewAI for tasks that are fundamentally sequential pipelines. This project demonstrates that **plain, well-structured Python functions with Pydantic and standard SQLite**:
- Are **10x faster to debug and trace**.
- Have **zero dependency bloat or breaking API churn**.
- Provide **100% deterministic control** over prompts, rate limits, and fallback retries.
- Are immediately ready for production deployment as serverless cloud functions or lightweight cron jobs.
