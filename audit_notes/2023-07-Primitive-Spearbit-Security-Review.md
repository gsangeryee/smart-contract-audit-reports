# 2023-07-Primitive-Spearbit-Security-Review
---
- Category: chose from [[protocol_categories]]
- Note Create 2024-12-14
- Platform: Spearbit
- Report Url: [2023-07-Primitive-Spearbit-Security-Review](https://github.com/spearbit/portfolio/blob/master/pdfs/Primitive-Spearbit-Security-Review-July.pdf)
---
# High Risk Findings (xx)

---

{{Copy from High Risk Finding Template.md}}

---

# Medium Risk Findings (xx)

---
## [M-01] `getSpotPrice, approximateReservesGivenPrice, getStartegyData` ignore time to maturity

----
- **Tags**: #business_logic #Time-based-logic 
- Number of finders: 2
- Difficulty: Medium
---
### Description

When calling `getSpotPrice`, `getStrategyData` or `approximateReservesGivenPrice`, the pool config is transformed into a `NormalCurve` struct. This transformation always sets the time to maturity field to the entire duration.

```solidity
	function transform(PortfolioConfig memory config) 
		pure 
		returns (NormalCurve memory) 
	{ 
		return NormalCurve({ 
			reserveXPerWad: 0, 
			reserveYPerWad: 0, 
			strikePriceWad: config.strikePriceWad, 
			standardDeviationWad: config.volatilityBasisPoints.bpsToPercentWad(), 
			timeRemainingSeconds: config.durationSeconds, 
			invariant: 0 
		}); 
	}
```

Neither is the `curve.timeRemainingSeconds` value overridden with the correct value for the mentioned functions. The reported spot price will be wrong after the pool has been initialized and integrators cannot rely on this value. 

### Recommendation: 

Initialize the `timeRemainingSeconds` value in `transform` to the current time remaining value or set it to the correct value afterwards for functions where it is needed. It should use a value similar to what `computeTau(..., block.timestamp)` returns. Consider adding additional tests for the affected functions for pools that have been active for a while.
### Notes & Impressions

**Notes**

`timeReaminingSeconds` is the entire duration of the pool (`config.durationSeconds`). This means that regardless of when the pool is actually created or how much time has passed, the time to maturity remains constant.

**Impressions**
It is the business logic and time-base-logic issue.

### Refine

- [[logical_issues#[04] Time-based Logic & Business Flow]]
- [[1-Business_Logic]]

---

---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}