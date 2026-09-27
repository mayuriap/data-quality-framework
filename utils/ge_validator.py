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

    # ------------------------------------------------------------------ #
    # Add a new table here — no other code changes needed                  #
    # ------------------------------------------------------------------ #
    VALIDATIONS = [
        ("bronze_customers",      "public_bronze", "stg_customers",         "bronze_customers_suite"),
        ("bronze_transactions",   "public_bronze", "stg_transactions",      "bronze_transactions_suite"),
        ("silver_customers",      "public_silver", "int_customers",         "silver_customers_suite"),
        ("silver_transactions",   "public_silver", "int_transactions",      "silver_transactions_suite"),
        ("gold_daily_summary",    "public_gold",   "gold_daily_summary",    "gold_daily_suite"),
        ("gold_customer_summary", "public_gold",   "gold_customer_summary", "gold_customer_suite"),
    ]

    # ------------------------------------------------------------------ #
    # Add a new dynamic parameter here — no other code changes needed      #
    # ------------------------------------------------------------------ #
    PARAMETER_QUERIES = {
        "bronze_customer_count":    "SELECT COUNT(*) AS cnt FROM public_bronze.stg_customers",
        "bronze_transaction_count": "SELECT COUNT(*) AS cnt FROM public_bronze.stg_transactions",
        "silver_customer_count":    "SELECT COUNT(*) AS cnt FROM public_silver.int_customers",
        "silver_transaction_count": "SELECT COUNT(*) AS cnt FROM public_silver.int_transactions",
    }

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

        for param_name, sql in self.PARAMETER_QUERIES.items():
            result             = db.execute_query(sql)
            params[param_name] = result[0]["cnt"]
            logger.info(f"Parameter {param_name} = {params[param_name]}")

        return params

    def _load_suites(self):
        """Load all expectation suites from JSON files."""
        for _, _, _, suite_name in self.VALIDATIONS:
            suite_path = self.GE_ROOT / "expectations" / f"{suite_name}.json"

            with open(suite_path, "r") as f:
                suite_data = json.load(f)

            # Normalise — handle GE 1.4.1 inconsistency
            # GE writes "expectation_type" but reads "type"
            for exp in suite_data.get("expectations", []):
                exp.pop("id", None)
                if "expectation_type" in exp and "type" not in exp:
                    exp["type"] = exp.pop("expectation_type")

            self.context.suites.add_or_update(
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

    # ── Run all ───────────────────────────────────────────────────

    def validate_all(self) -> dict:
        """
        Run all GE validations across all layers.
        Returns combined results.
        """
        results    = {}
        all_passed = True

        for name, schema, table, suite_name in self.VALIDATIONS:
            try:
                result        = self._validate_table(schema, table, suite_name)
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