------------------------------------------------------------------------------
-- Populate reporting table
------------------------------------------------------------------------------

INSERT INTO starlink.ReportingServiceUsage
(
    --------------------------------------------------------------------------
    -- Administrative
    --------------------------------------------------------------------------

    AccountNumber,
    AccountName,
    RegionCode,

    ServiceLineNumber,
    Nickname,

    ProductReferenceId,
    ProductName,

    CurrentRecurringBlocks50GB,
    CurrentRecurringBlocks500GB,

    --------------------------------------------------------------------------
    -- Billing Cycle
    --------------------------------------------------------------------------

    BillingCycleStart,
    BillingCycleEnd,

    BillingCycleOrder,
    BillingCycleLabel,

    IsCurrentBillingCycle,

    --------------------------------------------------------------------------
    -- Consumption
    --------------------------------------------------------------------------

    ContractedGB,
    PriorityConsumedGB,
    StandardConsumedGB,
    TotalConsumedGB,

    ContractUsagePercent,
    ConsumptionVarianceGB,

    --------------------------------------------------------------------------
    -- Top-Ups
    --------------------------------------------------------------------------

    HasTopUps,
    TopUpCount,
    TopUpCapacityGB,
    TopUpUsedGB,
    TopUpRemainingGB,
    TopUpCost,

    --------------------------------------------------------------------------
    -- Financial
    --------------------------------------------------------------------------

    OriginalBudget,
    AdditionalSpend,
    TotalCycleSpend,
    BudgetVariance,

    Currency
)
VALUES
(
    ?,
    ?,
    ?,

    ?,
    ?,

    ?,
    ?,

    ?,
    ?,

    ?,
    ?,

    ?,
    ?,

    ?,

    ?,
    ?,
    ?,
    ?,

    ?,
    ?,

    ?,
    ?,
    ?,
    ?,
    ?,
    ?,

    ?,
    ?,
    ?,
    ?,

    ?
);