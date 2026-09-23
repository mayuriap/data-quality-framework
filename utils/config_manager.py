"""
utils/config_manager.py

Configuration manager supporting:
- Two environments: dev and test
- One database type: postgresql
- Can be extended later for prod, snowflake etc

Usage:
    from utils.config_manager import config
    url = config.get_db_url()

"""

import os
import configparser
from  pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class ConfigManager:

    """
    Manages database configuration for dev and test environments.

    Why this class:
    - One place for all config
    - Switch environment by changing .env only
    - No hardcoded credentials anywhere
    - Easy to extend for prod or new DB types later
    """
    SUPPORTED_ENVIRONMENTS = ["dev", "test"]

    def __init__(self, environment :str = None):

        """
        Initialise with environment from .env or parameter.
        Args:
            environment: "dev" or "test"  defaults to ENVIRONMENT in .env
        """

        self.environment = environment or os.getenv("ENVIRONMENT", "test").lower()
        if self.environment not in self.SUPPORTED_ENVIRONMENTS:
            raise ValueError(f"Unsupported environment: {self.environment}. Supported environments: {self.SUPPORTED_ENVIRONMENTS}")        
        self.config = configparser.ConfigParser()
        self.config.read(Path(__file__).parent.parent / "config" / "database.ini")
        self.env = os.getenv("ENV", "test_postgresql")

   
        
    def get_db_url(self) -> str:
        env      = self.environment.upper()
        host     = os.getenv(f"{env}_DB_HOST", "localhost")
        port     = os.getenv(f"{env}_DB_PORT", "5432")
        name     = os.getenv(f"{env}_DB_NAME")
        user     = os.getenv(f"{env}_DB_USER", "postgres")
        password = os.getenv(f"{env}_DB_PASSWORD")

        if not password:
            raise ValueError(f"{env}_DB_PASSWORD not set in .env")

        if not name:
            raise ValueError(f"{env}_DB_NAME not set in .env")

        return f"postgresql://{user}:{password}@{host}:{port}/{name}"

       

    @property
    def is_test(self):
        return self.environment == "test"

    @property
    def is_dev(self):
        return self.environment == "dev"

    def __repr__(self):
        return f"ConfigManager(environment={self.environment}, env={self.env})" 

#default instance -reads Environment from .env
config = ConfigManager()