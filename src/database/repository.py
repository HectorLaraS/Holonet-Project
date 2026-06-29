"""
Holonet

Database Repository
"""

from __future__ import annotations

from src.database.connection import DatabaseConnection
from src.utils.logger import get_logger

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