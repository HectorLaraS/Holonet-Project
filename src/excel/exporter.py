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
from openpyxl.styles import PatternFill
from openpyxl.styles import Font
from openpyxl.styles import Alignment
from openpyxl import load_workbook

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
    
    def export_report(self) -> Path:
        """
        Exports the report to Excel.
        """

        dataframe = self.load_report()

        exports_folder = Path("exports")

        exports_folder.mkdir(
            exist_ok=True
        )

        file_name = (
            f"Holonet_"
            f"{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        )

        output_file = exports_folder / file_name

        logger.info(
            f"Generating Excel: {output_file}"
        )

        dataframe.to_excel(
            output_file,
            index=False
        )

        workbook = load_workbook(output_file)

        worksheet = workbook.active

        header_fill = PatternFill(
            fill_type="solid",
            start_color="C32032",
            end_color="C32032"
        )

        header_font = Font(
            bold=True,
            color="FFFFFF"
        )

        header_alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

        for cell in worksheet[1]:

            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment

        for column_cells in worksheet.columns:

            length = max(
                len(str(cell.value)) if cell.value is not None else 0
                for cell in column_cells
            )

            adjusted_width = min(length + 3, 60)

            worksheet.column_dimensions[
                column_cells[0].column_letter
            ].width = adjusted_width

        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions

        workbook.save(output_file)

        logger.info(
            "Excel generated successfully."
        )

        return output_file