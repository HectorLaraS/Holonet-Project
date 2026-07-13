------------------------------------------------------------------------------
-- Holonet
--
-- File:
-- refresh_service_line_analytics.sql
--
-- Description:
-- Rebuilds the ServiceLineAnalytics table.
--
-- Refresh strategy:
-- TRUNCATE and reload.
------------------------------------------------------------------------------

SET NOCOUNT ON;

------------------------------------------------------------------------------
-- Populate analytics table
------------------------------------------------------------------------------

INSERT INTO starlink.ServiceLineAnalytics
(
    --------------------------------------------------------------------------
    -- Identification
    --------------------------------------------------------------------------

    ServiceLineId,

    AccountNumber,
    AccountName,
    RegionCode,

    ServiceLineNumber,
    Nickname,

    Currency,

    --------------------------------------------------------------------------
    -- Analysis period
    --------------------------------------------------------------------------

    RequestedPreviousBillingCycles,
    BillingCyclesAnalyzed,

    AnalysisPeriodStart,
    AnalysisPeriodEnd,

    --------------------------------------------------------------------------
    -- Consumption statistics
    --------------------------------------------------------------------------

    MinimumConsumptionGB,
    MaximumConsumptionGB,
    AverageConsumptionGB,
    ConsumptionVariance,
    ConsumptionStandardDeviationGB,
    AverageContractedGB,
    AverageUsagePercent,

    --------------------------------------------------------------------------
    -- Top-Up statistics
    --------------------------------------------------------------------------

    BillingCyclesWithTopUps,
    AverageTopUpCount,
    AverageTopUpCapacityGB,
    AverageTopUpUsedGB,
    AverageTopUpCost,
    TopUpCostVariance,
    TopUpCostStandardDeviation,

    --------------------------------------------------------------------------
    -- Financial statistics
    --------------------------------------------------------------------------

    AverageOriginalBudget,
    AverageAdditionalSpend,
    AdditionalSpendVariance,
    AdditionalSpendStandardDeviation,
    AverageTotalCycleSpend,

    --------------------------------------------------------------------------
    -- Capacity recommendation
    --------------------------------------------------------------------------

    RecommendedRecurringBlocks500GB,
    RecommendedRecurringCapacityGB,
    EstimatedRecurringBlocksCost,
    EstimatedMonthlySavings,
    EstimatedAnnualSavings,

    --------------------------------------------------------------------------
    -- Recommendation explanation
    --------------------------------------------------------------------------

    Recommendation,
    RecommendationReason,
    ConfidenceLevel,

    RequiresOperationalReview
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