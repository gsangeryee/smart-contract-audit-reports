# 2023-05-liquid_collective
---
- Category: #staking_pool #liquid_staking #services #yield_aggregator #cross-chain 
- Note Create 2024-12-25
- Platform: Spearbit
- Report Url: [LiquidCollective3-Spearbit-Security-Review](https://github.com/spearbit/portfolio/blob/master/pdfs/LiquidCollective3-Spearbit-Security-Review.pdf)
---
# High Risk Findings (xx)

---
## [H-01]  `_pickNextValidatorsToExitFromActiveOperators` uses the wrong index to query stopped validator
----
- **Tags**:  #business_logic #array_index
- Number of finders: 5
- Difficulty: Degree of Difficulty in Discovering Problems (Hard: 1, Medium: 2~3, Easy: > 6 )
---
### Description
In `_pickNextValidatorsToExitFromActiveOperators`, `OperatorsV2.CachedOperator[] memory operators` does not necessarily have the same order as the actual `OperatorsV2'`s operators, since the ones that don't have `_hasExitableKeys` will be skipped (the operator might not be active or all of its funded keys might have been requested to exit). And so when querying the stopped validator counts

```solidity
for (uint256 idx = 0; idx < exitableOperatorCount;) { 
	uint32 currentRequestedExits = operators[idx].requestedExits; 
	uint32 currentStoppedCount = _getStoppedValidatorsCountFromRawArray(stoppedValidators, idx);
```

one should not use the `idx` in the cached operator's array, but the cached `index` of this array element, as the indexes of `stoppedValidators` correspond to the actual stored operator's array in storage. 

Note that when emitting the `UpdatedRequestedValidatorExitsUponStopped` event, the correct index has been used. 
### Recommendation: 

The calculation for `currentStoppedCount` needs to be corrected to use `operators[idx].index`

```solidity
uint32 currentStoppedCount = _getStoppedValidatorsCountFromRawArray(stoppedValidators, ,operators[idx].index)
```

Also, since this was not caught by test cases, it would be best to add some passing and failing test cases for `_pickNextValidatorsToExitFromActiveOperators`.
### Discussion

### Notes

#### Notes 

- Array Index

```solidity
Original operators array:    [A, B, C, D, E]  (indexes 0,1,2,3,4)
Cached operators array:      [A, C, E]        (indexes 0,1,2)
```
#### Impressions

*I reckon that during an audit, it is essential to repeatedly verify the business logic behind each line of code.*
### Tools
### Refine

- [[1-Business_Logic]]

---

---

# Medium Risk Findings (xx)

---
## [H-XX] High Risk Finding Title
----
- **Tags**:  [[report_tags]]
- Number of finders: nnn
- Difficulty: Degree of Difficulty in Discovering Problems (Hard: 1, Medium: 2~3, Easy: > 6 )
---
### Detail

{{Copy from solodit}}
### Impact

{{Copy from solodit}}
### Proof of Concept

{{Copy from solodit}}
### Recommended Mitigation

{{Copy from solodit}}

### Discussion


### Notes

#### Notes 
{{Some key points that need to be noted. }}
#### Impressions
{{Your feelings about uncovering this finding.}}

### Tools
### Refine

{{ Refine to typical issues}}

---

---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}