# 2023-07-Baton_Launchpad
---
- Category: #Launchpad
- Note Create 2024-12-19
- Platform: Pashov
- Report Url: [2023-07-01-Baton_Launchpad](https://github.com/solodit/solodit_content/blob/main/reports/Pashov%20Audit%20Group/2023-07-01-Baton%20Launchpad.md)
---
# High Risk Findings (xx)

---
## [H-01] Protocol fees from NFT mints can't be claimed in `BatonLaunchpad`

----
- **Tags**:  #business_logic 
- Number of finders: 1
- Difficulty: Easy
---
### Impact:  
High, as it results in a loss of value for the protocol

### Likelihood:  
High, as it certain to happen

### Description
In `Nft::mint` the `msg.value` expected is the price of an NFT multiplied by the amount of NFTs to mint plus a protocol fee. This protocol fee is sent to the `BatonLaunchpad` contract in the end of the `mint` method like this:

```solidity
	if (protocolFee != 0) {
	    address(batonLaunchpad).safeTransferETH(protocolFee);
	}
```

`BatonLaunchpad` defines a `receive` method that is marked as `payable`, which is correct. The problem is that in `BatonLaunchpad` there is no way to get the ETH balance out of it - it can't be spent in any way possible, leaving it stuck in the contract forever.
### Recommended Mitigation
In `BatonLaunchpad` add a method by which the `owner` of the contract can withdraw its ETH balance.
### Discussion

### Notes

#### Notes 
- can `receive` fee, can not `withdraw` fee
- similar a piggy bank
- simply and serious problem
#### Impressions
- In conclusion, future audits should prioritize the verification of fundamental contract functions, such as the ability to receive funds and the presence of a withdrawal function.
### Tools
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