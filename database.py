import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE = DATA_DIR / "database.db"


def get_connection():
    connection = sqlite3.connect(
        DATABASE,
        timeout=10
    )

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 10000")

    return connection


def create_tables():

    connection = get_connection()
    cursor = connection.cursor()

    # =====================================================
    # USERS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL
                CHECK (role IN ('boss', 'staff'))
        )
    """)

    # =====================================================
    # SUPPLIERS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            tin TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """)

    # =====================================================
    # INVOICES
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,

            supplier_id INTEGER NOT NULL,

            invoice_number TEXT,
            invoice_date TEXT NOT NULL,

            payment_terms TEXT,

            total_before_tax REAL NOT NULL DEFAULT 0,
            tax_amount REAL NOT NULL DEFAULT 0,
            total_amount REAL NOT NULL DEFAULT 0,

            amount_paid REAL NOT NULL DEFAULT 0,

            status TEXT NOT NULL DEFAULT 'Unpaid',

            image_path TEXT,

            uploaded_by INTEGER,

            verification_status TEXT NOT NULL DEFAULT 'Pending',

            is_deleted INTEGER NOT NULL DEFAULT 0,

            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (supplier_id)
                REFERENCES suppliers(supplier_id),

            FOREIGN KEY (uploaded_by)
                REFERENCES users(user_id)
        )
    """)

    # =====================================================
    # INVOICE ITEMS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,

            invoice_id INTEGER NOT NULL,

            item_code TEXT,

            product_name TEXT NOT NULL,

            quantity REAL NOT NULL DEFAULT 1,

            unit TEXT,

            unit_price REAL NOT NULL DEFAULT 0,

            subtotal REAL NOT NULL DEFAULT 0,

            FOREIGN KEY (invoice_id)
                REFERENCES invoices(invoice_id)
                ON DELETE CASCADE
        )
    """)

    # =====================================================
    # PAYMENTS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,

            invoice_id INTEGER NOT NULL,

            payment_date TEXT NOT NULL,

            amount REAL NOT NULL,

            payment_method TEXT,

            recorded_by INTEGER,

            FOREIGN KEY (invoice_id)
                REFERENCES invoices(invoice_id)
        )
    """)

    # =====================================================
    # EXPECTED INVOICES
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expected_invoices (
            expected_invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,

            supplier_id INTEGER NOT NULL,

            expected_date TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT 'Missing',

            FOREIGN KEY (supplier_id)
                REFERENCES suppliers(supplier_id)
        )
    """)

    connection.commit()
    connection.close()


def upgrade_existing_database():

    connection = get_connection()

    # -----------------------------------------------------
    # Add new supplier column
    # -----------------------------------------------------

    supplier_columns = [
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(suppliers)"
        ).fetchall()
    ]

    if "tin" not in supplier_columns:

        connection.execute(
            """
            ALTER TABLE suppliers
            ADD COLUMN tin TEXT
            """
        )

    # -----------------------------------------------------
    # Add new invoice columns
    # -----------------------------------------------------

    invoice_columns = [
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(invoices)"
        ).fetchall()
    ]

    new_invoice_columns = {
        "payment_terms": "TEXT",
        "total_before_tax": "REAL NOT NULL DEFAULT 0",
        "tax_amount": "REAL NOT NULL DEFAULT 0",
        "is_deleted": "INTEGER NOT NULL DEFAULT 0"
    }

    for column, definition in new_invoice_columns.items():

        if column not in invoice_columns:

            connection.execute(
                f"""
                ALTER TABLE invoices
                ADD COLUMN {column} {definition}
                """
            )

    # -----------------------------------------------------
    # Add new invoice item columns
    # -----------------------------------------------------

    item_columns = [
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(invoice_items)"
        ).fetchall()
    ]

    new_item_columns = {
        "item_code": "TEXT",
        "unit": "TEXT"
    }

    for column, definition in new_item_columns.items():

        if column not in item_columns:

            connection.execute(
                f"""
                ALTER TABLE invoice_items
                ADD COLUMN {column} {definition}
                """
            )

    # -----------------------------------------------------
    # Existing invoices
    # -----------------------------------------------------

    connection.execute(
        """
        UPDATE invoices
        SET total_before_tax = total_amount
        WHERE total_before_tax = 0
        """
    )

    connection.commit()
    connection.close()


if __name__ == "__main__":

    create_tables()
    upgrade_existing_database()

    print("Database created and upgraded successfully!")