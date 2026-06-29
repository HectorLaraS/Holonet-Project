/*
===============================================================================
Holonet
Service Line Summary Dataset

Version: 3

Purpose:
    Consolidated dataset used by:
        - Power BI
        - Excel Exporter

Notes:
    - current_usage_percent is the percentage reported by Starlink.
    - contract_usage_percent is calculated by Holonet against contracted capacity.
    - contract_usage_percent is truncated to 2 decimals.
===============================================================================
*/

WITH BlockSummary AS
(
    SELECT

        service_line_number,
        billing_cycle_key,

        ----------------------------------------------------------------------
        -- Contracted Capacity
        ----------------------------------------------------------------------

        SUM(
            CASE
                WHEN data_block_type = 'RecurringPerBillingCycle'
                THEN total_amount_gb
                ELSE 0
            END
        ) AS contracted_capacity_gb,

        ----------------------------------------------------------------------
        -- Top Ups
        ----------------------------------------------------------------------

        SUM(
            CASE
                WHEN data_block_type = 'Overage'
                THEN blocks_count
                ELSE 0
            END
        ) AS topup_quantity,

        SUM(
            CASE
                WHEN data_block_type = 'Overage'
                THEN total_amount_gb
                ELSE 0
            END
        ) AS topup_capacity_gb,

        SUM(
            CASE
                WHEN data_block_type = 'Overage'
                THEN consumed_amount_gb
                ELSE 0
            END
        ) AS topup_consumed_gb,

        SUM(
            CASE
                WHEN data_block_type = 'Overage'
                THEN remaining_amount_gb
                ELSE 0
            END
        ) AS topup_remaining_gb,

        SUM(
            CASE
                WHEN data_block_type = 'Overage'
                THEN total_price
                ELSE 0
            END
        ) AS topup_cost

    FROM starlink.data_blocks_current

    GROUP BY

        service_line_number,
        billing_cycle_key
),

ServiceLineSummary AS
(
    SELECT

        ----------------------------------------------------------------------
        -- Keys
        ----------------------------------------------------------------------

        u.service_line_number,
        u.billing_cycle_key,

        ----------------------------------------------------------------------
        -- Service Line
        ----------------------------------------------------------------------

        s.nickname,

        u.account_number,

        u.cycle_start,
        u.cycle_end,

        ----------------------------------------------------------------------
        -- Product
        ----------------------------------------------------------------------

        u.product_id,

        p.product_name,

        ----------------------------------------------------------------------
        -- Capacity
        ----------------------------------------------------------------------

        ISNULL(
            b.contracted_capacity_gb,
            0
        ) AS contracted_capacity_gb,

        ISNULL(
            b.topup_capacity_gb,
            0
        ) AS topup_capacity_gb,

        ISNULL(
            b.contracted_capacity_gb,
            0
        )
        +
        ISNULL(
            b.topup_capacity_gb,
            0
        ) AS total_capacity_gb,

        ----------------------------------------------------------------------
        -- Usage
        ----------------------------------------------------------------------

        u.consumed_gb AS total_consumed_gb,

        u.available_gb,

        CAST(
            u.usage_percent
            AS DECIMAL(10,2)
        ) AS current_usage_percent,

        CASE

            WHEN ISNULL(
                b.contracted_capacity_gb,
                0
            ) = 0

            THEN CAST(
                0.00
                AS DECIMAL(10,2)
            )

            ELSE CAST(

                ROUND(

                    (u.consumed_gb * 100.0)
                    / b.contracted_capacity_gb,

                    2,
                    1

                )

                AS DECIMAL(10,2)

            )

        END AS contract_usage_percent,

        ----------------------------------------------------------------------
        -- Top Ups
        ----------------------------------------------------------------------

        ISNULL(
            b.topup_quantity,
            0
        ) AS topup_quantity,

        ISNULL(
            b.topup_consumed_gb,
            0
        ) AS topup_consumed_gb,

        ISNULL(
            b.topup_remaining_gb,
            0
        ) AS topup_remaining_gb,

        ISNULL(
            b.topup_cost,
            0
        ) AS topup_cost,

        CASE

            WHEN ISNULL(
                b.topup_quantity,
                0
            ) > 0

            THEN CAST(1 AS BIT)

            ELSE CAST(0 AS BIT)

        END AS topup_required,

        ----------------------------------------------------------------------
        -- Billing
        ----------------------------------------------------------------------

        u.recurring_cost,

        u.currency,

        ----------------------------------------------------------------------
        -- Current Status (Starlink)
        ----------------------------------------------------------------------

        CASE

            WHEN u.usage_percent >= 90
                THEN 'Critical'

            WHEN u.usage_percent >= 80
                THEN 'Warning'

            ELSE 'Normal'

        END AS current_status,

        ----------------------------------------------------------------------
        -- Contract Status (Holonet)
        ----------------------------------------------------------------------

        CASE

            WHEN ISNULL(
                b.contracted_capacity_gb,
                0
            ) = 0

            THEN 'Normal'

            WHEN

                (u.consumed_gb * 100.0)

                / b.contracted_capacity_gb

                >= 100

            THEN 'Critical'

            WHEN

                (u.consumed_gb * 100.0)

                / b.contracted_capacity_gb

                >= 80

            THEN 'Warning'

            ELSE 'Normal'

        END AS contract_status,

        ----------------------------------------------------------------------
        -- Audit
        ----------------------------------------------------------------------

        GETDATE() AS last_updated

    FROM starlink.usage_current u

    LEFT JOIN starlink.products p

        ON u.product_id = p.product_id

    LEFT JOIN starlink.service_line_details s

        ON u.service_line_number = s.service_line_number

    LEFT JOIN BlockSummary b

        ON u.service_line_number = b.service_line_number

       AND u.billing_cycle_key = b.billing_cycle_key
)

SELECT *

FROM ServiceLineSummary

ORDER BY

    nickname,
    service_line_number;
