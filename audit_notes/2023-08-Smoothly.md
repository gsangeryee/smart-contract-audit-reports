
# 2023-08-Smoothly
---
- Category: #staking_pool
- Note Create 2024-12-17
- Platform: Pashov Audit Group
- Report Url: [2023-08-01-Smoothly](https://github.com/solodit/solodit_content/blob/main/reports/Pashov%20Audit%20Group/2023-08-01-Smoothly.md)
---
# High Risk Findings (xx)

---
## [H-02] Operator can still claim rewards after being removed from governance

----
- **Tags**:  #business_logic 
- Number of finders: nnn
- Difficulty: Medium
---
### Impact: 

High, as rewards shouldn't be claimable for operators that were removed from governance

### Likelihood:  

High, as this will happen every time this functionality is used and an operator has unclaimed rewards

### Description

The `deleteOperators` method removes an operator account from the `PoolGovernance` but it still leaves the `operatorRewards` mapping untouched, meaning even if an operator is acting maliciously and is removed he can still claim his accrued rewards. This shouldn't be the case, as this functionality is used when operators must be slashed. Also if an operator becomes inactive, even if he is removed, his unclaimed rewards will be stuck in the contract with the current implementation.

### Recommendations

On operator removal transfer the operator rewards to a chosen account, for example the `SmoothlyPool`.
### Notes

#### Notes 
1. **Reward Accessibility After Removal** When an operator is removed from governance - potentially due to malicious behavior or inactivity - they can still claim their previously accrued rewards. This directly contradicts the intent of removing an operator, which typically suggests they should forfeit future benefits.
2. **Stuck Rewards for Inactive Operators** If an operator becomes inactive and is subsequently removed, their unclaimed rewards remain "locked" in the contract. This creates an inefficient state where funds are essentially frozen and not productively utilized.
#### Impressions
*So, I reckon that when coming across operations like "delete" or "close" on a certain object while auditing, you must check the changes in its related status and assets.*

### Refine
- [[1-Business_Logic]]

---

---

# Medium Risk Findings (xx)

---

{{Copy from Medium Risk Finding Template.md}}

---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}