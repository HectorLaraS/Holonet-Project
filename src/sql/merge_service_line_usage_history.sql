------------------------------------------------------------------------------
-- Holonet
--
-- File:
-- merge_service_line_usage_history.sql
--
-- Description:
-- Inserts or updates historical Starlink billing-cycle information.
--
-- Target:
-- starlink.ServiceLineUsageHistory
------------------------------------------------------------------------------

SET NOCOUNT ON;

MERGE starlink.ServiceLineUsageHistory AS target
USING
(
    SELECT
        ? AS ServiceLineId,
        ? AS AccountNumber,
        ? AS ServiceLineNumber,
        ? AS BillingCycleStart,
        ? AS BillingCycleEnd,
        ? AS ContractedGB,
        ? AS ContractedCost,
        ? AS PriorityConsumedGB,
        ? AS StandardConsumedGB,
        ? AS OptInPriorityConsumedGB,
        ? AS NonBillableConsumedGB,
        ? AS TotalConsumedGB,
        ? AS ContractUsagePercent,
        ? AS ConsumptionVarianceGB,
        ? AS HasTopUps,
        ? AS TopUpCount,
        ? AS TopUpCapacityGB,
        ? AS TopUpUsedGB,
        ? AS TopUpRemainingGB,
        ? AS TopUpCost,
        ? AS OriginalBudget,
        ? AS AdditionalSpend,
        ? AS TotalCycleSpend,
        ? AS BudgetVariance,
        ? AS Currency,
        ? AS SourceLastUpdatedAt,
        SYSUTCDATETIME() AS CollectedAt
) AS source
ON
(
    target.ServiceLineNumber = source.ServiceLineNumber
    AND target.BillingCycleStart = source.BillingCycleStart
)

WHEN MATCHED THEN
    UPDATE SET
        target.ServiceLineId = source.ServiceLineId,
        target.AccountNumber = source.AccountNumber,
        target.BillingCycleEnd = source.BillingCycleEnd,
        target.ContractedGB = source.ContractedGB,
        target.ContractedCost = source.ContractedCost,
        target.PriorityConsumedGB = source.PriorityConsumedGB,
        target.StandardConsumedGB = source.StandardConsumedGB,
        target.OptInPriorityConsumedGB = source.OptInPriorityConsumedGB,
        target.NonBillableConsumedGB = source.NonBillableConsumedGB,
        target.TotalConsumedGB = source.TotalConsumedGB,
        target.ContractUsagePercent = source.ContractUsagePercent,
        target.ConsumptionVarianceGB = source.ConsumptionVarianceGB,
        target.HasTopUps = source.HasTopUps,
        target.TopUpCount = source.TopUpCount,
        target.TopUpCapacityGB = source.TopUpCapacityGB,
        target.TopUpUsedGB = source.TopUpUsedGB,
        target.TopUpRemainingGB = source.TopUpRemainingGB,
        target.TopUpCost = source.TopUpCost,
        target.OriginalBudget = source.OriginalBudget,
        target.AdditionalSpend = source.AdditionalSpend,
        target.TotalCycleSpend = source.TotalCycleSpend,
        target.BudgetVariance = source.BudgetVariance,
        target.Currency = source.Currency,
        target.SourceLastUpdatedAt = source.SourceLastUpdatedAt,
        target.CollectedAt = source.CollectedAt,
        target.UpdatedAt = SYSUTCDATETIME()

WHEN NOT MATCHED THEN
    INSERT
    (
        ServiceLineId,
        AccountNumber,
        ServiceLineNumber,
        BillingCycleStart,
        BillingCycleEnd,
        ContractedGB,
        ContractedCost,
        PriorityConsumedGB,
        StandardConsumedGB,
        OptInPriorityConsumedGB,
        NonBillableConsumedGB,
        TotalConsumedGB,
        ContractUsagePercent,
        ConsumptionVarianceGB,
        HasTopUps,
        TopUpCount,
        TopUpCapacityGB,
        TopUpUsedGB,
        TopUpRemainingGB,
        TopUpCost,
        OriginalBudget,
        AdditionalSpend,
        TotalCycleSpend,
        BudgetVariance,
        Currency,
        SourceLastUpdatedAt,
        CollectedAt
    )
    VALUES
    (
        source.ServiceLineId,
        source.AccountNumber,
        source.ServiceLineNumber,
        source.BillingCycleStart,
        source.BillingCycleEnd,
        source.ContractedGB,
        source.ContractedCost,
        source.PriorityConsumedGB,
        source.StandardConsumedGB,
        source.OptInPriorityConsumedGB,
        source.NonBillableConsumedGB,
        source.TotalConsumedGB,
        source.ContractUsagePercent,
        source.ConsumptionVarianceGB,
        source.HasTopUps,
        source.TopUpCount,
        source.TopUpCapacityGB,
        source.TopUpUsedGB,
        source.TopUpRemainingGB,
        source.TopUpCost,
        source.OriginalBudget,
        source.AdditionalSpend,
        source.TotalCycleSpend,
        source.BudgetVariance,
        source.Currency,
        source.SourceLastUpdatedAt,
        source.CollectedAt
    );