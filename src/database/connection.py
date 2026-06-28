"""
Holonet

SQL Server Connection
"""

from __future__ import annotations

import pyodbc

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseConnection:
    """
    SQL Server database connection.
    """

    def __init__(self):

        self.connection = None

    def __enter__(self):

        logger.info("Connecting to SQL Server...")

        connection_string = (
            f"DRIVER={{{settings.driver}}};"
            f"SERVER={settings.db_server};"
            f"DATABASE={settings.db_database};"
            f"UID={settings.db_username};"
            f"PWD={settings.db_password};"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
        )

        self.connection = pyodbc.connect(
            connection_string,
            timeout=30
        )

        logger.info("Connected successfully.")

        return self.connection

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb
    ):

        if self.connection is not None:

            self.connection.close()

            logger.info(
                "SQL Server connection closed."
            )