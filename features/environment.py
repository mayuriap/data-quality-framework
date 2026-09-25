"""
features/environment.py

Behave setup and teardown.
Runs before and after each scenario.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from utils.db_connection import db
from utils.config_manager import config


def before_all(context):
    """Runs once before all scenarios."""
    logger.info("Setting up test context...")
    context.db     = db
    context.config = config

    if not db.test_connection():
        raise RuntimeError(
            "Database connection failed. "
            "Check your configuration."
        )
    logger.info(f"Connected to: {config.environment} environment")


def before_scenario(context, scenario):
    """Runs before each scenario."""
    logger.info(f"Starting scenario: {scenario.name}")


def after_scenario(context, scenario):
    """Runs after each scenario."""
    if scenario.status == "failed":
        logger.error(f"FAILED: {scenario.name}")
    else:
        logger.info(f"PASSED: {scenario.name}")


def after_all(context):
    """Runs once after all scenarios complete."""
    logger.info("Test suite complete")