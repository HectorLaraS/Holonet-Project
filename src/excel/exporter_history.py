"""
Holonet

History Excel Exporter (Version 1)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

from src.utils.logger import get_logger

logger = get_logger(__name__)


class HistoryExporter:

    def __init__(self, usage_data: dict):
        self.usage_data = usage_data

    def build_dataframe(self) -> pd.DataFrame:
        rows = []

        for service in self.usage_data["content"]["results"]:

            row = {
                "Account Number": service.get("accountNumber"),
                "Service Line": service.get("serviceLineNumber"),
                "Nickname": service.get("nickname", ""),
                "Plan": service.get("productReferenceId", ""),
            }

            billing_cycles = sorted(
                service.get("billingCycles", []),
                key=lambda x: x["startDate"],
                reverse=True
            )

            labels = ["Current Month", "Last Month", "Month -2", "Month -3"]

            for label, cycle in zip(labels, billing_cycles):

                contracted = 0.0
                topup_qty = 0
                topup_capacity = 0.0
                topup_used = 0.0
                topup_cost = 0.0

                for pool in cycle.get("dataPoolUsage", []):
                    for block in pool.get("dataBlocks", []):
                        t = block.get("dataBlockType")

                        if t == "RecurringPerBillingCycle":
                            contracted += block.get("totalAmountGB", 0)

                        elif t == "Overage":
                            topup_qty += block.get("blocksCount", 0)
                            topup_capacity += block.get("totalAmountGB", 0)
                            topup_used += block.get("consumedAmountGB", 0)
                            topup_cost += block.get("totalPrice", 0)

                consumed = cycle.get("totalPriorityGB", 0)

                usage = round(consumed * 100 / contracted, 2) if contracted else 0

                row[f"{label} Contracted (GB)"] = contracted
                row[f"{label} Used (GB)"] = consumed
                row[f"{label} Usage (%)"] = usage
                row[f"{label} TopUps"] = topup_qty
                row[f"{label} TopUp Capacity (GB)"] = topup_capacity
                row[f"{label} TopUp Used (GB)"] = topup_used
                row[f"{label} TopUp Remaining (GB)"] = topup_capacity - topup_used
                row[f"{label} TopUp Cost"] = topup_cost

            rows.append(row)

        return pd.DataFrame(rows)

    def export_report(self) -> Path:

        dataframe = self.build_dataframe()

        exports_folder = Path("exports") / "history"
        exports_folder.mkdir(parents=True, exist_ok=True)

        output_file = exports_folder / (
            f"Holonet_History_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        )

        dataframe.to_excel(output_file, index=False)

        workbook = load_workbook(output_file)
        worksheet = workbook.active

        fill = PatternFill(fill_type="solid", start_color="C32032", end_color="C32032")
        font = Font(bold=True, color="FFFFFF")
        align = Alignment(horizontal="center", vertical="center")

        for cell in worksheet[1]:
            cell.fill = fill
            cell.font = font
            cell.alignment = align

        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions

        workbook.save(output_file)

        return output_file
