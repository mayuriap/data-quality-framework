
"""
setup_database.py

Creates database tables and loads test data.
Run once before executing tests.

Usage:
    python setup_database.py

What it does:
    1. Creates raw_customers table
    2. Creates raw_transactions table
    3. Generates test data with DQ issues
    4. Inserts data into both tables
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from loguru import logger
from utils.db_connection import db
from utils.data_generator import DataGenerator


def create_tables():
    """
    Create raw_customers and raw_transactions tables.
    Drops existing tables first — clean slate every run.
    """
    sql = """
    DROP TABLE IF EXISTS raw_transactions;
    DROP TABLE IF EXISTS raw_customers;

    CREATE TABLE raw_customers (
        customer_id   VARCHAR(20),
        first_name    VARCHAR(50),
        last_name     VARCHAR(50),
        email         VARCHAR(100),
        phone         VARCHAR(20),
        segment       VARCHAR(20),
        created_date  DATE
    );

    CREATE TABLE raw_transactions (
        transaction_id   VARCHAR(20),
        customer_id      VARCHAR(20),
        amount           DECIMAL(10,2),
        currency         VARCHAR(10),
        status           VARCHAR(20),
        transaction_date DATE,
        settlement_date  DATE
    );
    """

    with db.get_session() as session:
        session.execute(text(sql))

    logger.info("Tables created successfully")


def load_customers(customers: list):
    """
    Insert customer records into raw_customers table.

    Args:
        customers: list of customer dicts
    """
    sql = """
    INSERT INTO raw_customers
        (customer_id, first_name, last_name,
         email, phone, segment, created_date)
    VALUES
        (:customer_id, :first_name, :last_name,
         :email, :phone, :segment, :created_date)
    """
    db.execute_many(sql, customers)
    logger.info(f"Inserted {len(customers)} customers")


def load_transactions(transactions: list):
    """
    Insert transaction records into raw_transactions table.

    Args:
        transactions: list of transaction dicts
    """
    sql = """
    INSERT INTO raw_transactions
        (transaction_id, customer_id, amount,
         currency, status, transaction_date, settlement_date)
    VALUES
        (:transaction_id, :customer_id, :amount,
         :currency, :status, :transaction_date, :settlement_date)
    """
    db.execute_many(sql, transactions)
    logger.info(f"Inserted {len(transactions)} transactions")


def verify_data():
    """Quick check — show record counts after loading."""
    checks = [
        ("raw_customers",    "SELECT COUNT(*) AS cnt FROM raw_customers"),
        ("raw_transactions", "SELECT COUNT(*) AS cnt FROM raw_transactions"),
    ]

    print("\n── Data verification ──────────────────")
    for table, sql in checks:
        result = db.execute_query(sql)
        print(f"  {table:<25} {result[0]['cnt']} rows")
    print("───────────────────────────────────────\n")


def show_sample_issues():
    """Show sample of injected DQ issues."""

    print("── Sample DQ Issues ───────────────────")

    # Null emails
    result = db.execute_query("""
        SELECT customer_id, email
        FROM raw_customers
        WHERE email IS NULL
        LIMIT 3
    """)
    print(f"  Null emails: {len(result)} found")

    # Negative amounts
    result = db.execute_query("""
        SELECT transaction_id, amount
        FROM raw_transactions
        WHERE amount < 0
        LIMIT 3
    """)
    print(f"  Negative amounts: {len(result)} found")

    # Invalid currencies
    result = db.execute_query("""
        SELECT transaction_id, currency
        FROM raw_transactions
        WHERE currency NOT IN ('GBP','USD','EUR','JPY','CHF')
        LIMIT 3
    """)
    print(f"  Invalid currencies: {len(result)} found")

    print("───────────────────────────────────────\n")


if __name__ == "__main__":
    print("Setting up database...")
    print(f"Environment: {db}")

    # Step 1 — Create tables
    create_tables()

    # Step 2 — Generate data
    generator    = DataGenerator()
    customers    = generator.generate_customers(100)
    transactions = generator.generate_transactions(500)

    # Step 3 — Load data
    load_customers(customers)
    load_transactions(transactions)

    # Step 4 — Verify
    verify_data()
    show_sample_issues()

    print("✓ Database setup complete")
    print("  Run: behave — to execute BDD tests")