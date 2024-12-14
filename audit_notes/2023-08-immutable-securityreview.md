
# 2023-08-immutable-securityreview
---
- Category: chose from #Bridge
- Note Create 2024-12-13
- Platform: Trail of Bits
- Report Url: [2023-08-immutable-securityreview](https://github.com/trailofbits/publications/blob/master/reviews/2023-08-immutable-securityreview.pdf)
---
# High Risk Findings (xx)

---

{{Copy from High Risk Finding Template.md}}

---

# Medium Risk Findings (xx)

---
## [M-05] Withdrawal queue can be forcibly activated to hinder bridge operation

----
- **Tags**:  #business_logic #1/64_Rule #Denial_of_Service #withdraw_queue
- Number of finders: nnn
- Difficulty: Low
---
### Description

The withdrawal queue can be forcibly activated to impede the proper operation of the bridge. 

The `RootERC20PredicateFlowRate` contract implements a withdrawal queue to more easily detect and stop large withdrawals from passing through the bridge (e.g., bridging illegitimate funds from an exploit). A transaction can enter the withdrawal queue in four ways: 
1. If a token’s flow rate has not been configured by the rate control admin 
2. If the withdrawal amount is larger than or equal to the large transfer threshold for that token 
3. If, during a predefined period, the total withdrawals of that token are larger than the defined token capacity 
4. If the rate controller manually activates the withdrawal queue by using the `activateWithdrawalQueue` function 

In cases 3 and 4 above, the withdrawal queue becomes active for all tokens, not just the individual transfers. Once the withdrawal queue is active, all withdrawals from the bridge must wait a specified time before the withdrawal can be finalized. As a result, a malicious actor could withdraw a large amount of tokens to forcibly activate the withdrawal queue and hinder the expected operation of the bridge.

### Exploit Scenario 1 
Eve observes Alice initiating a transfer to bridge her tokens back to the mainnet. Eve also initiates a transfer, or a series of transfers to avoid exceeding the per-transaction limit, of sufficient tokens to exceed the expected flow rate. With Alice unaware she is being targeted for griefing, Eve can execute her withdrawal on the root chain first, cause Alice’s withdrawal to be pushed into the withdrawal queue, and activate the queue for every other bridge user.
### Exploit Scenario 2 
Mallory has identified an exploit on the child chain or in the bridge itself, but because of the withdrawal queue, it is not feasible to exfiltrate the funds quickly enough without risking getting caught. Mallory identifies tokens with small flow rate limits relative to their price and repeatedly triggers the withdrawal queue for the bridge, degrading the user experience until Immutable disables the withdrawal queue. Mallory takes advantage of this window of time to carry out her exploit, bridge the funds, and move them into a mixer. 
### Recommendations 
Short term, explore the feasibility of withdrawal queues on a per-token basis instead of having only a global queue. Be aware that if the flow rates are set low enough, an attacker could feasibly use them to grief all bridge users.

Long term, develop processes for regularly reviewing the configuration of the various token buckets. Fluctuating token values may unexpectedly make this type of griefing more feasible.
### Notes & Impressions

**Notes**
- Withdraw queue mechanism -> Denial-of-Service

**Impressions**
This is a *Business Logic* issue. Actually, you can spot these problems without checking the code but simply by reading the system documents.

### Refine

[[1-Business_Logic]]

---

---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}