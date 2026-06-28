"""
Holonet

SQL queries for reports.
"""

REPORT_QUERY = """
SELECT

    u.account_number,
    u.service_line_number,

    p.product_name,

    u.product_id,

    u.billing_cycle_key,
    u.cycle_start,
    u.cycle_end,

    u.usage_limit_gb,

    u.priority_gb,
    u.standard_gb,

    u.consumed_gb,
    u.available_gb,
    u.usage_percent,

    u.recurring_cost,

    d.data_block_type,
    d.blocks_count,
    d.per_block_amount_gb,
    d.total_amount_gb,
    d.consumed_amount_gb,
    d.remaining_amount_gb,
    d.per_block_price,
    d.total_price,

    u.currency

FROM starlink.usage_current u

LEFT JOIN starlink.products p

    ON u.product_id = p.product_id

LEFT JOIN starlink.data_blocks_current d

    ON u.service_line_number = d.service_line_number

ORDER BY

    u.account_number,
    u.service_line_number;
"""