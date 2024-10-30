
# 2024-08-wildact
---
- Category: Lending, Hooks
- Note Create 2024-10-28
- Platform: code4rena
- Report Url
---
## Findings Summary

### High Severity Findings
1. [[2024-08-wildact#H-01] User could withdraw more than supposed to, forcing last user withdraw to fail](https //github.com/code-423n4/2024-08-wildcat-findings/issues/64)|[H-01]User could withdraw more than supposed to, forcing last user withdraw to fail]]
### Medium Severity Findings
1. [[Medium Findings]](link to details)
2. [[Medium Findings]](link to details)

---
# High Risk Findings (1)

---
## [[H-01] User could withdraw more than supposed to, forcing last user withdraw to fail](https://github.com/code-423n4/2024-08-wildcat-findings/issues/64)
----
- **Tags**:  #state-transition #atithmetic #funds-locked #withdraw #loss_of_precision #withdraw_batch 
- Number of finders: 1
---
### Detail

Within Wildcat, withdraw requests are put into batches. Users first queue their withdraws and whenever there's sufficient liquidity, they're filled at the current rate. Usually, withdraw requests are only executable after the expiry passes and then all users within the batch get a cut from the `batch.normalizedAmountPaid` proportional to the scaled amount they've requested a withdraw for.
```solidity
    uint128 newTotalWithdrawn = uint128(
      MathUtils.mulDiv(batch.normalizedAmountPaid, status.scaledAmount, batch.scaledTotalAmount)
    );
```
This makes sure that the sum of all withdraws doesn't exceed the total `batch.normalizedAmountPaid`.

However, this invariant could be broken, if the market is closed as it allows for a batch's withdraws to be executed, before all requests are added.

Consider the market is made of 3 lenders - Alice, Bob and Laurence.

1. Alice queues a larger withdraw with an expiry time 1 year in the future.
2. Market gets closed.
3. Alice executes her withdraw request at the current rate.
4. Bob makes queues multiple smaller requests. As they're smaller, the normalized amount they represent suffers higher precision loss. Because they're part of the whole batch, they also slightly lower the batch's overall rate.
5. Bob executes his requests.
6. Laurence queues a withdraw for his entire amount. When he attempts to execute it, it will fail. This is because Alice has executed her withdraw at a higher rate than the current one and there's now insufficient `state.normalizedUnclaimedWithdrawals`

Note: marking this as High severity as it both could happen intentionally (attacker purposefully queuing numerous low-value withdraws to cause rounding down) and also with normal behaviour in high-value closed access markets where a user's withdraw could easily be in the hundreds of thousands.

Also breaks core invariant:

> The sum of all transfer amounts for withdrawal executions in a batch must be less than or equal to batch.normalizedAmountPaid
### Proof of Concept

Adding a PoC to showcase the issue:
```
forge test --match-test "test_deadrosesxyzissue" --match-path "test/market/WildcatMarket.t.sol"
```

```solidity
  // Test file: /Users/saneryee/3.3_AuditReportsPoC/2024-08-wildcat/test/market/WildcatMarket.t.sol
  function test_deadrosesxyzissue() external {
    parameters.annualInterestBips = 3650;
    _deposit(alice, 1e18);
    _deposit(bob, 0.5e18);
    address laurence = address(1337);
    _deposit(laurence, 0.5e18);
    fastForward(200 weeks);

    vm.startPrank(borrower);
    asset.approve(address(market), 10e18);
    asset.mint(borrower, 10e18);

    vm.stopPrank();
    vm.prank(alice);
    uint32 expiry = market.queueFullWithdrawal();       // alice queues large withdraw

    vm.prank(borrower);
    market.closeMarket();                               // market is closed

    market.executeWithdrawal(alice, expiry);     // alice withdraws at the current rate

    vm.startPrank(bob);
    for (uint i; i < 10; i++) {
      market.queueWithdrawal(1);        // bob does multiple small withdraw requests just so they round down the batch's overall rate
    }
    market.queueFullWithdrawal();
    vm.stopPrank();
    vm.prank(laurence);
    market.queueFullWithdrawal();

    market.executeWithdrawal(bob, expiry);     // bob can successfully withdraw all of his funds

    vm.expectRevert();
    market.executeWithdrawal(laurence, expiry);    // laurence cannot withdraw his funds. Scammer get scammed.

  }
```
### Recommended Mitigation

Although it's not a clean fix, consider adding a `addNormalizedUnclaimedRewards` function which can only be called after a market is closed. It takes token from the user and increases the global variable `state.normalizedUnclaimedRewards`. The invariant would remain broken, but it will make sure no funds are permanently stuck.

**[laurenceday (Wildcat) confirmed and commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/64#issuecomment-2388311632):**

> We're going to have to dig into this, but we're confirming. Thank you!

**[3docSec (judge) commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/64#issuecomment-2391436961):**

> I am confirming as High, under the assumption that funds can't be recovered (didn't see a `cancelWithdrawal` or similar option).

**[laurenceday (Wildcat) commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/64#issuecomment-2406135269):**

> Fixed by the mitigation for [M-01](https://github.com/code-423n4/2024-08-wildcat-findings/issues/121#issuecomment-2406134173):  
> [wildcat-finance/v2-protocol@b25e528](https://github.com/wildcat-finance/v2-protocol/commit/b25e528420617504f1ae6393b4be281a967c3e41).
### Notes

**Checkpoints**
1. State switching function
	```solidity
	// Look for state switching functions like this 
	function closeMarket() 
	function pause() 
	function freeze()
	```
	- Key checks: Behavioral differences before and after state switching.
	- Whether it affects existing mechanisms (such as withdrawals, pricing, etc.) after state switching.
	- Carefully sort out possible operation sequences.
2. Batch / Exchange rate calculation
	```solidity
	// Code related to batch processing 
	function executeWithdrawal() 
	function processUserWithdrawal() 
	
	// Exchange rate update related 
	unction updateRate() 
	function calculateCurrentRate()
	```
	- Check the fairness of batch processing.
	- Pay attention to exchange rate calculation and update logic.
	- Verify whether users can profit through specific operation sequences.
	
#### Impressions
- *Check all code related to funds*

---

---

# Medium Risk Findings (8)

---

##  [[M-01] Users are incentivized to not withdraw immediately after the market is closed](https://github.com/code-423n4/2024-08-wildcat-findings/issues/121)

----
- **Tags**:  #business_logic_design #withdraw_batch
- Number of finders: 1
---
### Detail

Within a withdraw batch, all users within said batch are paid equally - at the same rate, despite what exactly was the rate when each individual one created their withdraw.

While this usually is not a problem as it is a way to reward users who queue the withdrawal and start the expiry cooldown, it creates a problematic situation when the market is closed with an outstanding expiry batch.

The problem is that up until the expiry timestamp comes, all new withdraw requests are added to this old batch where the rate of the previous requests drags the overall withdraw rate down.

Consider the following scenario:

1. A withdraw batch is created and its expiry time is 1 year.
2. 6 months in, the withdraw batch has half of the markets value in it and the market is closed. The current rate is `1.12` and the batch is currently filled at `1.06`
3. Now users have two choices - to either withdraw their funds now at `~1.06` rate or wait 6 months to be able to withdraw their funds at `1.12` rate.

This creates a very unpleasant situation as the users have an incentive to hold their funds within the contract, despite not providing any value.

Looked from slightly different POV, these early withdraw requesters force everyone else to lock their funds for additional 6 months, for the APY they should've usually received for just holding up until now.
### Recommended Mitigation

After closing a market and filling the current expiry, delete it from `pendingWithdrawalExpiry`. Introduce a `closedExpiry` variable so you later make sure a future expiry is not made at that same timestamp to avoid collision.

**[d1ll0n (Wildcat) confirmed and commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/121#issuecomment-2403567138):**

> Thanks for this, good find! Will adopt the proposed solution and see if it fixes [H-01](https://github.com/code-423n4/2024-08-wildcat-findings/issues/64).

**[laurenceday (Wildcat) commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/121#issuecomment-2406134173):**

> Fixed with [wildcat-finance/v2-protocol@b25e528](https://github.com/wildcat-finance/v2-protocol/commit/b25e528420617504f1ae6393b4be281a967c3e41).
### Notes
The key:
- When the market is closed, new users are forced to join existing batches.
- The low exchange rate of early users pulls down the average withdrawal exchange rate of the entire batch
- This creates an unreasonable incentive: users tend to wait for six months to obtain a higher exchange rate even though they do not provided any value during this period.
#### Impressions
*This problem is an issue in business logic design. Any code implementing this logic will have problems*

### Refine
- [[common_issues#Batch Average Pricing Conflicts with Market Status (One-size-fits-all(一刀切))|Batch Average Pricing Conflicts with Market Status (One-size-fits-all(一刀切))]]

---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}