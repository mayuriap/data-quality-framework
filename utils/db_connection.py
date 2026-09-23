"""
utils/db_connection.py

Database connection manager.
All database operations go through this class.

Usage:
    from utils.db_connection import db
    results = db.execute_query("SELECT * FROM customers")
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from loguru import logger

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config_manager import config


class DatabaseConnection:
    """
    Manages PostgreSQL connections using SQLAlchemy.

    Why SQLAlchemy:
    - Handles connection pooling automatically
    - Works with Great Expectations natively
    - Clean context manager for sessions
    """

    def __init__(self):
        self._engine  = None
        self._Session = None
        self._connect()

    def _connect(self):
        """Create engine and session factory."""
        try:
            db_url        = config.get_db_url()
            self._engine  = create_engine(
                db_url,
                pool_pre_ping = True
            )
            self._Session = sessionmaker(bind=self._engine)
            logger.info(f"Connected to: {config.environment} environment")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise

    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions.
        Automatically commits on success.
        Automatically rolls back on error.
        Automatically closes when done.

        Usage:
            with db.get_session() as session:
                session.execute(text("SELECT 1"))
        """
        session = self._Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()

    def execute_query(self, sql: str) -> list:
        """
        Execute SQL and return list of dicts.

        Args:
            sql: SQL query string

        Returns:
            list of dicts — one dict per row
        """
        with self.get_session() as session:
            result = session.execute(text(sql))
            rows   = result.fetchall()
            cols   = result.keys()
            return [dict(zip(cols, row)) for row in rows]

    def execute_many(self, sql: str, params: list):
        """
        Execute SQL with multiple parameter sets.
        Used for bulk inserts.

        Args:
            sql:    SQL with named parameters
            params: list of dicts with parameter values
        """
        with self.get_session() as session:
            for param in params:
                session.execute(text(sql), param)

    def test_connection(self) -> bool:
        """Quick check — is database reachable?"""
        try:
            result = self.execute_query("SELECT 1 AS test")
            return result[0]["test"] == 1
        except Exception:
            return False

    @property
    def engine(self):
        """Read-only engine access for Great Expectations."""
        return self._engine

    def __repr__(self):
        return f"DatabaseConnection(environment={config.environment})"


# Single instance — import everywhere
db = DatabaseConnection()