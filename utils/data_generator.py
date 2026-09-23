"""
utils/data_generator.py

Generates synthetic test data for:
- raw_customers table
- raw_transactions table

Includes intentional data quality issues for testing.

Usage:
    from utils.data_generator import DataGenerator
    generator = DataGenerator()
    customers    = generator.generate_customers(100)
    transactions = generator.generate_transactions(500)
"""

import random
import uuid
from datetime import datetime, timedelta
from loguru import logger


class DataGenerator:
    """
    Generates realistic financial test data
    with intentional DQ issues injected.

    Issues injected in customers:
    - Null emails
    - Duplicate customer IDs
    - Invalid phone formats
    - Missing names

    Issues injected in transactions:
    - Null amounts
    - Negative amounts
    - Invalid currencies
    - Orphan customer IDs
    - Future dates
    - Duplicate transaction IDs
    """

    VALID_CURRENCIES   = ["GBP", "USD", "EUR", "JPY", "CHF"]
    INVALID_CURRENCIES = ["XYZ", "ABC", "ZZZ"]
    CUSTOMER_SEGMENTS  = ["RETAIL", "PREMIUM", "BUSINESS"]
    TX_STATUSES        = ["COMPLETED", "PENDING", "FAILED"]

    def __init__(self):
        self._customer_ids = []
        logger.info("DataGenerator initialised")

    def generate_customers(self, count: int = 100) -> list:
        """
        Generate customer records with intentional issues.

        Args:
            count: number of customers to generate

        Returns:
            list of customer dicts
        """
        customers = []

        for i in range(1, count + 1):
            customer_id = f"CUST-{i:04d}"
            self._customer_ids.append(customer_id)

            customer = {
                "customer_id":  customer_id,
                "first_name":   f"FirstName{i}",
                "last_name":    f"LastName{i}",
                "email":        f"customer{i}@example.com",
                "phone":        f"+44770000{i:04d}",
                "segment":      random.choice(self.CUSTOMER_SEGMENTS),
                "created_date": self._random_past_date(365)
            }
            customers.append(customer)

        # Inject DQ issues
        customers = self._inject_customer_issues(customers)

        logger.info(f"Generated {len(customers)} customers")
        return customers

    def _inject_customer_issues(self, customers: list) -> list:
        """
        Inject intentional data quality issues
        into customer records.
        """

        # Issue 1 — Null emails (5 records)
        for i in range(5):
            customers[i]["email"] = None

        # Issue 2 — Duplicate customer IDs (3 records)
        for i in range(5, 8):
            customers[i]["customer_id"] = "CUST-0001"

        # Issue 3 — Invalid phone format (4 records)
        for i in range(8, 12):
            customers[i]["phone"] = "INVALID-PHONE"

        # Issue 4 — Missing names (2 records)
        for i in range(12, 14):
            customers[i]["first_name"] = None
            customers[i]["last_name"]  = None

        return customers

    def generate_transactions(self, count: int = 500) -> list:
        """
        Generate transaction records with intentional issues.

        Args:
            count: number of transactions to generate

        Returns:
            list of transaction dicts
        """
        if not self._customer_ids:
            raise ValueError(
                "Generate customers first — "
                "transactions need customer IDs"
            )

        transactions = []

        for i in range(1, count + 1):
            tx_id = f"TXN-{i:06d}"

            transaction = {
                "transaction_id":   tx_id,
                "customer_id":      random.choice(self._customer_ids),
                "amount":           round(random.uniform(10, 5000), 2),
                "currency":         random.choice(self.VALID_CURRENCIES),
                "status":           random.choice(self.TX_STATUSES),
                "transaction_date": self._random_past_date(90),
                "settlement_date":  self._random_past_date(88)
            }
            transactions.append(transaction)

        # Inject DQ issues
        transactions = self._inject_transaction_issues(transactions)

        logger.info(f"Generated {len(transactions)} transactions")
        return transactions

    def _inject_transaction_issues(self, transactions: list) -> list:
        """
        Inject intentional data quality issues
        into transaction records.
        """

        # Issue 1 — Null amounts (5 records)
        for i in range(5):
            transactions[i]["amount"] = None

        # Issue 2 — Negative amounts (3 records)
        for i in range(5, 8):
            transactions[i]["amount"] = round(
                random.uniform(-1000, -1), 2
            )

        # Issue 3 — Invalid currencies (3 records)
        for i in range(8, 11):
            transactions[i]["currency"] = random.choice(
                self.INVALID_CURRENCIES
            )

        # Issue 4 — Orphan customer IDs (4 records)
        # customer IDs that do not exist in customers table
        for i in range(11, 15):
            transactions[i]["customer_id"] = "CUST-9999"

        # Issue 5 — Future dates (2 records)
        for i in range(15, 17):
            transactions[i]["transaction_date"] = (
                datetime.now() + timedelta(days=30)
            ).strftime("%Y-%m-%d")

        # Issue 6 — Duplicate transaction IDs (3 records)
        for i in range(17, 20):
            transactions[i]["transaction_id"] = "TXN-000001"

        return transactions

    def _random_past_date(self, days_back: int) -> str:
        """Generate a random date within the last N days."""
        days_ago = random.randint(1, days_back)
        date     = datetime.now() - timedelta(days=days_ago)
        return date.strftime("%Y-%m-%d")

    def get_issue_summary(self) -> dict:
        """
        Returns summary of injected issues.
        Useful for test documentation.
        """
        return {
            "customers": {
                "null_emails":        5,
                "duplicate_ids":      3,
                "invalid_phones":     4,
                "missing_names":      2,
                "total_issues":       14
            },
            "transactions": {
                "null_amounts":       5,
                "negative_amounts":   3,
                "invalid_currencies": 3,
                "orphan_customers":   4,
                "future_dates":       2,
                "duplicate_ids":      3,
                "total_issues":       20
            }
        }