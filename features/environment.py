"""
features/environment.py

Behave setup and teardown.
Runs before and after each scenario.

This is Behave's equivalent of pytest fixtures.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger   
from utils.db_connection import db
from utils_config_manager import Config

def before_all(context):
      """
    Runs once before all scenarios.
    Sets up shared context for all tests.

    context is Behave's shared object —
    anything stored here is available
    in every step definition.
    """
    logger.info("Setting up test context.   ..")
    
    # Store db and config on context
    # so all steps can access them
    
    context.db = db
    context.config = Config()
    
    #verify that the database connection is working
   if not db.test_connection():
       raise runtimeError("Database connection failed. Check your configuration.")
   
   logger.info(f"Connected to: {config.environment} environment")
   
   
   def before_scenario(context, scenario):
    """
    Runs before each scenario.
    Resets the database to a clean state.
    """
    logger.info(f"Setting up for scenario: {scenario.name}")
    
    
    def after_scenario(context, scenario):
     """
    Runs after each individual scenario.
    Logs pass or fail.
    """
    if scenario.status == "failed":
        logger.error(f"FAILED: {scenario.name}")
    else:
        logger.info(f"PASSED: {scenario.name}")
    
   
   def after_all(context):
       """
    Runs once after all scenarios complete.
    Clean up resources.
    """
    logger.info("Test suite complete")
       
       
    
    
    
    
    