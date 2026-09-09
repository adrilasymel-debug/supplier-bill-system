import os

import psycopg2
import psycopg2.extras

try:
    import streamlit as st
except ImportError:
    st = None


def _get_secret(key):
    """
    Read a config value from Streamlit secrets first
    (used on Streamlit Community Cloud), falling back
    to an environment variable (used for local dev).
    """

    if st is not None:

        try:
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass

    return os.environ.get(key)


# ================================================================
# sqlite3-COMPATIBLE WRAPPER
# ----------------------------------------------------------------
# app.py, auth.py etc. were written against sqlite3's interface:
#   connection.execute(sql, params).fetchone() / .fetchall()
#   row["column_name"]
#   cursor.lastrowid
#
# These thin wrappers let all of that existing code keep working
# unchanged against a real Postgres (Supabase) database, using
# "?" placeholders exactly like sqlite3 does.
# ================================================================

class CursorWrapper:

    def __init__(self, cursor):
        self._cursor = cursor

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def lastrowid(self):
        # Postgres has no lastrowid. Call sites that need the new
        # row's id add "RETURNING <id_column>" to their SQL and
        # read it from fetchone() instead - see app.py.
        return None


class ConnectionWrapper:

    def __init__(self, connection):
        self._connection = connection

    def execute(self, sql, params=None):

        params = params or []

        # sqlite3 uses "?" placeholders; psycopg2 uses "%s".
        pg_sql = sql.replace("?", "%s")

        cursor = self._connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )

        cursor.execute(pg_sql, tuple(params))

        return CursorWrapper(cursor)

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()


def get_connection():

    connection = psycopg2.connect(
        host=_get_secret("SUPABASE_DB_HOST"),
        port=_get_secret("SUPABASE_DB_PORT") or 5432,
        dbname=_get_secret("SUPABASE_DB_NAME") or "postgres",
        user=_get_secret("SUPABASE_DB_USER"),
        password=_get_secret("SUPABASE_DB_PASSWORD"),
        sslmode="require",
    )

    return ConnectionWrapper(connection)


def create_tables():

    connection = get_connection()

    try:

        # =====================================================
        # USERS
        # =====================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
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

        connection.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                supplier_id SERIAL PRIMARY KEY,
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

        connection.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_id SERIAL PRIMARY KEY,

                supplier_id INTEGER NOT NULL
                    REFERENCES suppliers(supplier_id),

                invoice_number TEXT,
                invoice_date TEXT NOT NULL,

                payment_terms TEXT,

                total_before_tax REAL NOT NULL DEFAULT 0,
                tax_amount REAL NOT NULL DEFAULT 0,
                total_amount REAL NOT NULL DEFAULT 0,

                amount_paid REAL NOT NULL DEFAULT 0,

                status TEXT NOT NULL DEFAULT 'Unpaid',

                image_path TEXT,

                uploaded_by INTEGER
                    REFERENCES users(user_id),

                verification_status TEXT NOT NULL DEFAULT 'Pending',

                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =====================================================
        # INVOICE ITEMS
        # =====================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                item_id SERIAL PRIMARY KEY,

                invoice_id INTEGER NOT NULL
                    REFERENCES invoices(invoice_id)
                    ON DELETE CASCADE,

                item_code TEXT,
                product_name TEXT NOT NULL,
                quantity REAL NOT NULL DEFAULT 1,
                unit TEXT,
                unit_price REAL NOT NULL DEFAULT 0,
                subtotal REAL NOT NULL DEFAULT 0
            )
        """)

        # =====================================================
        # PAYMENTS
        # =====================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id SERIAL PRIMARY KEY,

                invoice_id INTEGER NOT NULL
                    REFERENCES invoices(invoice_id),

                payment_date TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT,
                recorded_by INTEGER
            )
        """)

        # =====================================================
        # EXPECTED INVOICES
        # =====================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS expected_invoices (
                expected_invoice_id SERIAL PRIMARY KEY,

                supplier_id INTEGER NOT NULL
                    REFERENCES suppliers(supplier_id),

                expected_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Missing'
            )
        """)

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":

    create_tables()

    print("Database tables created successfully on Supabase!")
