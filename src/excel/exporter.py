"""
Holonet

Excel Exporter
"""

from __future__ import annotations

import pandas as pd

from src.database.connection import DatabaseConnection
from src.excel.queries import REPORT_QUERY
from src.utils.logger import get_logger
from pathlib import Path
from datetime import datetime

logger = get_logger(__name__)


class ExcelExporter:

    def load_report(self) -> pd.DataFrame:
        """
        Loads the report from SQL Server.
        """

        logger.info(
            "Loading report data..."
        )

        with DatabaseConnection() as connection:

            dataframe = pd.read_sql(
                REPORT_QUERY,
                connection
            )

        logger.info(
            f"{len(dataframe)} rows loaded."
        )

        return dataframe