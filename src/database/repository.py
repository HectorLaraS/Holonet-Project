"""
Holonet

Database Repository
"""

from __future__ import annotations

from src.database.connection import DatabaseConnection
from src.utils.logger import get_logger
from src.database.sql_loader import SQLLoader
from datetime import datetime, timezone
import statistics
from collections import defaultdict
from src.config.settings import settings
import math
from decimal import Decimal


logger = get_logger(__name__)


class Repository:
    """
    Handles all database operations.
    """

    def save_products(
        self,
        products: dict
    ) -> None:
        """
        Saves the Starlink products catalog.
        """

        results = products["content"]["results"]

        logger.info(
            f"Saving {len(results)} products..."
        )

        with DatabaseConnection() as connection:

            cursor = connection.cursor()

            for product in results:

                cursor.execute(
                    """
                    MERGE starlink.products AS target
                    USING
                    (
                        SELECT
                            ? AS product_id,
                            ? AS product_reference_id,
                            ? AS product_name,
                            ? AS monthly_price,
                            ? AS currency,
                            ? AS is_sla,
                            ? AS max_user_terminals
                    ) AS source
                    ON target.product_id = source.product_id

                    WHEN MATCHED THEN
                        UPDATE SET
                            product_reference_id = source.product_reference_id,
                            product_name = source.product_name,
                            monthly_price = source.monthly_price,
                            currency = source.currency,
                            is_sla = source.is_sla,
                            max_user_terminals = source.max_user_terminals,
                            updated_at = SYSUTCDATETIME()

                    WHEN NOT MATCHED THEN

                        INSERT
                        (
                            product_id,
                            product_reference_id,
                            product_name,
                            monthly_price,
                            currency,
                            is_sla,
                            max_user_terminals
                        )

                        VALUES
                        (
                            source.product_id,
                            source.product_reference_id,
                            source.product_name,
                            source.monthly_price,
                            source.currency,
                            source.is_sla,
                            source.max_user_terminals
                        );
                    """,
                    product["productReferenceId"],
                    product["productReferenceId"],
                    product["name"],
                    product["price"],
                    product["isoCurrencyCode"],
                    product["isSla"],
                    product["maxNumberOfUserTerminals"]
                )

            connection.commit()

        logger.info(
            "Products saved successfully."
        )

    def save_service_line_details(
        self,
        service_line: dict
    ) -> None:
        """
        Saves the Service Line details.
        """

        content = service_line["content"]

        logger.info(
            f"Saving Service Line details: "
            f"{content['serviceLineNumber']}"
        )

        with DatabaseConnection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                MERGE starlink.service_line_details AS target

                USING
                (
                    SELECT
                        ? AS service_line_number,
                        ? AS nickname,
                        ? AS address_reference_id,
                        ? AS product_reference_id,
                        ? AS public_ip,
                        ? AS active,
                        ? AS start_date,
                        ? AS end_date
                ) AS source

                ON target.service_line_number = source.service_line_number

                WHEN MATCHED THEN

                    UPDATE SET

                        nickname             = source.nickname,
                        address_reference_id = source.address_reference_id,
                        product_reference_id = source.product_reference_id,
                        public_ip            = source.public_ip,
                        active               = source.active,
                        start_date           = source.start_date,
                        end_date             = source.end_date,
                        last_synced_at       = SYSUTCDATETIME()

                WHEN NOT MATCHED THEN

                    INSERT
                    (
                        service_line_number,
                        nickname,
                        address_reference_id,
                        product_reference_id,
                        public_ip,
                        active,
                        start_date,
                        end_date
                    )

                    VALUES
                    (
                        source.service_line_number,
                        source.nickname,
                        source.address_reference_id,
                        source.product_reference_id,
                        source.public_ip,
                        source.active,
                        source.start_date,
                        source.end_date
                    );
                """,
                content["serviceLineNumber"],
                content.get("nickname"),
                content.get("addressReferenceId"),
                content.get("productReferenceId"),
                content.get("publicIp"),
                content.get("active"),
                content.get("startDate"),
                content.get("endDate")
            )

            connection.commit()

        logger.info(
            f"Service Line details saved: "
            f"{content['serviceLineNumber']}"
        )

    def save_usage(
        self,
        usage: dict
    ) -> None:
        """
        Saves the current usage information.
        """

        results = usage["content"]["results"]

        logger.info(
            f"Processing {len(results)} service lines..."
        )

        with DatabaseConnection() as connection:

            cursor = connection.cursor()

            for service_line in results:

                billing_cycle = max(
                    service_line["billingCycles"],
                    key=lambda cycle: cycle["startDate"]
                )

                service_plan = service_line["servicePlan"]

                priority_gb = billing_cycle["totalPriorityGB"]

                standard_gb = billing_cycle["totalStandardGB"]

                optin_priority_gb = billing_cycle["totalOptInPriorityGB"]

                non_billable_gb = billing_cycle["totalNonBillableGB"]

                # Opt-In Priority ya está incluido dentro de Priority.
                consumed_gb = (
                    priority_gb
                    + standard_gb
                    + non_billable_gb
                )

                usage_limit = service_plan["usageLimitGB"]

                available_gb = max(
                    usage_limit - consumed_gb,
                    0
                )

                usage_percent = (
                    round((consumed_gb / usage_limit) * 100, 2)
                    if usage_limit > 0
                    else 0
                )

                billing_cycle_key = (
                    f"{service_line['serviceLineNumber']}_"
                    f"{billing_cycle['startDate'][:10]}"
                )

                self._save_current_usage(
                    cursor=cursor,
                    service_line=service_line,
                    billing_cycle=billing_cycle,
                    billing_cycle_key=billing_cycle_key,
                    consumed_gb=consumed_gb,
                    available_gb=available_gb,
                    usage_percent=usage_percent
                )

                self._save_data_blocks(
                    cursor=cursor,
                    service_line=service_line,
                    billing_cycle=billing_cycle,
                    billing_cycle_key=billing_cycle_key
                )

            connection.commit()

        logger.info(
            "Usage saved successfully."
        )

    def _save_current_usage(
        self,
        cursor,
        service_line: dict,
        billing_cycle: dict,
        billing_cycle_key: str,
        consumed_gb: float,
        available_gb: float,
        usage_percent: float
    ) -> None:
        """
        Inserts or updates the current billing cycle.
        """

        cursor.execute(
            """
            SELECT billing_cycle_key
            FROM starlink.usage_current
            WHERE service_line_number = ?
            """,
            service_line["serviceLineNumber"]
        )

        row = cursor.fetchone()

        if row is not None:

            current_billing_cycle_key = row[0]

            if current_billing_cycle_key != billing_cycle_key:

                logger.info(
                    f"Billing cycle changed for "
                    f"{service_line['serviceLineNumber']}. "
                    f"Archiving previous cycle..."
                )

                self._archive_current_usage(
                    cursor,
                    service_line["serviceLineNumber"]
                )

        cursor.execute(
            """
            MERGE starlink.usage_current AS target

            USING
            (
                SELECT
                    ? AS service_line_number,
                    ? AS account_number,
                    ? AS billing_cycle_key,
                    ? AS product_id,
                    ? AS usage_limit_gb,
                    ? AS priority_gb,
                    ? AS standard_gb,
                    ? AS optin_priority_gb,
                    ? AS non_billable_gb,
                    ? AS consumed_gb,
                    ? AS available_gb,
                    ? AS usage_percent,
                    ? AS recurring_cost,
                    ? AS overage_cost,
                    ? AS total_cost,
                    ? AS currency,
                    ? AS cycle_start,
                    ? AS cycle_end,
                    ? AS api_last_updated
            ) AS source

            ON target.service_line_number = source.service_line_number

            WHEN MATCHED THEN

                UPDATE SET

                    account_number      = source.account_number,
                    billing_cycle_key   = source.billing_cycle_key,
                    product_id          = source.product_id,
                    usage_limit_gb      = source.usage_limit_gb,
                    priority_gb         = source.priority_gb,
                    standard_gb         = source.standard_gb,
                    optin_priority_gb   = source.optin_priority_gb,
                    non_billable_gb     = source.non_billable_gb,
                    consumed_gb         = source.consumed_gb,
                    available_gb        = source.available_gb,
                    usage_percent       = source.usage_percent,
                    recurring_cost      = source.recurring_cost,
                    overage_cost        = source.overage_cost,
                    total_cost          = source.total_cost,
                    currency            = source.currency,
                    cycle_start         = source.cycle_start,
                    cycle_end           = source.cycle_end,
                    api_last_updated    = source.api_last_updated,
                    updated_at          = SYSUTCDATETIME()

            WHEN NOT MATCHED THEN

                INSERT
                (
                    service_line_number,
                    account_number,
                    billing_cycle_key,
                    product_id,
                    usage_limit_gb,
                    priority_gb,
                    standard_gb,
                    optin_priority_gb,
                    non_billable_gb,
                    consumed_gb,
                    available_gb,
                    usage_percent,
                    recurring_cost,
                    overage_cost,
                    total_cost,
                    currency,
                    cycle_start,
                    cycle_end,
                    api_last_updated
                )

                VALUES
                (
                    source.service_line_number,
                    source.account_number,
                    source.billing_cycle_key,
                    source.product_id,
                    source.usage_limit_gb,
                    source.priority_gb,
                    source.standard_gb,
                    source.optin_priority_gb,
                    source.non_billable_gb,
                    source.consumed_gb,
                    source.available_gb,
                    source.usage_percent,
                    source.recurring_cost,
                    source.overage_cost,
                    source.total_cost,
                    source.currency,
                    source.cycle_start,
                    source.cycle_end,
                    source.api_last_updated
                );
            """,
            service_line["serviceLineNumber"],
            service_line["accountNumber"],
            billing_cycle_key,
            service_line["servicePlan"]["productId"],
            service_line["servicePlan"]["usageLimitGB"],
            billing_cycle["totalPriorityGB"],
            billing_cycle["totalStandardGB"],
            billing_cycle["totalOptInPriorityGB"],
            billing_cycle["totalNonBillableGB"],
            consumed_gb,
            available_gb,
            usage_percent,
            0,
            0,
            0,
            service_line["servicePlan"]["isoCurrencyCode"],
            billing_cycle["startDate"],
            billing_cycle["endDate"],
            service_line["lastUpdated"]
        )

    def _archive_current_usage(
        self,
        cursor,
        service_line_number: str
    ) -> None:
        """
        Archives the current usage row into usage_history.
        """

        cursor.execute(
            """
            INSERT INTO starlink.usage_history
            (
                service_line_number,
                account_number,
                billing_cycle_key,
                product_id,
                usage_limit_gb,
                priority_gb,
                standard_gb,
                optin_priority_gb,
                non_billable_gb,
                consumed_gb,
                available_gb,
                usage_percent,
                recurring_cost,
                overage_cost,
                total_cost,
                currency,
                cycle_start,
                cycle_end,
                api_last_updated
            )

            SELECT
                service_line_number,
                account_number,
                billing_cycle_key,
                product_id,
                usage_limit_gb,
                priority_gb,
                standard_gb,
                optin_priority_gb,
                non_billable_gb,
                consumed_gb,
                available_gb,
                usage_percent,
                recurring_cost,
                overage_cost,
                total_cost,
                currency,
                cycle_start,
                cycle_end,
                api_last_updated

            FROM starlink.usage_current

            WHERE service_line_number = ?
            """,
            service_line_number
        )

    def _save_data_blocks(
        self,
        cursor,
        service_line: dict,
        billing_cycle: dict,
        billing_cycle_key: str
    ) -> None:
        """
        Saves the current Data Blocks.
        """

        for pool in billing_cycle["dataPoolUsage"]:

            for block in pool["dataBlocks"]:

                cursor.execute(
                    """
                    MERGE starlink.data_blocks_current AS target

                    USING
                    (
                        SELECT
                            ? AS data_block_id,
                            ? AS service_line_number,
                            ? AS billing_cycle_key,
                            ? AS product_id,
                            ? AS data_block_type,
                            ? AS total_amount_gb,
                            ? AS consumed_amount_gb,
                            ? AS remaining_amount_gb,
                            ? AS blocks_count,
                            ? AS per_block_amount_gb,
                            ? AS per_block_price,
                            ? AS total_price,
                            ? AS currency,
                            ? AS start_date,
                            ? AS expiration_date
                    ) AS source

                    ON target.data_block_id = source.data_block_id

                    WHEN MATCHED THEN

                        UPDATE SET

                            service_line_number = source.service_line_number,
                            billing_cycle_key   = source.billing_cycle_key,
                            product_id          = source.product_id,
                            data_block_type     = source.data_block_type,
                            total_amount_gb     = source.total_amount_gb,
                            consumed_amount_gb  = source.consumed_amount_gb,
                            remaining_amount_gb = source.remaining_amount_gb,
                            blocks_count        = source.blocks_count,
                            per_block_amount_gb = source.per_block_amount_gb,
                            per_block_price     = source.per_block_price,
                            total_price         = source.total_price,
                            currency            = source.currency,
                            start_date          = source.start_date,
                            expiration_date     = source.expiration_date,
                            updated_at          = SYSUTCDATETIME()

                    WHEN NOT MATCHED THEN

                        INSERT
                        (
                            data_block_id,
                            service_line_number,
                            billing_cycle_key,
                            product_id,
                            data_block_type,
                            total_amount_gb,
                            consumed_amount_gb,
                            remaining_amount_gb,
                            blocks_count,
                            per_block_amount_gb,
                            per_block_price,
                            total_price,
                            currency,
                            start_date,
                            expiration_date
                        )

                        VALUES
                        (
                            source.data_block_id,
                            source.service_line_number,
                            source.billing_cycle_key,
                            source.product_id,
                            source.data_block_type,
                            source.total_amount_gb,
                            source.consumed_amount_gb,
                            source.remaining_amount_gb,
                            source.blocks_count,
                            source.per_block_amount_gb,
                            source.per_block_price,
                            source.total_price,
                            source.currency,
                            source.start_date,
                            source.expiration_date
                        );
                    """,
                    block["dataBlockId"],
                    service_line["serviceLineNumber"],
                    billing_cycle_key,
                    block["productId"],
                    block["dataBlockType"],
                    block["totalAmountGB"],
                    block["consumedAmountGB"],
                    block["totalAmountGB"] - block["consumedAmountGB"],
                    block["blocksCount"],
                    block["perBlockAmountGB"],
                    block["perBlockPrice"],
                    block["totalPrice"],
                    block["isoCurrencyCode"],
                    block["startDateUtc"],
                    block["expirationDateUtc"]
                )

    def save_service_lines(
        self,
        account: dict,
        products: dict,
        service_lines: dict
    ) -> None:
        """
        Inserts or updates the Starlink Service Line inventory.
        """

        logger.info(
            "Saving Service Line inventory..."
        )

        #
        # Account
        #

        account_content = account["content"]

        account_number = account_content.get(
            "accountNumber"
        )

        account_name = account_content.get(
            "accountName"
        )

        region_code = account_content.get(
            "regionCode"
        )

        #
        # Products Lookup
        #

        products_lookup = {
            product["productReferenceId"]: product
            for product in products["content"]["results"]
        }

        with DatabaseConnection() as connection:

            cursor = connection.cursor()

            total = len(
                service_lines["content"]["results"]
            )

            logger.info(
                f"{total} Service Lines found."
            )

            for index, service_line in enumerate(
                service_lines["content"]["results"],
                start=1
            ):

                logger.info(
                    f"[{index}/{total}] "
                    f"{service_line['serviceLineNumber']}"
                )

                #
                # Product
                #

                product = products_lookup.get(
                    service_line.get(
                        "productReferenceId"
                    ),
                    {}
                )

                product_name = product.get(
                    "name"
                )

                currency = product.get(
                    "isoCurrencyCode"
                )

                #
                # Current Billing Cycle
                #

                current_blocks_50 = 0
                current_blocks_500 = 0

                current_contracted_gb = 0
                current_contracted_cost = 0

                #
                # Build Block Price Lookup
                #

                block_prices = {}

                for block in product.get(
                    "dataProducts",
                    {}
                ).get(
                    "dataBlockProducts",
                    []
                ):

                    block_prices[
                        block["dataAmount"]
                    ] = block["price"]

                #
                # Current Recurring Blocks
                #

                for block in service_line.get(
                    "dataBlocks",
                    {}
                ).get(
                    "recurringBlocksCurrentBillingCycle",
                    []
                ):

                    count = block.get(
                        "count",
                        0
                    )

                    data_amount = block.get(
                        "dataAmount",
                        0
                    )

                    if data_amount == 50:

                        current_blocks_50 += count

                    elif data_amount == 500:

                        current_blocks_500 += count

                    current_contracted_gb += (
                        count * data_amount
                    )

                    current_contracted_cost += (
                        count *
                        block_prices.get(
                            data_amount,
                            0
                        )
                    )

                #
                # SQL MERGE
                #

                merge_sql = """
                MERGE starlink.ServiceLine AS target
                USING
                (
                    SELECT
                        ? AS AccountNumber,
                        ? AS AccountName,
                        ? AS RegionCode,
                        ? AS ServiceLineNumber,
                        ? AS Nickname,
                        ? AS ProductReferenceId,
                        ? AS ProductName,
                        ? AS OptInProductId,
                        ? AS DelayedProductId,
                        ? AS ServiceStartDate,
                        ? AS ServiceEndDate,
                        ? AS IsPublicIp,
                        ? AS IsActive,
                        ? AS CurrentRecurringBlocks50GB,
                        ? AS CurrentRecurringBlocks500GB,
                        ? AS CurrentContractedGB,
                        ? AS CurrentContractedCost,
                        ? AS Currency,
                        ? AS AddressReferenceId,
                        SYSUTCDATETIME() AS LastCollectedAt
                ) AS source
                ON target.ServiceLineNumber = source.ServiceLineNumber
                WHEN MATCHED THEN
                    UPDATE SET
                        AccountNumber = source.AccountNumber,
                        AccountName = source.AccountName,
                        RegionCode = source.RegionCode,
                        Nickname = source.Nickname,
                        ProductReferenceId = source.ProductReferenceId,
                        ProductName = source.ProductName,
                        OptInProductId = source.OptInProductId,
                        DelayedProductId = source.DelayedProductId,
                        ServiceStartDate = source.ServiceStartDate,
                        ServiceEndDate = source.ServiceEndDate,
                        IsPublicIp = source.IsPublicIp,
                        IsActive = source.IsActive,
                        CurrentRecurringBlocks50GB = source.CurrentRecurringBlocks50GB,
                        CurrentRecurringBlocks500GB = source.CurrentRecurringBlocks500GB,
                        CurrentContractedGB = source.CurrentContractedGB,
                        CurrentContractedCost = source.CurrentContractedCost,
                        Currency = source.Currency,
                        AddressReferenceId = source.AddressReferenceId,
                        LastCollectedAt = source.LastCollectedAt,
                        UpdatedAt = SYSUTCDATETIME()
                WHEN NOT MATCHED THEN
                    INSERT
                    (
                        AccountNumber,
                        AccountName,
                        RegionCode,
                        ServiceLineNumber,
                        Nickname,
                        ProductReferenceId,
                        ProductName,
                        OptInProductId,
                        DelayedProductId,
                        ServiceStartDate,
                        ServiceEndDate,
                        IsPublicIp,
                        IsActive,
                        CurrentRecurringBlocks50GB,
                        CurrentRecurringBlocks500GB,
                        CurrentContractedGB,
                        CurrentContractedCost,
                        Currency,
                        AddressReferenceId,
                        LastCollectedAt
                    )
                    VALUES
                    (
                        source.AccountNumber,
                        source.AccountName,
                        source.RegionCode,
                        source.ServiceLineNumber,
                        source.Nickname,
                        source.ProductReferenceId,
                        source.ProductName,
                        source.OptInProductId,
                        source.DelayedProductId,
                        source.ServiceStartDate,
                        source.ServiceEndDate,
                        source.IsPublicIp,
                        source.IsActive,
                        source.CurrentRecurringBlocks50GB,
                        source.CurrentRecurringBlocks500GB,
                        source.CurrentContractedGB,
                        source.CurrentContractedCost,
                        source.Currency,
                        source.AddressReferenceId,
                        source.LastCollectedAt
                    );
                """

                cursor.execute(
                    merge_sql,
                    (
                        account_number,
                        account_name,
                        region_code,
                        service_line.get("serviceLineNumber"),
                        service_line.get("nickname"),
                        service_line.get("productReferenceId"),
                        product_name,
                        service_line.get("optInProductId"),
                        service_line.get("delayedProductId"),
                        service_line.get("startDate"),
                        service_line.get("endDate"),
                        service_line.get("publicIp"),
                        service_line.get("active"),
                        current_blocks_50,
                        current_blocks_500,
                        current_contracted_gb,
                        current_contracted_cost,
                        currency,
                        service_line.get("addressReferenceId")
                    )
                )

            connection.commit()

        logger.info(
            "Service Line inventory saved successfully."
        )
    
    def save_usage_history(
        self,
        records: list[tuple]
    ) -> None:
        """
        Saves Service Line Usage History into SQL Server.
        """

        if not records:

            logger.warning(
                "No Service Line Usage History records to save."
            )

            return

        logger.info(
            "Saving %s Service Line Usage History records...",
            len(records)
        )

        merge_sql = SQLLoader.load(
            "merge_service_line_usage_history.sql"
        )

        with DatabaseConnection() as connection:

            cursor = connection.cursor()

            ##cursor.fast_executemany = True

            record = records[0]

            for i, value in enumerate(record, start=1):

                if isinstance(value, str):

                    print(
                        f"{i:02d} | {len(value):3d} | {value}"
                    )

            cursor.executemany(
                merge_sql,
                records
            )

            connection.commit()

        logger.info(
            "Service Line Usage History saved successfully."
        )

    def get_service_line_id(
        self,
        service_line_number: str
    ) -> int | None:
        """
        Returns the ServiceLineId for a Service Line Number.
        """

        with DatabaseConnection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    ServiceLineId
                FROM
                    starlink.ServiceLine
                WHERE
                    ServiceLineNumber = ?
                """,
                service_line_number
            )

            row = cursor.fetchone()

            if row is None:

                return None

            return row.ServiceLineId


    def build_usage_history_records(
        self,
        account: dict,
        history: dict
    ) -> list[tuple]:
        """
        Builds SQL-ready records from the Starlink usage history response.
        """

        logger.info(
            "Building Service Line Usage History records..."
        )

        records = []

        account_number = account["content"]["accountNumber"]

        for service_line in history.get("results", []):

            service_line_number = service_line.get(
                "serviceLineNumber"
            )

            service_line_id = self.get_service_line_id(
                service_line_number
            )

            if service_line_id is None:

                logger.warning(
                    "Service Line %s not found in database.",
                    service_line_number
                )

                continue

            source_last_updated = service_line.get(
                "lastUpdated"
            )

            for billing_cycle in service_line.get(
                "billingCycles",
                []
            ):

                contracted_gb = 0
                contracted_cost = 0
                topup_count = 0
                topup_capacity_gb = 0
                topup_cost = 0
                currency = None

                for pool in billing_cycle.get(
                    "dataPoolUsage",
                    []
                ):

                    for block in pool.get(
                        "dataBlocks",
                        []
                    ):

                        currency = block.get(
                            "isoCurrencyCode"
                        )

                        block_type = block.get(
                            "dataBlockType"
                        )

                        if (
                            block_type
                            == "RecurringPerBillingCycle"
                        ):

                            contracted_gb += (
                                block.get(
                                    "totalAmountGB",
                                    0
                                ) or 0
                            )

                            contracted_cost += (
                                block.get(
                                    "totalPrice",
                                    0
                                ) or 0
                            )

                        else:

                            topup_count += (
                                block.get(
                                    "blocksCount",
                                    0
                                ) or 0
                            )

                            topup_capacity_gb += (
                                block.get(
                                    "totalAmountGB",
                                    0
                                ) or 0
                            )

                            topup_cost += (
                                block.get(
                                    "totalPrice",
                                    0
                                ) or 0
                            )

                priority_gb = (
                    billing_cycle.get(
                        "totalPriorityGB",
                        0
                    ) or 0
                )

                standard_gb = (
                    billing_cycle.get(
                        "totalStandardGB",
                        0
                    ) or 0
                )

                opt_in_priority_gb = (
                    billing_cycle.get(
                        "totalOptInPriorityGB",
                        0
                    ) or 0
                )

                non_billable_gb = (
                    billing_cycle.get(
                        "totalNonBillableGB",
                        0
                    ) or 0
                )

                total_usage_gb = (
                    priority_gb
                    + standard_gb
                    + non_billable_gb
                )

                topup_used_gb = max(
                    priority_gb - contracted_gb,
                    0
                )

                topup_remaining_gb = max(
                    topup_capacity_gb - topup_used_gb,
                    0
                )

                original_budget = contracted_cost

                additional_spend = topup_cost

                total_cycle_spend = (
                    original_budget
                    + additional_spend
                )

                contract_usage_percent = (
                    round((priority_gb / contracted_gb) * 100, 2)
                    if contracted_gb > 0
                    else 0
                )

                consumption_variance_gb = (
                    total_usage_gb - contracted_gb
                )

                has_topups = topup_count > 0

                budget_variance = (
                    total_cycle_spend - original_budget
                )

                records.append(
                    (
                        service_line_id,
                        account_number,
                        service_line_number,
                        billing_cycle.get("startDate"),
                        billing_cycle.get("endDate"),
                        contracted_gb,
                        contracted_cost,
                        priority_gb,
                        standard_gb,
                        opt_in_priority_gb,
                        non_billable_gb,
                        total_usage_gb,
                        contract_usage_percent,
                        consumption_variance_gb,
                        has_topups,
                        topup_count,
                        topup_capacity_gb,
                        topup_used_gb,
                        topup_remaining_gb,
                        topup_cost,
                        original_budget,
                        additional_spend,
                        total_cycle_spend,
                        budget_variance,
                        currency,
                        source_last_updated
                    )
                )

        logger.info(
            "%s billing cycle records built.",
            len(records)
        )

        return records
    
    
    def save_reporting_service_usage(
        self,
        records: list[tuple]
    ) -> None:
        """
        Rebuilds the ReportingServiceUsage table.
        """

        logger.info(
            f"Saving {len(records)} Reporting Service Usage records..."
        )

        insert_sql = SQLLoader.load(
            "refresh_reporting_service_usage.sql"
        )

        with DatabaseConnection() as connection:

            cursor = connection.cursor()

            logger.info(
                "Clearing ReportingServiceUsage table..."
            )   

            cursor.execute(
                "TRUNCATE TABLE starlink.ReportingServiceUsage;"
            )

            #
            # fast_executemany se deja deshabilitado.
            #
            # Tuvimos problemas con MERGE en SQL Server y
            # preferimos mantener un comportamiento consistente.
            #

            for record in records:

                cursor.execute(
                    insert_sql,
                    record
                )

            connection.commit()

        logger.info(
            "Reporting Service Usage updated successfully."
        )

    def build_reporting_service_usage_records(
        self
    ) -> list[tuple]:
        """
        Builds the ReportingServiceUsage dataset.

        For each Service Line, selects the current
        Billing Cycle and the previous configured
        Billing Cycles.

        Returns:
            List containing the selected billing
            cycle rows.
        """

        today = datetime.now(timezone.utc).replace(
            tzinfo=None
        )

        history_cycles = (
            settings.BILLING_CYCLES_HISTORY
        )

        selected_rows = []

        with DatabaseConnection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    sl.ServiceLineId,
                    sl.AccountNumber,
                    sl.AccountName,
                    sl.RegionCode,
                    sl.ServiceLineNumber,
                    sl.Nickname,
                    sl.ProductReferenceId,
                    sl.ProductName,
                    sl.CurrentRecurringBlocks50GB,
                    sl.CurrentRecurringBlocks500GB,

                    h.BillingCycleStart,
                    h.BillingCycleEnd,
                    h.ContractedGB,
                    h.PriorityConsumedGB,
                    h.StandardConsumedGB,
                    h.TotalConsumedGB,
                    h.ContractUsagePercent,
                    h.ConsumptionVarianceGB,
                    h.HasTopUps,
                    h.TopUpCount,
                    h.TopUpCapacityGB,
                    h.TopUpUsedGB,
                    h.TopUpRemainingGB,
                    h.TopUpCost,
                    h.OriginalBudget,
                    h.AdditionalSpend,
                    h.TotalCycleSpend,
                    h.BudgetVariance,
                    h.Currency
                FROM starlink.ServiceLineUsageHistory h
                INNER JOIN starlink.ServiceLine sl
                    ON sl.ServiceLineId = h.ServiceLineId
                ORDER BY
                    h.ServiceLineNumber,
                    h.BillingCycleStart DESC;
                """
            )

            rows = cursor.fetchall()

        #
        # Group rows by Service Line
        #

        service_lines = {}

        for row in rows:

            service_lines.setdefault(
                row.ServiceLineNumber,
                []
            ).append(row)

        #
        # Select Current Billing Cycle
        # + Previous Billing Cycles
        #

        for cycles in service_lines.values():

            current_index = None

            for index, cycle in enumerate(cycles):

                if (
                    cycle.BillingCycleStart
                    <= today
                    <= cycle.BillingCycleEnd
                ):

                    current_index = index

                    break

            if current_index is None:

                continue

            end_index = (
                current_index
                + history_cycles
                + 1
            )

            selected_cycles = cycles[
                current_index:end_index
            ]

            for billing_cycle_order, cycle in enumerate(
                selected_cycles
            ):

                if billing_cycle_order == 0:

                    billing_cycle_label = (
                        "Current Month"
                    )

                elif billing_cycle_order == 1:

                    billing_cycle_label = (
                        "Last Month"
                    )

                else:

                    billing_cycle_label = (
                        f"Month -{billing_cycle_order}"
                    )

                is_current_billing_cycle = (
                    billing_cycle_order == 0
                )

                selected_rows.append(
                    (
                        cycle.AccountNumber,
                        cycle.AccountName,
                        cycle.RegionCode,
                        cycle.ServiceLineNumber,
                        cycle.Nickname,
                        cycle.ProductReferenceId,
                        cycle.ProductName,
                        cycle.CurrentRecurringBlocks50GB,
                        cycle.CurrentRecurringBlocks500GB,
                        cycle.BillingCycleStart,
                        cycle.BillingCycleEnd,
                        billing_cycle_order,
                        billing_cycle_label,
                        is_current_billing_cycle,
                        cycle.ContractedGB,
                        cycle.PriorityConsumedGB,
                        cycle.StandardConsumedGB,
                        cycle.TotalConsumedGB,
                        cycle.ContractUsagePercent,
                        cycle.ConsumptionVarianceGB,
                        cycle.HasTopUps,
                        cycle.TopUpCount,
                        cycle.TopUpCapacityGB,
                        cycle.TopUpUsedGB,
                        cycle.TopUpRemainingGB,
                        cycle.TopUpCost,
                        cycle.OriginalBudget,
                        cycle.AdditionalSpend,
                        cycle.TotalCycleSpend,
                        cycle.BudgetVariance,
                        cycle.Currency
                    )
                )

        return selected_rows
    
    def get_service_line_history(
        self
    ) -> dict[str, list]:
        """
        Retrieves the Billing Cycle history grouped by
        Service Line.

        Returns:
            Dictionary where the key is the
            ServiceLineNumber and the value is the list
            of Billing Cycles ordered from newest to oldest.
        """

        with DatabaseConnection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    sl.ServiceLineId,
                    sl.AccountNumber,
                    sl.AccountName,
                    sl.RegionCode,
                    sl.ServiceLineNumber,
                    sl.Nickname,
                    sl.Currency,
                    sl.CurrentRecurringBlocks500GB,
                    sl.CurrentContractedCost,

                    h.BillingCycleStart,
                    h.BillingCycleEnd,
                    h.ContractedGB,
                    h.ContractedCost,
                    h.PriorityConsumedGB,
                    h.StandardConsumedGB,
                    h.TotalConsumedGB,
                    h.ContractUsagePercent,
                    h.ConsumptionVarianceGB,
                    h.HasTopUps,
                    h.TopUpCount,
                    h.TopUpCapacityGB,
                    h.TopUpUsedGB,
                    h.TopUpRemainingGB,
                    h.TopUpCost,
                    h.OriginalBudget,
                    h.AdditionalSpend,
                    h.TotalCycleSpend,
                    h.BudgetVariance
                FROM starlink.ServiceLineUsageHistory h
                INNER JOIN starlink.ServiceLine sl
                    ON sl.ServiceLineId = h.ServiceLineId
                ORDER BY
                    h.ServiceLineNumber,
                    h.BillingCycleStart DESC
                """
            )

            rows = cursor.fetchall()

        history = {}

        for row in rows:

            history.setdefault(
                row.ServiceLineNumber,
                []
            ).append(row)

        return history
    
    def calculate_consumption_statistics(
        self,
        billing_cycles: list
    ) -> dict:
        """
        Calculates consumption statistics for a
        Service Line.

        Args:
            billing_cycles:
                Billing Cycle history for a
                single Service Line.

        Returns:
            Dictionary containing consumption
            statistics.
        """

        import statistics

        consumptions = [
            cycle.TotalConsumedGB
            for cycle in billing_cycles
        ]

        contracted = [
            cycle.ContractedGB
            for cycle in billing_cycles
        ]

        usage_percent = [
            cycle.ContractUsagePercent
            for cycle in billing_cycles
        ]

        if len(consumptions) > 1:

            consumption_variance = (
                statistics.variance(
                    consumptions
                )
            )

            consumption_std_dev = (
                statistics.stdev(
                    consumptions
                )
            )

        else:

            consumption_variance = 0

            consumption_std_dev = 0

        return {
            "minimum_consumption_gb":
                min(consumptions),

            "maximum_consumption_gb":
                max(consumptions),

            "average_consumption_gb":
                statistics.mean(
                    consumptions
                ),

            "consumption_variance":
                consumption_variance,

            "consumption_standard_deviation_gb":
                consumption_std_dev,

            "average_contracted_gb":
                statistics.mean(
                    contracted
                ),

            "average_usage_percent":
                statistics.mean(
                    usage_percent
                )
        }
    
    def calculate_topup_statistics(
        self,
        billing_cycles: list
    ) -> dict:
        """
        Calculates Top-Up statistics for a
        Service Line.

        Args:
            billing_cycles:
                Billing Cycle history for a
                single Service Line.

        Returns:
            Dictionary containing Top-Up
            statistics.
        """

        topup_counts = [
            cycle.TopUpCount
            for cycle in billing_cycles
        ]

        topup_capacity = [
            cycle.TopUpCapacityGB
            for cycle in billing_cycles
        ]

        topup_used = [
            cycle.TopUpUsedGB
            for cycle in billing_cycles
        ]

        topup_cost = [
            cycle.TopUpCost
            for cycle in billing_cycles
        ]

        billing_cycles_with_topups = sum(
            1
            for cycle in billing_cycles
            if cycle.HasTopUps
        )

        if len(topup_cost) > 1:

            topup_cost_variance = (
                statistics.variance(
                    topup_cost
                )
            )

            topup_cost_std_dev = (
                statistics.stdev(
                    topup_cost
                )
            )

        else:

            topup_cost_variance = 0

            topup_cost_std_dev = 0

        return {

            "billing_cycles_with_topups":
                billing_cycles_with_topups,

            "average_topup_count":
                statistics.mean(
                    topup_counts
                ),

            "average_topup_capacity_gb":
                statistics.mean(
                    topup_capacity
                ),

            "average_topup_used_gb":
                statistics.mean(
                    topup_used
                ),

            "average_topup_cost":
                statistics.mean(
                    topup_cost
                ),

            "topup_cost_variance":
                topup_cost_variance,

            "topup_cost_standard_deviation":
                topup_cost_std_dev
        }
    
    def calculate_financial_statistics(
        self,
        billing_cycles: list
    ) -> dict:
        """
        Calculates financial statistics for a
        Service Line.

        Args:
            billing_cycles:
                Billing Cycle history for a
                single Service Line.

        Returns:
            Dictionary containing financial
            statistics.
        """

        original_budget = [
            cycle.OriginalBudget
            for cycle in billing_cycles
        ]

        additional_spend = [
            cycle.AdditionalSpend
            for cycle in billing_cycles
        ]

        total_cycle_spend = [
            cycle.TotalCycleSpend
            for cycle in billing_cycles
        ]

        if len(additional_spend) > 1:

            additional_spend_variance = (
                statistics.variance(
                    additional_spend
                )
            )

            additional_spend_std_dev = (
                statistics.stdev(
                    additional_spend
                )
            )

        else:

            additional_spend_variance = 0

            additional_spend_std_dev = 0

        return {

            "average_original_budget":
                statistics.mean(
                    original_budget
                ),

            "average_additional_spend":
                statistics.mean(
                    additional_spend
                ),

            "additional_spend_variance":
                additional_spend_variance,

            "additional_spend_standard_deviation":
                additional_spend_std_dev,

            "average_total_cycle_spend":
                statistics.mean(
                    total_cycle_spend
                )
        }
    
    def get_recurring_block_price(
        self,
        region_code: str
    ) -> float:
        """
        Returns the configured price for a
        recurring 500 GB block.
        """

        if region_code == "US":
            return Decimal(str(settings.STARLINK_US_500GB_PRICE))

        if region_code == "CA":
            return Decimal(str(settings.STARLINK_CA_500GB_PRICE))

        if region_code == "MX":
            return Decimal(str(settings.STARLINK_MX_500GB_PRICE))

        return 0

    def get_confidence_level(
        self,
        average_consumption: float,
        standard_deviation: float
    ) -> str:
        """
        Determines the confidence level for the
        capacity recommendation.

        Args:
            average_consumption:
                Average consumption in GB.

            standard_deviation:
                Consumption standard deviation in GB.

        Returns:
            HIGH, MEDIUM or LOW.
        """

        if average_consumption <= 0:
            return "LOW"

        coefficient_of_variation = (
            standard_deviation /
            average_consumption
        )

        if (
            coefficient_of_variation
            <= settings.ANALYTICS_HIGH_CONFIDENCE_THRESHOLD
        ):
            return "HIGH"

        if (
            coefficient_of_variation
            <= settings.ANALYTICS_MEDIUM_CONFIDENCE_THRESHOLD
        ):
            return "MEDIUM"

        return "LOW"
    
    def requires_operational_review(
        self,
        average_topup_count: float
    ) -> bool:
        """
        Determines whether the Service Line
        requires operational review.
        """

        return (
            average_topup_count >=
            settings.ANALYTICS_OPERATIONAL_REVIEW_MIN_TOPUPS
        )
    
    def calculate_capacity_recommendation(
        self,
        billing_cycles: list,
        consumption_statistics: dict,
        topup_statistics: dict
    ) -> dict:
        """
        Calculates the capacity recommendation for a
        Service Line.

        Args:
            billing_cycles:
                Billing Cycle history for a
                single Service Line.

            consumption_statistics:
                Consumption statistics previously
                calculated.

            topup_statistics:
                Top-Up statistics previously
                calculated.

        Returns:
            Dictionary containing the capacity
            recommendation.
        """

        average_consumption = (
            consumption_statistics[
                "average_consumption_gb"
            ]
        )

        recommended_blocks = math.ceil(
            average_consumption /
            settings.ANALYTICS_RECURRING_BLOCK_SIZE_GB
        )

        recommended_capacity = (
            recommended_blocks *
            settings.ANALYTICS_RECURRING_BLOCK_SIZE_GB
        )

        region_code = billing_cycles[0].RegionCode

        recurring_block_cost = (
            self.get_recurring_block_price(
                region_code
            )
        )

        estimated_recurring_cost = (
            recommended_blocks *
            recurring_block_cost
        )

        estimated_monthly_savings = (
            topup_statistics[
                "average_topup_cost"
            ]
            -
            estimated_recurring_cost
        )

        estimated_annual_savings = (
            estimated_monthly_savings *
            settings.ANALYTICS_MONTHS_PER_YEAR
        )

        confidence_level = (
            self.get_confidence_level(
                average_consumption,
                consumption_statistics[
                    "consumption_standard_deviation_gb"
                ]
            )
        )

        operational_review = (
            self.requires_operational_review(
                topup_statistics[
                    "average_topup_count"
                ]
            )
        )

        recommendation = (
            f"Add {recommended_blocks} recurring "
            f"500 GB blocks."
        )

        recommendation_reason = (
            "Recommendation based on average "
            "historical consumption."
        )

        return {

            "recommended_recurring_blocks":
                recommended_blocks,

            "recommended_recurring_capacity_gb":
                recommended_capacity,

            "estimated_recurring_blocks_cost":
                estimated_recurring_cost,

            "estimated_monthly_savings":
                estimated_monthly_savings,

            "estimated_annual_savings":
                estimated_annual_savings,

            "recommendation":
                recommendation,

            "recommendation_reason":
                recommendation_reason,

            "confidence_level":
                confidence_level,

            "requires_operational_review":
                operational_review
        }
    
    def build_analytics_record(
        self,
        billing_cycles: list,
        consumption_statistics: dict,
        topup_statistics: dict,
        financial_statistics: dict,
        recommendation: dict
    ) -> tuple:
        """
        Builds a ServiceLineAnalytics record.
        """

        current = billing_cycles[0]

        return (

            # --------------------------------------------------------------
            # Identification
            # --------------------------------------------------------------

            current.ServiceLineId,

            current.AccountNumber,
            current.AccountName,
            current.RegionCode,

            current.ServiceLineNumber,
            current.Nickname,

            current.Currency,

            # --------------------------------------------------------------
            # Analysis period
            # --------------------------------------------------------------

            settings.BILLING_CYCLES_HISTORY,

            len(billing_cycles),

            billing_cycles[-1].BillingCycleStart,
            billing_cycles[0].BillingCycleEnd,

            # --------------------------------------------------------------
            # Consumption statistics
            # --------------------------------------------------------------

            consumption_statistics["minimum_consumption_gb"],
            consumption_statistics["maximum_consumption_gb"],
            consumption_statistics["average_consumption_gb"],
            consumption_statistics["consumption_variance"],
            consumption_statistics[
                "consumption_standard_deviation_gb"
            ],
            consumption_statistics["average_contracted_gb"],
            consumption_statistics["average_usage_percent"],

            # --------------------------------------------------------------
            # Top-Up statistics
            # --------------------------------------------------------------

            topup_statistics[
                "billing_cycles_with_topups"
            ],
            topup_statistics["average_topup_count"],
            topup_statistics["average_topup_capacity_gb"],
            topup_statistics["average_topup_used_gb"],
            topup_statistics["average_topup_cost"],
            topup_statistics["topup_cost_variance"],
            topup_statistics[
                "topup_cost_standard_deviation"
            ],

            # --------------------------------------------------------------
            # Financial statistics
            # --------------------------------------------------------------

            financial_statistics[
                "average_original_budget"
            ],
            financial_statistics[
                "average_additional_spend"
            ],
            financial_statistics[
                "additional_spend_variance"
            ],
            financial_statistics[
                "additional_spend_standard_deviation"
            ],
            financial_statistics[
                "average_total_cycle_spend"
            ],

            # --------------------------------------------------------------
            # Recommendation
            # --------------------------------------------------------------

            recommendation[
                "recommended_recurring_blocks"
            ],
            recommendation[
                "recommended_recurring_capacity_gb"
            ],
            recommendation[
                "estimated_recurring_blocks_cost"
            ],
            recommendation[
                "estimated_monthly_savings"
            ],
            recommendation[
                "estimated_annual_savings"
            ],

            recommendation["recommendation"],
            recommendation["recommendation_reason"],
            recommendation["confidence_level"],

            recommendation[
                "requires_operational_review"
            ]
        )
    
    def build_service_line_analytics_records(
        self
    ) -> list[tuple]:
        """
        Builds ServiceLineAnalytics records.
        """

        logger.info(
            "Building Service Line Analytics records..."
        )

        history = self.get_service_line_history()

        records = []

        for billing_cycles in history.values():

            consumption_statistics = (
                self.calculate_consumption_statistics(
                    billing_cycles
                )
            )

            topup_statistics = (
                self.calculate_topup_statistics(
                    billing_cycles
                )
            )

            financial_statistics = (
                self.calculate_financial_statistics(
                    billing_cycles
                )
            )

            recommendation = (
                self.calculate_capacity_recommendation(
                    billing_cycles,
                    consumption_statistics,
                    topup_statistics
                )
            )

            records.append(
                self.build_analytics_record(
                    billing_cycles,
                    consumption_statistics,
                    topup_statistics,
                    financial_statistics,
                    recommendation
                )
            )

        logger.info(
            f"Built {len(records)} Service Line Analytics records."
        )

        return records
    
    def save_service_line_analytics(
            self,
            records: list[tuple]
        ) -> None:
        """
        Rebuilds the ServiceLineAnalytics table.
        """

        logger.info(
            f"Saving {len(records)} Service Line Analytics records..."
        )

        insert_sql = SQLLoader.load(
            "refresh_service_line_analytics.sql"
        )

        with DatabaseConnection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                "TRUNCATE TABLE starlink.ServiceLineAnalytics;"
            )

            #
            # fast_executemany is intentionally disabled.
            #
            # We prefer a consistent behavior across all
            # database operations.
            #

            for record in records:

                cursor.execute(
                    insert_sql,
                    record
                )

            connection.commit()

        logger.info(
            "Service Line Analytics updated successfully."
        )