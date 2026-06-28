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
from openpyxl.styles import PatternFill
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Font

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

            dataframe.rename(
            columns={
                "account_number": "Account Number",
                "service_line_number": "Service Line",
                "product_name": "Plan",
                "product_id": "Product ID",
                "billing_cycle_key": "Billing Cycle",
                "cycle_start": "Cycle Start",
                "cycle_end": "Cycle End",
                "usage_limit_gb": "Usage Limit (GB)",
                "priority_gb": "Priority (GB)",
                "standard_gb": "Standard (GB)",
                "consumed_gb": "Consumed (GB)",
                "available_gb": "Available (GB)",
                "usage_percent": "Usage (%)",
                "recurring_cost": "Monthly Cost",
                "data_block_type": "Data Block Type",
                "blocks_count": "Blocks",
                "per_block_amount_gb": "Block Size (GB)",
                "total_amount_gb": "Total Block (GB)",
                "consumed_amount_gb": "Block Used (GB)",
                "remaining_amount_gb": "Block Remaining (GB)",
                "per_block_price": "Block Price",
                "total_price": "Total Block Cost",
                "currency": "Currency"
            },
            inplace=True
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

        gb_columns = [
            "Usage Limit (GB)",
            "Priority (GB)",
            "Standard (GB)",
            "Consumed (GB)",
            "Available (GB)",
            "Block Size (GB)",
            "Total Block (GB)",
            "Block Used (GB)",
            "Block Remaining (GB)"
        ]

        currency_columns = [
            "Monthly Cost",
            "Block Price",
            "Total Block Cost"
        ]

        date_columns = [
            "Cycle Start",
            "Cycle End"
        ]

        percent_columns = [
            "Usage (%)"
        ]

        header_map = {}

        for cell in worksheet[1]:
            header_map[cell.value] = cell.column

        for column_name in gb_columns:

            if column_name in header_map:

                column = header_map[column_name]

                for row in range(2, worksheet.max_row + 1):

                    worksheet.cell(
                        row=row,
                        column=column
                    ).number_format = "0.00"

        for column_name in currency_columns:

            if column_name in header_map:

                column = header_map[column_name]

                for row in range(2, worksheet.max_row + 1):

                    worksheet.cell(
                        row=row,
                        column=column
                    ).number_format = '$#,##0.00'

        for column_name in date_columns:

            if column_name in header_map:

                column = header_map[column_name]

                for row in range(2, worksheet.max_row + 1):

                    worksheet.cell(
                        row=row,
                        column=column
                    ).number_format = "yyyy-mm-dd"

        for column_name in percent_columns:

            if column_name in header_map:

                column = header_map[column_name]

                for row in range(2, worksheet.max_row + 1):

                    worksheet.cell(
                        row=row,
                        column=column
                    ).number_format = '0.00"%"'


        if "Usage (%)" in header_map:

            column = header_map["Usage (%)"]

            for row in range(2, worksheet.max_row + 1):

                cell = worksheet.cell(
                    row=row,
                    column=column
                )

                print(
                    row,
                    cell.value,
                    type(cell.value)
                )

                if cell.value is None:
                    continue

                if cell.value >= 90:

                    cell.font = Font(
                        bold=True,
                        color="C00000"
                    )

                elif cell.value >= 80:

                    cell.font = Font(
                        bold=True,
                        color="C09000"
                    )

                else:

                    cell.font = Font(
                        bold=True,
                        color="008000"
                    )

        workbook.save(output_file)

        logger.info(
            "Excel generated successfully."
        )

        return output_file