# 2023-01-liquid-collective
---
- Category: #staking_pool #liquid_staking #services #yield_aggregator #cross-chain 
- Note Create 2025-01-23
- Platform: Spearbit
- Report Url: [LiquidCollective2-Spearbit-Security-Review](https://github.com/spearbit/portfolio/blob/master/pdfs/LiquidCollective2-Spearbit-Security-Review.pdf)
---
# High Risk Findings (xx)

---

{{Copy from High Risk Finding Template.md}}

---

# Medium Risk Findings (xx)

---
## [M-01] Coverage funds might be pulled not only for the purpose of covering slashing losses
----
- **Tags**: #business_logic #PCPvsSCP 
- Number of finders: 4
- Difficulty: Medium
---
### Description: 

The newly introduced coverage fund is a smart contract that holds ETH to cover a potential `lsETH` price decrease due to unexpected slashing events. Funds might be pulled from `CoverageFundV1` to the River contract through `setConsensusLayerData` to cover the losses and keep the share price stable In practice, however, it is possible that these funds will be pulled not only in emergency events. 

`_maxIncrease` is used as a measure to enforce the maximum difference between `prevTotalEth` and `postTotalEth`, but in practice, it is being used as a mandatory growth factor in the context of coverage funds, which might cause the pulling of funds from the coverage fund to ensure `_maxIncrease` of revenue in case fees are not high enough
### Recommended Mitigation
Consider replacing
```solidity
if (((_maxIncrease + previousValidatorTotalBalance) - executionLayerFees) > _validatorTotalBalance) { 
	coverageFunds = _pullCoverageFunds( 
		((_maxIncrease + previousValidatorTotalBalance) - executionLayerFees) - _validatorTotalBalance ); 
}
```

with
```solidity
if (previousValidatorTotalBalance > _validatorTotalBalance + executionLayerFees)) {
	coverageFunds = _pullCoverageFunds( 
		((_maxIncrease + previousValidatorTotalBalance) - executionLayerFees) - _validatorTotalBalance ); 
}
```
### Discussion

**Alluvial Team**: Trying to clarify the use-case and the sequence of operations here: 
- Use case: Liquid Collective partners with Nexus Mutual (NXM) and possibly other actors to cover for slashing losses. Each time Liquid Collective adds a validator key to the system, we will submit the key to NXM so they can monitor it and cover it in case of slashing. In case one of the validator's keys gets slashed (slashing being defined according to NXM policy), NXM will reimburse part or all of the lost ETH. The period between the slashing event occurs and the reimbursement that happens can go from 30 days up to 365 days. The reimbursement will go to the CoverageFund contract and subsequently be pulled into the core system respecting maximum bounds. 
- Sequence of Operations: 
1. Liquid Collective submits a validator key to NXM to be covered. 
2. A slashing event occurs (e.g a validator key gets slashed 1 ETH). 
3. NXM monitoring catches the slashing event. 4. 30 days to 365 days later NXM reimburses 1 ETH to the CoverageFund.
4. 1 ETH gets progressively pulled from the CoverageFund into River respecting the bounds. 

**Spearbit**: Acknowledged as discussed with the Alluvial team, the impact of this issue is limited since the coverage fund should hold ETH only in case of a slashing event.
### Notes & Impressions

#### **Issue Overview**

- **Problem**: The Coverage Fund's ETH could be withdrawn not just to compensate for slashing losses but also to artificially meet revenue growth targets, even when fees are insufficient.
    
- **Root Cause**: The condition triggering fund withdrawals uses `_maxIncrease` (a parameter capping allowable balance growth) in a way that mandates growth, forcing Coverage Fund usage if fees fall short of this target—regardless of actual slashing events.

#### **Business Logic Implications**

- **Intended Use**: Coverage Funds should solely reimburse slashing losses (e.g., after Nexus Mutual validates a slashing event).
    
- **Risk**: Without the fix, partners providing coverage (like Nexus Mutual) might see funds used for unintended purposes, undermining trust and the system's ability to handle real slashing events.
#### Impressions

*A critical misalignment between the code's logic and the Coverage Fund's intended purpose.*
### Tools
### Refine

- [[1-Business_Logic]]
- #PCPvsSCP 

---
---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}