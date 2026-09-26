"""
utils/ge_validator.py

Great Expectations validator for ETL data quality.
Uses FileDataContext with JSON suite files.
Supports Evaluation Parameters for dynamic thresholds.

Usage:
    from utils.ge_validator import GEValidator
    validator = GEValidator()
    results   = validator.validate_all()
"""

import sys
import os
import json 
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from pathlib import Path
import great_expectations as ge
from loguru import logger
from utils.config_manager import config
from utils.db_connection import db


class GEValidator:
    """
    Validates data quality using Great Expectations.

    Uses FileDataContext — reads from great_expectations.yml
    Uses JSON suite files for expectations
    Uses Evaluation Parameters for dynamic thresholds
    """

    # Path to great_expectations folder
    GE_ROOT = Path(__file__).parent.parent / "great_expectations"

    def __init__(self):
        self.db_url  = config.get_db_url()
        self.context = self._create_context()
        self._add_datasource()
        self._load_suites()
        self.params  = self._get_dynamic_parameters()
        logger.info("GEValidator initialised")

    def _create_context(self):
        """Create GE context."""
        context = ge.get_context(
            context_root_dir=str(self.GE_ROOT)
        )
        logger.info(f"GE context created from: {self.GE_ROOT}")
        return context

    def _add_datasource(self):
        """Add PostgreSQL datasource."""
        try:
            self.datasource = self.context.data_sources.get("dq_postgres")
            logger.info("PostgreSQL datasource already exists")
        except Exception:
            self.datasource = self.context.data_sources.add_postgres(
                name              = "dq_postgres",
                connection_string = self.db_url
            )
            logger.info("PostgreSQL datasource added")

    def _get_dynamic_parameters(self) -> dict:
        """
        Query actual counts from database.
        These become Evaluation Parameters —
        replacing $PARAMETER placeholders in JSON suites.

        Returns:
            dict of parameter_name -> value
        """
        params = {}

        queries = {
            "bronze_customer_count":    "SELECT COUNT(*) AS cnt FROM public_bronze.stg_customers",
            "bronze_transaction_count": "SELECT COUNT(*) AS cnt FROM public_bronze.stg_transactions",
            "silver_customer_count":    "SELECT COUNT(*) AS cnt FROM public_silver.int_customers",
            "silver_transaction_count": "SELECT COUNT(*) AS cnt FROM public_silver.int_transactions",
        }

        for param_name, sql in queries.items():
            result       = db.execute_query(sql)
            params[param_name] = result[0]["cnt"]
            logger.info(f"Parameter {param_name} = {params[param_name]}")

        return params
    
    def _load_suites(self):
        """Load all expectation suites from JSON files."""
        suite_files = [
            "bronze_customers_suite",
            "bronze_transactions_suite",
            "silver_customers_suite",
            "silver_transactions_suite",
            "gold_daily_suite",
            "gold_customer_suite"
        ]
    
        for suite_name in suite_files:
            suite_path = self.GE_ROOT / "expectations" / f"{suite_name}.json"
        
            with open(suite_path, "r") as f:
                suite_data = json.load(f)
        
            suite = self.context.suites.add_or_update(
                ge.ExpectationSuite(
                   name         = suite_name,
                   expectations = suite_data.get("expectations", [])
                )
            )
            logger.info(f"Loaded suite: {suite_name}")

    def _validate_table(
        self,
        schema:     str,
        table:      str,
        suite_name: str
    ) -> dict:
        """
        Core validation method.
        Loads suite from JSON file and runs against table.

        Args:
            schema:     PostgreSQL schema name
            table:      table name
            suite_name: name of JSON suite file

        Returns:
            dict with success, statistics and suite name
        """
        # Add table as asset
        try:
            asset = self.datasource.get_asset(
                name=f"{schema}_{table}_{suite_name}"
            )
            logger.info(f"Asset already exists: {asset.name}")
        except Exception:
            asset = self.datasource.add_table_asset(
                name        = f"{schema}_{table}_{suite_name}",
                table_name  = table,
                schema_name = schema
        )

        # Build batch request
        batch_request = asset.build_batch_request()

        # Get validator with loaded suite
        validator = self.context.get_validator(
            batch_request          = batch_request,
            expectation_suite_name = suite_name,
            
        )

        # Run validation with dynamic parameters
        results = validator.validate(
            suite_parameters = self.params
        )    
        

        passed = results.statistics["successful_expectations"]
        total  = results.statistics["evaluated_expectations"]
        failed = results.statistics["unsuccessful_expectations"]
        pct    = results.statistics["success_percent"]

        status = "PASS" if results.success else "FAIL"
        logger.info(
            f"{status} {suite_name}: "
            f"{passed}/{total} expectations "
            f"({pct:.1f}%)"
        )

        return {
            "suite":      suite_name,
            "table":      f"{schema}.{table}",
            "success":    results.success,
            "statistics": {
                "evaluated":   total,
                "successful":  passed,
                "failed":      failed,
                "success_pct": pct
            }
        }

    # ── Bronze validations ────────────────────────────────────────

    def validate_bronze_customers(self) -> dict:
        """Validate Bronze customer layer."""
        return self._validate_table(
            schema     = "public_bronze",
            table      = "stg_customers",
            suite_name = "bronze_customers_suite"
        )

    def validate_bronze_transactions(self) -> dict:
        """Validate Bronze transaction layer."""
        return self._validate_table(
            schema     = "public_bronze",
            table      = "stg_transactions",
            suite_name = "bronze_transactions_suite"
        )

    # ── Silver validations ────────────────────────────────────────

    def validate_silver_customers(self) -> dict:
        """Validate Silver customer layer."""
        return self._validate_table(
            schema     = "public_silver",
            table      = "int_customers",
            suite_name = "silver_customers_suite"
        )

    def validate_silver_transactions(self) -> dict:
        """Validate Silver transaction layer."""
        return self._validate_table(
            schema     = "public_silver",
            table      = "int_transactions",
            suite_name = "silver_transactions_suite"
        )

    # ── Gold validations ──────────────────────────────────────────

    def validate_gold_daily_summary(self) -> dict:
        """Validate Gold daily summary."""
        return self._validate_table(
            schema     = "public_gold",
            table      = "gold_daily_summary",
            suite_name = "gold_daily_suite"
        )

    def validate_gold_customer_summary(self) -> dict:
        """Validate Gold customer summary."""
        return self._validate_table(
            schema     = "public_gold",
            table      = "gold_customer_summary",
            suite_name = "gold_customer_suite"
        )

    # ── Run all ───────────────────────────────────────────────────

    def validate_all(self) -> dict:
        """
        Run all GE validations across all layers.
        Returns combined results.
        """
        validations = [
            ("bronze_customers",      self.validate_bronze_customers),
            ("bronze_transactions",   self.validate_bronze_transactions),
            ("silver_customers",      self.validate_silver_customers),
            ("silver_transactions",   self.validate_silver_transactions),
            ("gold_daily_summary",    self.validate_gold_daily_summary),
            ("gold_customer_summary", self.validate_gold_customer_summary),
        ]

        results    = {}
        all_passed = True

        for name, validation_fn in validations:
            try:
                result       = validation_fn()
                results[name] = result
                if not result["success"]:
                    all_passed = False
            except Exception as e:
                logger.error(f"ERROR {name}: {e}")
                results[name] = {
                    "success": False,
                    "error":   str(e)
                }
                all_passed = False

        results["overall_success"] = all_passed
        return results

    def __repr__(self):
        return (
            f"GEValidator("
            f"environment={config.environment}, "
            f"params={self.params})"
        )