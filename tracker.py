"""
tracker.py
Agent 2: Invoice Status Tracker & SQLite Database
Stores extracted invoices in a local SQLite database, calculates days overdue,
updates statuses (pending, paid, overdue), and provides helper functions to mark invoices as paid.
"""

import os
import sqlite3
import sys
from datetime import date, datetime
from typing import Dict, List, Optional, Union

# Configure UTF-8 for console output on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DB_PATH = os.path.join(os.path.dirname(__file__), "invoices.db")


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Returns a SQLite connection with dict-like row access."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Initializes the SQLite invoices table if not already created."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_number TEXT PRIMARY KEY,
                client_name TEXT NOT NULL,
                client_email TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('pending', 'paid', 'overdue')),
                days_overdue INTEGER NOT NULL DEFAULT 0,
                source_file TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def calculate_status(due_date_str: str, is_already_paid: bool = False, today: Optional[date] = None) -> tuple[str, int]:
    """
    Calculates status ('pending', 'paid', 'overdue') and days_overdue.
    """
    if is_already_paid:
        return "paid", 0

    if today is None:
        today = date.today()

    try:
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    except ValueError:
        # Fallback if invalid format
        return "pending", 0

    if due_date < today:
        days = (today - due_date).days
        return "overdue", days
    else:
        return "pending", 0


def save_or_update_invoices(invoices: List[Union[dict, object]], db_path: str = DB_PATH) -> Dict[str, int]:
    """
    Saves or updates a list of invoices into SQLite.
    Preserves manual 'paid' status if an existing invoice was already marked paid.
    """
    init_db(db_path)
    today = date.today()
    now_str = datetime.now().isoformat()
    stats = {"inserted": 0, "updated": 0, "pending": 0, "overdue": 0, "paid": 0}

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        for inv in invoices:
            # Handle Pydantic model or dict
            data = inv.model_dump() if hasattr(inv, "model_dump") else dict(inv)

            inv_number = data["invoice_number"]
            due_date_str = data["due_date"]
            doc_is_paid = data.get("is_paid", False)

            # Check if invoice already exists in DB
            cursor.execute("SELECT status FROM invoices WHERE invoice_number = ?", (inv_number,))
            existing = cursor.fetchone()

            # Preserve paid status if already paid in DB or marked paid on document
            was_paid = bool(existing and existing["status"] == "paid") or doc_is_paid

            status, days_overdue = calculate_status(due_date_str, is_already_paid=was_paid, today=today)
            stats[status] += 1

            if existing:
                cursor.execute(
                    """
                    UPDATE invoices SET
                        client_name = ?,
                        client_email = ?,
                        amount = ?,
                        currency = ?,
                        issue_date = ?,
                        due_date = ?,
                        status = ?,
                        days_overdue = ?,
                        source_file = ?,
                        updated_at = ?
                    WHERE invoice_number = ?
                    """,
                    (
                        data["client_name"],
                        data["client_email"],
                        data["amount"],
                        data["currency"],
                        data["issue_date"],
                        data["due_date"],
                        status,
                        days_overdue,
                        data.get("source_file"),
                        now_str,
                        inv_number,
                    ),
                )
                stats["updated"] += 1
            else:
                cursor.execute(
                    """
                    INSERT INTO invoices (
                        invoice_number, client_name, client_email, amount, currency,
                        issue_date, due_date, status, days_overdue, source_file,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        inv_number,
                        data["client_name"],
                        data["client_email"],
                        data["amount"],
                        data["currency"],
                        data["issue_date"],
                        data["due_date"],
                        status,
                        days_overdue,
                        data.get("source_file"),
                        now_str,
                        now_str,
                    ),
                )
                stats["inserted"] += 1

        conn.commit()

    return stats


def mark_as_paid(invoice_number: str, db_path: str = DB_PATH) -> bool:
    """
    Marks an invoice as paid and resets days_overdue to 0.
    """
    init_db(db_path)
    now_str = datetime.now().isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE invoices SET
                status = 'paid',
                days_overdue = 0,
                updated_at = ?
            WHERE invoice_number = ?
            """,
            (now_str, invoice_number),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_overdue_invoices(db_path: str = DB_PATH) -> List[Dict]:
    """Retrieves all invoices with status='overdue', ordered by days_overdue DESC."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM invoices
            WHERE status = 'overdue'
            ORDER BY days_overdue DESC
            """
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_all_invoices(db_path: str = DB_PATH) -> List[Dict]:
    """Retrieves all invoices from SQLite."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoices ORDER BY invoice_number ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def display_invoices_table(invoices: List[Dict]) -> None:
    """Prints a clean ASCII table of invoices for console inspection."""
    if not invoices:
        print("No invoices found in database.")
        return

    header = f"{'Invoice #':<14} | {'Client':<26} | {'Amount':<14} | {'Due Date':<10} | {'Status':<9} | {'Overdue':<8}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for inv in invoices:
        curr = inv.get("currency", "INR")
        amt_str = f"₹{inv['amount']:,.0f} {curr}"
        status_disp = inv["status"].upper()
        days_disp = f"{inv['days_overdue']} d" if inv["status"] == "overdue" else "-"
        print(f"{inv['invoice_number']:<14} | {inv['client_name'][:26]:<26} | {amt_str:<14} | {inv['due_date']:<10} | {status_disp:<9} | {days_disp:<8}")
    print("-" * len(header))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Invoice Status Tracker CLI")
    parser.add_argument("--pay", help="Invoice number to mark as paid (e.g. INV-2026-002)")
    parser.add_argument("--unpay", help="Invoice number to reset to pending/overdue (e.g. INV-2026-002)")
    parser.add_argument("--reset", action="store_true", help="Clear and re-sync database from invoice files")
    parser.add_argument("--list", action="store_true", help="List all invoices in the database")
    args = parser.parse_args()

    if args.pay:
        success = mark_as_paid(args.pay)
        if success:
            print(f"✓ Invoice {args.pay} successfully marked as PAID.")
        else:
            print(f"✗ Invoice {args.pay} not found.")

    if args.unpay:
        with get_db_connection(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT due_date FROM invoices WHERE invoice_number = ?", (args.unpay,))
            row = cur.fetchone()
            if row:
                st, days = calculate_status(row["due_date"], is_already_paid=False)
                cur.execute(
                    "UPDATE invoices SET status = ?, days_overdue = ?, updated_at = ? WHERE invoice_number = ?",
                    (st, days, datetime.now().isoformat(), args.unpay),
                )
                conn.commit()
                print(f"✓ Invoice {args.unpay} reset to {st.upper()} ({days}d overdue).")
            else:
                print(f"✗ Invoice {args.unpay} not found.")

    if args.reset:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        print("✓ Database reset. Run 'python main.py' to re-extract and sync.")

    all_invs = get_all_invoices()
    print(f"\nInvoice Tracker DB ({DB_PATH}): {len(all_invs)} total records")
    display_invoices_table(all_invs)
