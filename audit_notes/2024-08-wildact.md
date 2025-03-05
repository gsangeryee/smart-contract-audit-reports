# 2024-08-wildact
---
- Category: #Lending, #Hooks
- Note Create 2024-10-28
- Platform: code4rena
- [Report Url](https://github.com/code-423n4/2024-08-wildcat-findings/blob/main/report.md)
---
## Findings Summary

### High Severity Findings
1. [[2024-08-wildact#H-01] User could withdraw more than supposed to, forcing last user withdraw to fail](https //github.com/code-423n4/2024-08-wildcat-findings/issues/64)|[H-01]User could withdraw more than supposed to, forcing last user withdraw to fail]]
### Medium Severity Findings
1. [[2024-08-wildact#[M-01] Users are incentivized to not withdraw immediately after the market is closed|[M-01] Users are incentivized to not withdraw immediately after the market is closed]]
2. [[2024-08-wildact#[M-02] `FixedTermLoanHooks` allow Borrower to update Annual Interest before end of the "Fixed Term Period"|[M-02] `FixedTermLoanHooks` allow Borrower to update Annual Interest before end of the "Fixed Term Period"]]
3. [[2024-08-wildact#[M-03] Inconsistency across multiple repaying functions causing lender to pay extra fees|[M-03] Inconsistency across multiple repaying functions causing lender to pay extra fees]]
4. [[2024-08-wildact#[M-04] `FixedTermLoanHook` looks at `block.timestamp` instead of `expiry`|[M-04] `FixedTermLoanHook` looks at `block.timestamp` instead of `expiry`]]
5. [[2024-08-wildact#[M-05] Role provide can bypass intended restrictions and lower expiry set by other providers|[M-05] Role provide can bypass intended restrictions and lower expiry set by other providers]]
6. [[2024-08-wildact#[M-06] No lender is able to exit even after the market is closed|[M-06] No lender is able to exit even after the market is closed]]
7. [[2024-08-wildact#[M-07] Role providers cannot be EOAs as stated in the documentation|[M-07] Role providers cannot be EOAs as stated in the documentation]]
8. [[2024-08-wildact#[M-08] `AccessControlHooks` `onQueueWithdrawal()` does not check if market is hooked which could lead to unexpected errors such as temporary DoS|[M-08] `AccessControlHooks` `onQueueWithdrawal()` does not check if market is hooked which could lead to unexpected errors such as temporary DoS]]

---
# High Risk Findings (1)

---
## [H-01] User could withdraw more than supposed to, forcing last user withdraw to fail
----
- **Tags**:  #state-transition #atithmetic #funds-locked #withdraw #loss_of_precision #withdraw_batch 
- Number of finders: 1
- Difficulty: Hard
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

##  [M-01] Users are incentivized to not withdraw immediately after the market is closed

----
- **Tags**:  #withdraw_batch #business_logic 
- Number of finders: 1
- Difficulty: Hard
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

## [M-02] `FixedTermLoanHooks` allow Borrower to update Annual Interest before end of the "Fixed Term Period"

----
- **Tags**: refer from #PCPvsSCP 
- Number of finders: 3
- Difficulty: Medium
---
### Summary

While the documentation states that in case of 'fixed term' market the APR cannot be changed until the term ends, nothing prevents this in `FixedTermLoanHooks`.

### Vulnerability details

In Wildcat markets, lenders know in advance how much `APR` the borrower will pay them. In order to allow lenders to exit the market swiftly, the market must always have at least a `reserve ratio` of the lender funds ready to be withdrawn.

If the borrower decides to [reduce the `APR`](https://docs.wildcat.finance/using-wildcat/day-to-day-usage/borrowers#reducing-apr), in order to allow lenders to 'ragequit', a new `reserve ratio` is calculated based on the variation of the APR as described in the link above.

Finally, is a market implement a fixed term (date until when withdrawals are not possible), it shouldn't be able to reduce the APR, as this would allow the borrower to 'rug' the lenders by reducing the APR to 0% while they couldn't do anything against that.

The issue here is that while lenders are (as expected) prevented to withdraw before end of term:<br>
<https://github.com/code-423n4/2024-08-wildcat/blob/main/src/access/FixedTermLoanHooks.sol#L857-L859>

```solidity
File: src/access/FixedTermLoanHooks.sol
848:   function onQueueWithdrawal(
849:     address lender,
850:     uint32 /* expiry */,
851:     uint /* scaledAmount */,
852:     MarketState calldata /* state */,
853:     bytes calldata hooksData
854:   ) external override {
855:     HookedMarket memory market = _hookedMarkets[msg.sender];
856:     if (!market.isHooked) revert NotHookedMarket();
857:     if (market.fixedTermEndTime > block.timestamp) {
858:       revert WithdrawBeforeTermEnd();
859:     }
```

this is not the case for the borrower setting the annual interest:<br>
<https://github.com/code-423n4/2024-08-wildcat/blob/main/src/access/FixedTermLoanHooks.sol#L960-L978>

```solidity
File: src/access/FixedTermLoanHooks.sol
960:   function onSetAnnualInterestAndReserveRatioBips(
961:     uint16 annualInterestBips,
962:     uint16 reserveRatioBips,
963:     MarketState calldata intermediateState,
964:     bytes calldata hooksData
965:   )
966:     public
967:     virtual
968:     override
969:     returns (uint16 updatedAnnualInterestBips, uint16 updatedReserveRatioBips)
970:   {
971:     return
972:       super.onSetAnnualInterestAndReserveRatioBips(
973:         annualInterestBips,
974:         reserveRatioBips,
975:         intermediateState,
976:         hooksData
977:       );
978:   }
979: 
```

### Impact

Borrower can rug the lenders by reducing the APR while they cannot quit the market.

### Proof of Concept

Add this test to `test/access/FixedTermLoanHooks.t.sol`

```solidity
  function testAudit_SetAnnualInterestBeforeTermEnd() external {
    DeployMarketInputs memory inputs;

	// "deploying" a market with MockFixedTermLoanHooks
	inputs.hooks = EmptyHooksConfig.setHooksAddress(address(hooks));
	hooks.onCreateMarket(
		address(this),				// deployer
		address(1),				// dummy market address
		inputs,					// ...
		abi.encode(block.timestamp + 365 days, 0) // fixedTermEndTime: 1 year, minimumDeposit: 0
	);

	vm.prank(address(1));
	MarketState memory state;
	// as the fixedTermEndTime isn't past yet, it's not possible to withdraw
	vm.expectRevert(FixedTermLoanHooks.WithdrawBeforeTermEnd.selector);
	hooks.onQueueWithdrawal(address(1), 0, 1, state, '');

	// but it is still possible to reduce the APR to zero
	hooks.onSetAnnualInterestAndReserveRatioBips(0, 0, state, "");
  }
```

### Recommended Mitigation Steps

When `FixedTermLoanHooks::onSetAnnualInterestAndReserveRatioBips` is called, revert if `market.fixedTermEndTime > block.timestamp`.

**[laurenceday (Wildcat) disputed and commented via duplicate issue \#23](https://github.com/code-423n4/2024-08-wildcat-findings/issues/23#issuecomment-2368151696):**
 > This is a valid finding, thank you - an embarrassing one for us at that, we clearly just missed this when writing the hook templates!
> 
> However, we're a bit torn internally on whether this truly classifies as a High. We've definitely specified in documentation that this is a rug pull mechanic, but there are no funds directly or indirectly at risk here, unless you classify the potential of _earning_ less than expected when you initially deposited as falling in that bucket.
> 
> So, we're going to kick this one to the judge: does earning 10,000 on a 100,000 deposit rather than 15,000 count as funds at risk if there's no way to ragequit for the period of time where that interest should accrue? Or is this more of a medium wherein protocol functionality is impacted?
> 
> It's definitely a goof on our end, and we're appreciative that the warden caught it, so thank you. With that said, we're trying to be fair to you (the warden) while also being fair to everyone else that's found things. This is a _very_ gentle dispute for the judge to handle: sadly the 'disagree with severity' tag isn't available to us anymore!

**[3docSec (judge) decreased severity to Medium and commented via duplicate issue \#23](https://github.com/code-423n4/2024-08-wildcat-findings/issues/23#issuecomment-2393321534):**
 > Hi @laurenceday thanks for adding context.
> 
> > "So, we're going to kick this one to the judge: does earning 10,000 on a 100,000 deposit rather than 15,000 count as funds at risk if there's no way to ragequit for the period of time where that interest should accrue? Or is this more of a medium wherein protocol functionality is impacted?"
> 
> I consider this a Medium issue: because it's only future "interest" gains that are at risk, I see this more like an availability issue where the lender's funds are locked at conditions they didn't necessarily sign up for; the problem is the locking (as you said if there was a ragequit option, it would be a different story).
> 
> I admit this is a subjective framing, but at the same time, it's consistent with how severity is assessed in bug bounty programs, where missing out on future returns generally has lower severity than having present funds at risk.


### Notes

- It belongs to the type of error of PCP vs SCP
- The developers missed the critical control points.
- *It is necessary to read the code in detail and understand it. Meanwhile, a careful inspection should be carried out in accordance with the design and business logic.*
### Refine

 - [[logical_issues#[01] PCP vs SCP]]

---

## [M-03]  Inconsistency across multiple repaying functions causing lender to pay extra fees

----
- **Tags**:  #consistency #business_logic 
- Number of finders: 6
- Difficulty: Easy
---
Within functions such as `repay` and `repayAndProcessUnpaidWithdrawalBatches`, funds are first pulled from the user in order to use them towards the currently expired, but not yet unpaid batch, and then the updated state is fetched.

```solidity
  function repay(uint256 amount) external nonReentrant sphereXGuardExternal {
    if (amount == 0) revert_NullRepayAmount();

    asset.safeTransferFrom(msg.sender, address(this), amount);
    emit_DebtRepaid(msg.sender, amount);

    MarketState memory state = _getUpdatedState();
    if (state.isClosed) revert_RepayToClosedMarket();

    // Execute repay hook if enabled
    hooks.onRepay(amount, state, _runtimeConstant(0x24));

    _writeState(state);
  }
```

However, this is not true for functions such as `closeMarket`, `deposit`, `repayOutstandingDebt` and `repayDelinquentDebt`, where the state is first fetched and only then funds are pulled, forcing borrower into higher fees.

```solidity
  function closeMarket() external onlyBorrower nonReentrant sphereXGuardExternal {
    MarketState memory state = _getUpdatedState();    // fetches updated state

    if (state.isClosed) revert_MarketAlreadyClosed();

    uint256 currentlyHeld = totalAssets();
    uint256 totalDebts = state.totalDebts();
    if (currentlyHeld < totalDebts) {
      // Transfer remaining debts from borrower
      uint256 remainingDebt = totalDebts - currentlyHeld;
      _repay(state, remainingDebt, 0x04);             // pulls user funds
      currentlyHeld += remainingDebt;
```

This inconsistency will cause borrowers to pay extra fees which they otherwise wouldn't.

### PoC:

```solidity
  function test_inconsistencyIssue() external {
      parameters.annualInterestBips = 3650;
      _deposit(alice, 1e18);
      uint256 borrowAmount = market.borrowableAssets();
      vm.prank(borrower);
      market.borrow(borrowAmount);
      vm.prank(alice);
      market.queueFullWithdrawal();
      fastForward(52 weeks);

      asset.mint(borrower, 10e18);
      vm.startPrank(borrower);
      asset.approve(address(market), 10e18);
      uint256 initBalance = asset.balanceOf(borrower); 

      asset.transfer(address(market), 10e18);
      market.closeMarket();
      uint256 finalBalance = asset.balanceOf(borrower);
      uint256 paid = initBalance - finalBalance;
      console.log(paid);

  } 

    function test_inconsistencyIssue2() external {
      parameters.annualInterestBips = 3650;
      _deposit(alice, 1e18);
      uint256 borrowAmount = market.borrowableAssets();
      vm.prank(borrower);
      market.borrow(borrowAmount);
      vm.prank(alice);
      market.queueFullWithdrawal();
      fastForward(52 weeks);

      asset.mint(borrower, 10e18);
      vm.startPrank(borrower);
      asset.approve(address(market), 10e18);
      uint256 initBalance = asset.balanceOf(borrower); 


      market.closeMarket();
      uint256 finalBalance = asset.balanceOf(borrower);
      uint256 paid = initBalance - finalBalance;
      console.log(paid);

  }
```

and the logs:

    Ran 2 tests for test/market/WildcatMarket.t.sol:WildcatMarketTest
    [PASS] test_inconsistencyIssue() (gas: 656338)
    Logs:
      800455200405885337

    [PASS] test_inconsistencyIssue2() (gas: 680537)
    Logs:
      967625143234433533

### Recommended Mitigation Steps

Always pull the funds first and refund later if needed.

**[d1ll0n (Wildcat) acknowledged and commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/62#issuecomment-2388275386):**
 > The listed functions which incur higher fees all require the current state of the market to accurately calculate relevant values to the transfer. Because of that, the transfer can't happen until after the state is updated, and it would be expensive (and too large to fit in the contract size) to redo the withdrawal payments post-transfer.
> 
> For the repay functions this is more of an issue than the others, as that represents the borrower specifically taking action to repay their debts, whereas the other functions are actions by other parties (and thus we aren't very concerned if they fail to cure the borrower's delinquency for them). We may end up just removing these secondary repay functions.

**[laurenceday (Wildcat) commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/62#issuecomment-2403678176):**
 > Resolved by [wildcat-finance/v2-protocol@e7afdc9](https://github.com/wildcat-finance/v2-protocol/commit/e7afdc9312ec672df2a9d03add18727a4c774b88).


***
### Notes & Impressions

**Key Points:**
1. There are multiple functions with repayment capabilities in the contract. 
2. However, the processing order of these functions is inconsistent: some are "change the status first, then transfer funds", while others are "transfer funds first, then change the status". 
3. These inconsistencies ultimately lead to different final amounts for the same repayment. 
4. Why do different processing orders result in inconsistent amounts? Because accumulated interest and fees are calculated when the status is updated. 
5. The original intention of the project team: Different functions are intended for different users. However, no role control has been implemented. 

**Impressions:** 
This is a typical problem regarding Consistency. 
- **Principle of Consistency**: The same business operations should have a unified processing mode. 
- **Principle of Least Surprise**: Users should not get unexpected results due to calling different functions. 
- **Code Reuse**: The common business logic should be abstracted into a unified function for processing. 

Checklist: 
1. Check whether there are multiple functions for the same business (repayment, deposit) in the contract. 
2. If they exist, check whether the business operations of these functions are consistent. 
3. If they are inconsistent, determine whether the consequences of this inconsistency are serious. 
4. If multiple functions for the same business are found, check whether there is a need for role control. 
5. Check whether the documentation of the relevant functions clearly indicates the expected users. 
6. Examine whether the common logic can be processed by a unified internal function.
### Refine
- [[logical_issues#[03] Consistency Issues]]
---
## [M-04] `FixedTermLoanHook` looks at `block.timestamp` instead of `expiry`

----
- **Tags**: refer from #Time-based-logic
- Number of finders: 1
- Difficulty: Hard
---
The idea of `FixedTermLoanHook` is to only allow for withdrawals after a certain term end time. However, the problem is that the current implementation does not look at the expiry, but instead at the `block.timestamp`.

```solidity
  function onQueueWithdrawal(
    address lender,
    uint32 /* expiry */,
    uint /* scaledAmount */,
    MarketState calldata /* state */,
    bytes calldata hooksData
  ) external override {
    HookedMarket memory market = _hookedMarkets[msg.sender];
    if (!market.isHooked) revert NotHookedMarket();
    if (market.fixedTermEndTime > block.timestamp) {
      revert WithdrawBeforeTermEnd();
    }
```

### Recommended Mitigation Steps

Check the `expiry` instead of `block.timestamp`.

**[d1ll0n (Wildcat) confirmed](https://github.com/code-423n4/2024-08-wildcat-findings/issues/60#event-14486191444)**

**[laurenceday (Wildcat) acknowledged and commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/60#issuecomment-2403650325):**
 > We've reflected on this a little bit, and decided that we want to turn this from a confirmed into an acknowledge.
> 
> The reasoning goes as follows:
> 
> Imagine that a fixed market has an expiry of December 30th, but there's a withdrawal cycle of 7 days.
> 
> Presumably the borrower is anticipating [and may have structured things] such that they are expecting to be able to make full use of any credit extended to them until then, and not a day sooner.
> 
> Fixing this in the way suggested would permit people to place withdrawal requests on December 23rd, with the potential to tip a market into delinquent status (depending on grace period configuration) before the fixed duration has actually met.
> 
> Net-net we think it makes more sense to allow the market to revert back to a perpetual after that expiry and allow withdrawal requests to be processed per the conditions. The expectation here would be that the withdrawal cycle would actually be quite short.

**[Infect3d (warden) commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/60#issuecomment-2405458024):**
 > May I comment on this issue: can we really consider this a bug rather than a feature and a design improvement, also considering sponsor comment?<br>
> Expiry mechanism is known by borrower and lender, so if borrower wants lenders to be able to withdraw on time, he can simply configure `fixedTermEndTime = value - withdrawalBatchDuration`.

**[3docSec (judge) commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/60#issuecomment-2411378025):**
 > Hi @Infect3d - I agree we are close to an accepted trade-off territory. Here I lean on the sponsor who very transparently made it clear this trade-off is not something they had deliberately thought of.
> 
> Therefore, because the impact is compatible with Medium severity, "satisfactory Medium" plus "sponsor acknowledged" is a fair way of categorizing this finding.


***
### Notes & Impressions

This type of issue belongs to "Time-based Logic & Business Flow" audit category, involving the following aspects:

1. Audit Strategy:
```solidity
// When seeing code like this
function onQueueWithdrawal(
    address lender,
    uint32 expiry,        // 👈 Note unused parameter
    uint scaledAmount,
    MarketState calldata state,
    bytes calldata hooksData
) {
    // 👇 Note time-related check
    if (market.fixedTermEndTime > block.timestamp) {
        revert WithdrawBeforeTermEnd();
    }
}
```

During audit, focus on:
1. Parameter Usage Analysis
   - Check if all function parameters are properly utilized
   - Pay special attention to unused parameters (like expiry here)
   - Consider: Why is this parameter present but unused? Is important logic missing?

2. Time Logic Analysis
   - Identify all time-related checks (block.timestamp, expiry, etc.)
   - Draw timelines to verify if logic at each time point is reasonable
   - For example:
     ```
     Request Time -> fixedTermEndTime -> expiry -> Actual Withdrawal Time
     ```

3. Business Flow Analysis
   - Understand the complete business flow (from request submission to actual withdrawal)
   - Check if time controls at each step are reasonable
   - Verify if user expectations match actual behavior

4. Configuration Risk Analysis
   - Check configurable parameters (like fixedTermEndTime)
   - Consider potential issues from misconfiguration
   - Evaluate if additional protection mechanisms are needed

5. Documentation Consistency Check
   - Compare code implementation with documentation
   - Check for potentially misleading design or instructions

Steps to identify such issues:

```
1. Establish Checklist:
   □ Identify all time-related parameters
   □ Check unused parameters
   □ Verify time check logic
   □ Analyze configuration parameter impacts
   □ Test edge cases

2. Scenario Testing:
   □ Normal withdrawal scenarios
   □ Early withdrawal attempts
   □ Boundary time point tests
   □ Different configuration combinations

3. Risk Assessment:
   □ User experience impact
   □ Fund security impact
   □ Contract interaction impact
```

Summary:
- This type of issue belongs to "Time-based Logic & Business Flow" audit category
- Requires combination of code review, business understanding, and scenario testing
- Pay special attention to:
  1. Unused parameters (may indicate design issues)
  2. Time control logic (whether it meets business expectations)
  3. Configuration parameter impacts (potential unexpected behaviors)
  4. Documentation and implementation consistency

This explains why it's a valid audit finding even if the code itself isn't buggy, as it involves user experience and potential configuration risks.

### Refine

- [[[logical_issues#[04] Time-based Logic & Business Flow]]
---

## [M-05] Role provide can bypass intended restrictions and lower expiry set by other providers

----
- **Tags**: refer from #access_control #two-step_attack #multi_OR
- Number of finders: 3
- Difficulty: Medium
---
If we look at the code comments, we'll see that role providers can update a user's credential only if at least one of the 3 is true:

- the previous credential's provider is no longer supported, OR
- the caller is the previous role provider, OR
- the new expiry is later than the current expiry

```solidity
  /**
   * @dev Grants a role to an account by updating the account's status.
   *      Can only be called by an approved role provider.
   *
   *      If the account has an existing credential, it can only be updated if:
   *      - the previous credential's provider is no longer supported, OR
   *      - the caller is the previous role provider, OR
   *      - the new expiry is later than the current expiry
   */
  function grantRole(address account, uint32 roleGrantedTimestamp) external {
    RoleProvider callingProvider = _roleProviders[msg.sender];

    if (callingProvider.isNull()) revert ProviderNotFound();

    _grantRole(callingProvider, account, roleGrantedTimestamp);
  }
```

This means that a role provider should not be able to reduce a credential set by another role provider.

However, this could easily be bypassed by simply splitting the call into 2 separate ones:

1. First one to set the expiry slightly later than the currently set one. This would set the role provider to the new one.
2. Second call to reduce the expiry as much as they'd like. Since they're the previous provider they can do that.

### Recommended Mitigation Steps

Fix is non-trivial.

**[d1ll0n (Wildcat) disputed and commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/57#issuecomment-2384066409):**

> This is a useful note to be aware of, but I'd categorize it low/informational as role providers are inherently trusted entities. The likelihood and impact of this kind of attack are pretty minimal.

**[3docSec (judge) commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/57#issuecomment-2393602205):**

> There are a few factors to be considered:
> 
> - it is a valid privilege escalation vector
> - the attacker has to be privileged already
> - the attack can have a direct impact on a lender
> 
> While the first two have me on the fence when choosing between Medium and Low severity, the third point is a tiebreaker towards Medium.
> 
> If we stick to the [C4 severity categorization](https://docs.code4rena.com/awarding/judging-criteria/severity-categorization), I see a good fit with the Medium definition:
> 
> > "the function of the protocol or its availability could be impacted [...] with a hypothetical attack path with stated assumptions"
### Notes & Impressions

Let me break down this smart contract security vulnerability:



The vulnerability relates to role management in a smart contract, specifically around how role providers can modify user credentials. Here's the issue explained:

1. **Intended Behavior**:
The contract aims to prevent role providers from reducing the expiry time of credentials that were set by other providers. According to the comments, a role provider should only be able to update a credential if:
- The previous provider is no longer supported
- They are the same provider who set the previous credential
- They're extending the expiry time (making it later)

2. **The Vulnerability**:
A malicious role provider can bypass these restrictions using a two-step attack:

Step 1: First Call
- Set a new expiry that's slightly later than the current one
- This is allowed because it meets the condition "new expiry is later than the current expiry"
- This call changes the credential's provider to the attacker

Step 2: Second Call
- Now that they're registered as the credential's provider, they can make a second call
- In this call, they can set any expiry they want (even a much earlier one)
- This works because they now meet the condition "caller is the previous role provider"

3. **Impact**:
- This allows any role provider to effectively override and reduce the expiry times set by other providers
- It breaks the intended access control mechanism
- Could lead to premature revocation of user permissions

4. **Root Cause**:
The vulnerability exists because the contract doesn't maintain any history or checks about the original provider once a credential is updated. It only looks at the most recent provider.

To fix this, the contract would need to either:
- Prevent provider changes unless absolutely necessary
- Maintain and check the original provider's settings
- Add additional checks to prevent expiry reduction by different providers
- Implement a timelock or cool-down period between credential updates

*So the key point of this issue is that "the connection of these three conditions is an ‘OR’ rel "*
### Refine

[[logical_issues#Multi-Step Bypass via OR Logic in Access Controls]]

---

## [M-06] No lender is able to exit even after the market is closed

----
- **Tags**: refer from #state-transition 
- Number of finders: 3
- Difficulty: Medium
---
When a borrower creates a market hooked by a [fixed-term hook](https://github.com/code-423n4/2024-08-wildcat/blob/main/src/access/FixedTermLoanHooks.sol), all lenders are prohibited from withdrawing their assets from the market before the fixed-term time has elapsed.

The borrower can close the market at any time. However, `fixedTermEndTime` of the market is not updated, preventing lenders from withdrawing their assets if `fixedTermEndTime` has not yet elapsed.

Copy below codes to [WildcatMarket.t.sol](https://github.com/code-423n4/2024-08-wildcat/blob/main/test/market/WildcatMarket.t.sol) and run forge test --match-test test_closeMarket_BeforeFixedTermExpired:

```solidity
  function test_closeMarket_BeforeFixedTermExpired() external {
    //@audit-info deploy a FixedTermLoanHooks template
    address fixedTermHookTemplate = LibStoredInitCode.deployInitCode(type(FixedTermLoanHooks).creationCode);
    hooksFactory.addHooksTemplate(
      fixedTermHookTemplate,
      'FixedTermLoanHooks',
      address(0),
      address(0),
      0,
      0
    );
    
    vm.startPrank(borrower);
    //@audit-info borrower deploy a FixedTermLoanHooks hookInstance
    address hooksInstance = hooksFactory.deployHooksInstance(fixedTermHookTemplate, '');
    DeployMarketInputs memory parameters = DeployMarketInputs({
      asset: address(asset),
      namePrefix: 'name',
      symbolPrefix: 'symbol',
      maxTotalSupply: type(uint128).max,
      annualInterestBips: 1000,
      delinquencyFeeBips: 1000,
      withdrawalBatchDuration: 10000,
      reserveRatioBips: 10000,
      delinquencyGracePeriod: 10000,
      hooks: EmptyHooksConfig.setHooksAddress(address(hooksInstance))
    });
    //@audit-info borrower deploy a market hooked by a FixedTermLoanHooks hookInstance
    address market = hooksFactory.deployMarket(
      parameters,
      abi.encode(block.timestamp + (365 days)),
      bytes32(uint(1)),
      address(0),
      0
    );
    vm.stopPrank();
    //@audit-info lenders can only withdraw their asset one year later
    assertEq(FixedTermLoanHooks(hooksInstance).getHookedMarket(market).fixedTermEndTime, block.timestamp + (365 days));
    //@audit-info alice deposit 50K asset into market
    vm.startPrank(alice);
    asset.approve(market, type(uint).max);
    WildcatMarket(market).depositUpTo(50_000e18);
    vm.stopPrank();
    //@audit-info borrower close market in advance
    vm.prank(borrower);
    WildcatMarket(market).closeMarket();
    //@audit-info the market is closed
    assertTrue(WildcatMarket(market).isClosed());
    //@audit-info however, alice can not withdraw her asset due to the unexpired fixed term.
    vm.expectRevert(FixedTermLoanHooks.WithdrawBeforeTermEnd.selector);
    vm.prank(alice);
    WildcatMarket(market).queueFullWithdrawal();
  }
```

### Recommended Mitigation

When a market hooked by a fixed-term hook is closed, `fixedTermEndTime` should be set to `block.timestamp` if it has not yet elapsed:

```solidity
  constructor(address _deployer, bytes memory /* args */) IHooks() {
    borrower = _deployer;
    // Allow deployer to grant roles with no expiry
    _roleProviders[_deployer] = encodeRoleProvider(
      type(uint32).max,
      _deployer,
      NotPullProviderIndex
    );
    HooksConfig optionalFlags = encodeHooksConfig({
      hooksAddress: address(0),
      useOnDeposit: true,
      useOnQueueWithdrawal: false,
      useOnExecuteWithdrawal: false,
      useOnTransfer: true,
      useOnBorrow: false,
      useOnRepay: false,
      useOnCloseMarket: false,
      useOnNukeFromOrbit: false,
      useOnSetMaxTotalSupply: false,
      useOnSetAnnualInterestAndReserveRatioBips: false,
      useOnSetProtocolFeeBips: false
    });
    HooksConfig requiredFlags = EmptyHooksConfig
      .setFlag(Bit_Enabled_SetAnnualInterestAndReserveRatioBips)
+     .setFlag(Bit_Enabled_CloseMarket);
      .setFlag(Bit_Enabled_QueueWithdrawal);
    config = encodeHooksDeploymentConfig(optionalFlags, requiredFlags);
  }
```

```solidity
  function onCloseMarket(
    MarketState calldata /* state */,
    bytes calldata /* hooksData */
- ) external override {}
+ ) external override {
+   HookedMarket memory market = _hookedMarkets[msg.sender];
+   if (!market.isHooked) revert NotHookedMarket();
+   if (market.fixedTermEndTime > block.timestamp) {
+     _hookedMarkets[msg.sender].fixedTermEndTime = uint32(block.timestamp);
+   }
+ }
```

**[laurenceday (Wildcat) confirmed and commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/52#issuecomment-2364042816):**

> This is a great catch.

**[laurenceday (Wildcat) commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/52#issuecomment-2403731338):**

> Fixed by [wildcat-finance/v2-protocol@05958e3](https://github.com/wildcat-finance/v2-protocol/commit/05958e35995093bcf6941c82fc14f9b9acc7cea0).
### Notes & Impressions

It is very similar to the following high-risk finding. 
[[2024-08-wildact#[H-01] User could withdraw more than supposed to, forcing last user withdraw to fail|[H-01] User could withdraw more than supposed to, forcing last user withdraw to fail]]

Common Pattern Analysis between the two issues:

1. Core Similarity: Inconsistent State Transitions
```
Fixed-Term Issue:
- Market State: Closed
- Time Lock State: Still active
- Result: Deadlock

Withdrawal Issue:
- Batch State: Partially executed
- Rate State: Changes during execution
- Result: Under-collateralization
```

2. Shared Root Cause: Race Conditions in Market Closure
```solidity
Market Closure Scenarios:

Scenario 1 (Fixed-Term):
- Time Lock: t + 365 days
- Market Closes: t + 30 days
- States become unsynchronized

Scenario 2 (Withdrawals):
- Withdrawal Batch: Expected uniform rate
- Market Closes: Mid-batch execution
- Rates become unsynchronized
```

3. Pattern Recognition Framework:
```
Category: State Synchronization in Market Closure

Key Identifiers:
1. Multiple dependent states
2. Administrative override capability
3. Time-based or sequential operations
4. Batch processing with shared resources

Risk Amplifiers:
- Rate calculations
- Time locks
- Multi-user interactions
- Partial execution paths
```

4. Audit Strategy:
```
Critical Checkpoints:
1. Market Closure Effects
   - What states should be updated?
   - What constraints should be lifted?
   - What rates should be locked?

2. Sequence Dependencies
   - Can operations be split?
   - Are rates consistent?
   - Are locks properly cleared?

3. Resource Distribution
   - Is total withdrawal amount preserved?
   - Are time locks properly handled?
   - Are all users able to exit?
```

5. Combined Defense Pattern:
```solidity
function closeMarket() external {
    // 1. Lock new operations
    marketState = CLOSED;
    
    // 2. Clear all time-based restrictions
    fixedTermEndTime = block.timestamp;
    
    // 3. Freeze rates/calculations
    finalizedRate = getCurrentRate();
    
    // 4. Enable immediate withdrawals
    clearWithdrawalQueue();
    
    // 5. Verify invariants
    require(totalAssets >= totalLiabilities, "Invalid closure state");
}
```

This analysis shows why these issues are related - they both stem from incomplete market closure handling and demonstrate how administrative actions can break protocol invariants if state synchronization isn't properly managed.

For auditors, this suggests:
1. Always trace market closure effects across all state variables
2. Look for time-based or sequential operations that could be disrupted
3. Verify that emergency actions properly handle all constraints
4. Check for rate calculations that could be manipulated during state changes
### Refine

[[common_issues#[04] State Transition Synchronization]]

---

## [M-07] Role providers cannot be EOAs as stated in the documentation

----
- **Tags**: refer from #PCPvsSCP 
- Number of finders: 2
- Difficulty: Degree of Difficulty in Discovering Problems (High: 1, Medium: 2~3, Low: > 6 )
---
```solidity
220:      bool isPullProvider = IRoleProvider(providerAddress).isPullProvider();
```

```solidity
254  function addRoleProvider(address providerAddress, uint32 timeToLive) external onlyBorrower {
```

### Impact

The [Documentation](https://docs.wildcat.finance/technical-overview/security-developer-dives/hooks/access-control-hooks#role-providers) suggests that a role provider can be a "push" provider (one that "pushes" credentials into the hooks contract by calling `grantRole`) and a "pull" provider (one that the hook calls via `getCredential` or `validateCredential`).

The documentation also states that:

> Role providers do not have to implement any of these functions - a role provider can be an EOA.

But in fact, only the initial deployer can be an EOA provider, since it is coded in the constructor. Any other EOA provider that the borrower tries to add via `addRoleProvider` will fail because it does not implement the interface.
### Proof of Concept

PoC will revert because EOA does not implement interface obviously:

```
  [118781] AuditMarket::test_PoC_EOA_provider()
    ├─ [0] VM::startPrank(BORROWER1: [0xB193AC639A896a0B7a0B334a97f0095cD87427f2])
    │   └─ ← [Return]
    ├─ [29883] AccessControlHooks::addRoleProvider(RoleProvider: [0x2e234DAe75C793f67A35089C9d99245E1C58470b], 2592000 [2.592e6])
    │   ├─ [2275] RoleProvider::isPullProvider() [staticcall]
    │   │   └─ ← [Return] false
    │   ├─ emit RoleProviderAdded(providerAddress: RoleProvider: [0x2e234DAe75C793f67A35089C9d99245E1C58470b], timeToLive: 2592000 [2.592e6], pullProviderIndex: 16777215 [1.677e7])
    │   └─ ← [Stop]
    ├─ [74243] AccessControlHooks::addRoleProvider(RoleProvider: [0xF62849F9A0B5Bf2913b396098F7c7019b51A820a], 2592000 [2.592e6])
    │   ├─ [2275] RoleProvider::isPullProvider() [staticcall]
    │   │   └─ ← [Return] true
    │   ├─ emit RoleProviderAdded(providerAddress: RoleProvider: [0xF62849F9A0B5Bf2913b396098F7c7019b51A820a], timeToLive: 2592000 [2.592e6], pullProviderIndex: 0)
    │   └─ ← [Stop]
    ├─ [5547] AccessControlHooks::addRoleProvider(EOA_PROVIDER1: [0x6aAfF89c996cAa2BD28408f735Ba7A441276B03F], 2592000 [2.592e6])
    │   ├─ [0] EOA_PROVIDER1::isPullProvider() [staticcall]
    │   │   └─ ← [Stop]
    │   └─ ← [Revert] EvmError: Revert
    └─ ← [Revert] EvmError: Revert
```

**PoC**:
```solidity
// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "forge-std/console2.sol";

import {WildcatArchController} from "../src/WildcatArchController.sol";
import {HooksFactory} from "../src/HooksFactory.sol";
import {LibStoredInitCode} from "src/libraries/LibStoredInitCode.sol";
import {WildcatMarket} from "src/market/WildcatMarket.sol";
import {AccessControlHooks} from "../src/access/AccessControlHooks.sol";
import {DeployMarketInputs} from "../src/interfaces/WildcatStructsAndEnums.sol";
import {HooksConfig, encodeHooksConfig} from "../src/types/HooksConfig.sol";

import {MockERC20} from "../test/shared/mocks/MockERC20.sol";
import {MockSanctionsSentinel} from "./shared/mocks/MockSanctionsSentinel.sol";
import {deployMockChainalysis} from "./shared/mocks/MockChainalysis.sol";
import {IRoleProvider} from "../src/access/IRoleProvider.sol";

contract AuditMarket is Test {
    WildcatArchController wildcatArchController;
    MockSanctionsSentinel internal sanctionsSentinel;
    HooksFactory hooksFactory;

    MockERC20 ERC0 = new MockERC20();

    address immutable ARCH_DEPLOYER = makeAddr("ARCH_DEPLOYER");
    address immutable FEE_RECIPIENT = makeAddr("FEE_RECIPIENT");
    address immutable BORROWER1 = makeAddr("BORROWER1");

    address immutable EOA_PROVIDER1 = makeAddr("EOA_PROVIDER1");
    address immutable PROVIDER1 = address(new RoleProvider(false));
    address immutable PROVIDER2 = address(new RoleProvider(true));

    address accessControlHooksTemplate = LibStoredInitCode.deployInitCode(type(AccessControlHooks).creationCode);

    AccessControlHooks accessControlHooksInstance;

    function _storeMarketInitCode() internal virtual returns (address initCodeStorage, uint256 initCodeHash) {
        bytes memory marketInitCode = type(WildcatMarket).creationCode;
        initCodeHash = uint256(keccak256(marketInitCode));
        initCodeStorage = LibStoredInitCode.deployInitCode(marketInitCode);
    }

    function setUp() public {
        deployMockChainalysis();
        vm.startPrank(ARCH_DEPLOYER);
        wildcatArchController = new WildcatArchController();
        sanctionsSentinel = new MockSanctionsSentinel(address(wildcatArchController));
        (address initCodeStorage, uint256 initCodeHash) = _storeMarketInitCode();
        hooksFactory =
            new HooksFactory(address(wildcatArchController), address(sanctionsSentinel), initCodeStorage, initCodeHash);

        wildcatArchController.registerControllerFactory(address(hooksFactory));
        hooksFactory.registerWithArchController();
        wildcatArchController.registerBorrower(BORROWER1);

        hooksFactory.addHooksTemplate(
            accessControlHooksTemplate, "accessControlHooksTemplate", FEE_RECIPIENT, address(ERC0), 1 ether, 500
        );
        vm.startPrank(BORROWER1);

        DeployMarketInputs memory marketInput = DeployMarketInputs({
            asset: address(ERC0),
            namePrefix: "Test",
            symbolPrefix: "TT",
            maxTotalSupply: uint128(100_000e27),
            annualInterestBips: uint16(500),
            delinquencyFeeBips: uint16(500),
            withdrawalBatchDuration: uint32(5 days),
            reserveRatioBips: uint16(500),
            delinquencyGracePeriod: uint32(5 days),
            hooks: encodeHooksConfig(address(0), true, true, false, true, false, false, false, false, false, true, false)
        });
        bytes memory hooksData = abi.encode(uint32(block.timestamp + 30 days), uint128(1e27));
        deal(address(ERC0), BORROWER1, 1 ether);
        ERC0.approve(address(hooksFactory), 1 ether);
        (address market, address hooksInstance) = hooksFactory.deployMarketAndHooks(
            accessControlHooksTemplate,
            abi.encode(BORROWER1),
            marketInput,
            hooksData,
            bytes32(bytes20(BORROWER1)),
            address(ERC0),
            1 ether
        );
        accessControlHooksInstance = AccessControlHooks(hooksInstance);
        vm.stopPrank();
    }

    function test_PoC_EOA_provider() public {
        vm.startPrank(BORROWER1);

        accessControlHooksInstance.addRoleProvider(PROVIDER1, uint32(30 days));
        accessControlHooksInstance.addRoleProvider(PROVIDER2, uint32(30 days));
        accessControlHooksInstance.addRoleProvider(EOA_PROVIDER1, uint32(30 days));
    }
}

contract RoleProvider is IRoleProvider {
    bool public isPullProvider;
    mapping(address account => uint32 timestamp) public getCredential;

    constructor(bool _isPullProvider) {
        isPullProvider = _isPullProvider;
    }

    function setCred(address account, uint32 timestamp) external {
        getCredential[account] = timestamp;
    }

    function validateCredential(address account, bytes calldata data) external returns (uint32 timestamp) {
        if (data.length != 0) {
            return uint32(block.timestamp);
        } else {
            revert("Wrong creds");
        }
    }
}
```

### Recommended Mitigation

Replace the interface call with a low-level call and check if the user implements the interface in order to be a pull provider:

```solidity
(bool succes, bytes memory data) =
    providerAddress.call(abi.encodeWithSelector(IRoleProvider.isPullProvider.selector));
bool isPullProvider;
if (succes && data.length == 0x20) {
    isPullProvider = abi.decode(data, (bool));
} else {
    isPullProvider = false;
}
```

With this code all logic works as expected, for EOA providers `pullProviderIndex` is set to `type(uint24).max`, for contracts - depending on the result of calling `isPullProvider`:

```
Traces:
  [141487] AuditMarket::test_PoC_EOA_provider()
    ├─ [0] VM::startPrank(BORROWER1: [0xB193AC639A896a0B7a0B334a97f0095cD87427f2])
    │   └─ ← [Return]
    ├─ [30181] AccessControlHooks::addRoleProvider(RoleProvider: [0x2e234DAe75C793f67A35089C9d99245E1C58470b], 2592000 [2.592e6])
    │   ├─ [2275] RoleProvider::isPullProvider()
    │   │   └─ ← [Return] false
    │   ├─ emit RoleProviderAdded(providerAddress: RoleProvider: [0x2e234DAe75C793f67A35089C9d99245E1C58470b], timeToLive: 2592000 [2.592e6], pullProviderIndex: 16777215 [1.677e7])
    │   └─ ← [Stop]
    ├─ [74541] AccessControlHooks::addRoleProvider(RoleProvider: [0xF62849F9A0B5Bf2913b396098F7c7019b51A820a], 2592000 [2.592e6])
    │   ├─ [2275] RoleProvider::isPullProvider()
    │   │   └─ ← [Return] true
    │   ├─ emit RoleProviderAdded(providerAddress: RoleProvider: [0xF62849F9A0B5Bf2913b396098F7c7019b51A820a], timeToLive: 2592000 [2.592e6], pullProviderIndex: 0)
    │   └─ ← [Stop]
    ├─ [27653] AccessControlHooks::addRoleProvider(EOA_PROVIDER1: [0x6aAfF89c996cAa2BD28408f735Ba7A441276B03F], 2592000 [2.592e6])
    │   ├─ [0] EOA_PROVIDER1::isPullProvider()
    │   │   └─ ← [Stop]
    │   ├─ emit RoleProviderAdded(providerAddress: EOA_PROVIDER1: [0x6aAfF89c996cAa2BD28408f735Ba7A441276B03F], timeToLive: 2592000 [2.592e6], pullProviderIndex: 16777215 [1.677e7])
    │   └─ ← [Stop]
    └─ ← [Stop]
```

**[laurenceday (Wildcat) commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/49#issuecomment-2387986619):**

> Not really a medium in that it doesn't 'matter' for the most part: this is sort of a documentation issue in that we'd never really expect an EOA that _wasn't_ the borrower (which is an EOA provider) to be a role provider.
> 
> It's vanishingly unlikely that a borrower is going to add some random arbiter that they don't control - possible that they add another address that THEY control but in that case they might as well use the one that's known to us.
> 
> Disputing, but with a light touch: we consider this a useful QA.

**[3docSec (judge) commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/49#issuecomment-2391862173):**

> Thanks for the context. If we ignore the documentation, the fact that the initial role provider is the borrower, and the `NotPullProviderIndex` value that is used in this case makes it clear that the intention is allowing for EOAs to be there.
> 
> While not the most requested feature, it's something a borrower may want to do, and given the above, may reasonably expect to see working. For this reason, I think a Medium is reasonable because we have marginal I admit, but still tangible, availability impact.
### Notes & Impressions

**Impressions**

>*Overall, this is still an issue that the PCP doesn't match up with the SCP.*

**Notes**
In Solidity, an EOA can only:
- Send transactions
- Transfer funds
- Call other contracts
An EOA cannot:
- Have contract-specific functions
- Implement interface methods
- Return view/pure function results
When you do `IRoleProvider(providerAddress).isPullProvider()`, it's attempting to:
1. Cast the address to an interface
2. Call a specific method `isPullProvider()`
For a contract, this works normally:
```solidity
interface IRoleProvider {
    function isPullProvider() external view returns (bool);
}

// Contract can implement this
contract ValidRoleProvider is IRoleProvider {
    function isPullProvider() external view returns (bool) {
        return true; // or some logic
    }
}
```

But for an EOA:
- It has no code
- No function implementations
- No way to return `true/false` for `isPullProvider()`
So when you try to call `isPullProvider()` on an EOA, it will:
- Fail the interface cast
- Throw a runtime error
- Prevent the transaction

Low-level Call
```solidity
(bool success, bytes memory data) = 
    providerAddress.call(abi.encodeWithSelector(IRoleProvider.isPullProvider.selector));
bool isPullProvider;
if (success && data.length == 0x20) {
    isPullProvider = abi.decode(data, (bool));
} else {
    isPullProvider = false;
}
```

How this works:
- `call()` attempts to execute the function selector
- For an EOA:
	- `success` will be `false`
	- `data.length` will not be `0x20`
	- Defaults to `isPullProvider = false`
- For a contract:
	- If method exists: returns the actual boolean
	- If method doesn't exist: `success` is `false`
### Refine

[[logical_issues#[01] PCP vs SCP]]

---

## [M-08] `AccessControlHooks` `onQueueWithdrawal()` does not check if market is hooked which could lead to unexpected errors such as temporary DoS

----
- **Tags**: #compare_similar_funs_cross_cotract
- Number of finders: 4
- Difficulty: Easy
---
### Impact

The `onQueueWithdrawal()` function does not check if the caller is a hooked market, meaning anyone can call the function and attempt to verify credentials on a lender. This results in calls to registered pull providers with arbitrary hookData, which could lead to potential issues such as abuse of credentials that are valid for a short term, e.g. 1 block.

### Proof of Concept

The `onQueueWithdrawal()` function does not check if the msg.sender is a hooked market, which is standart in virtually all other hooks:

```solidity
  /**
   * @dev Called when a lender attempts to queue a withdrawal.
   *      Passes the check if the lender has previously deposited or received
   *      market tokens while having the ability to deposit, or currently has a
   *      valid credential from an approved role provider.
   */
  function onQueueWithdrawal(
    address lender,
    uint32 /* expiry */,
    uint /* scaledAmount */,
    MarketState calldata /* state */,
    bytes calldata hooksData
  ) external override {
    LenderStatus memory status = _lenderStatus[lender];
    if (
      !isKnownLenderOnMarket[lender][msg.sender] && !_tryValidateAccess(status, lender, hooksData)
    ) {
      revert NotApprovedLender();
    }
  }
```

If the caller is not a hooked market, the statement `!isKnownLenderOnMarket[lender][msg.sender]`, will return true, because the lender will be unknown. As a result the `_tryValidateAccess()` function will be executed for any `lender` and any `hooksData` passed. The call to `_tryValidateAccess()` will forward the call to `_tryValidateAccessInner()`. Choosing a lender of arbitrary address, say `address(1)` will cause the function to attempt to retrieve the credential via the call to `_handleHooksData()`, since the lender will have no previous provider or credentials.
t
As a result, the `_handleHooksData` function will forward the call to the encoded provider in the hooksData and will forward the extra hooks data as well, say merkle proof, or any arbitrary malicious data.

```solidity
  function _handleHooksData(
    LenderStatus memory status,
    address accountAddress,
    bytes calldata hooksData
  ) internal returns (bool validCredential) {
    // Check if the hooks data only contains a provider address
    if (hooksData.length == 20) {
      // If the data contains only an address, attempt to query a credential from that provider
      // if it exists and is a pull provider.
      address providerAddress = _readAddress(hooksData);
      RoleProvider provider = _roleProviders[providerAddress];
      if (!provider.isNull() && provider.isPullProvider()) {
        return _tryGetCredential(status, provider, accountAddress);
      }
    } else if (hooksData.length > 20) {
      // If the data contains both an address and additional bytes, attempt to
      // validate a credential from that provider
      return _tryValidateCredential(status, accountAddress, hooksData);
    }
  }
```

The function call will be executed in [tryValidateCredential()](https://github.com/code-423n4/2024-08-wildcat/blob/main/src/access/AccessControlHooks.sol#L525), where the extra hookData will be forwarded. As described in the function comments, it will execute a call to `provider.(address account, bytes calldata data)`.

This means that anyone can call the function and pass arbitrary calldata. This can lead to serious vulnerabilities as the calldata is passed to the provider.

Consider the following scenario:

- The pull provider is implemented to provide a short-term(say one block) approval timestamp.
- A user of the protocol provides a merkle-proof which would grant the one-time approval to withdraw in a transaction.
- A malicious miner frontruns the transaction submitting the same proof, but does not include the honest transaction in the mined block. Instead it is left for the next block.
- In the next block, the credential is no longer valid and as a result the honest user has their transaction revert.
- The miner does this continuosly essentially DoSing the entire market that uses this provider until it is removed and a new one added.

By following this scenario, a malicious user can essentially DoS a specific type pull provider.

Depending on implemenation of the pull provider, this can lead to other issues, as the malicious user can supply any arbitrary hookData in the function call.

### Recommended Mitigation

Require the caller to be a registered hooked market, same as [onQueueWithdrawal()](https://github.com/code-423n4/2024-08-wildcat/blob/main/src/access/FixedTermLoanHooks.sol#L848) in `FixedTermloanHooks`

**[3docSec (judge) commented via duplicate issue #83](https://github.com/code-423n4/2024-08-wildcat-findings/issues/83#issuecomment-2404270998):**

> I find this group compatible with the Medium severity for the following reasons:
> 
> - access to a lender's signature is very feasible in the frontrunning scenario depicted in this finding
> - the hypothesis on `validateCredential` isn't really a speculation but rather a very reasonable implementation, one that was also assumed in the [previous audit (finding number 2)](https://hackmd.io/@geistermeister/BJk4Ekt90).

**[laurenceday (Wildcat) acknowledged and commented](https://github.com/code-423n4/2024-08-wildcat-findings/issues/11#issuecomment-2431829302):**

> We don't consider this a real issue, in that we’ve always wanted it to be possible for anyone to call the validate function to poke a credential update. This finding assumes that you have the signature someone else would be using as a credential and generally relies on a specific implementation of the provider that doesn’t actually exist, so there's no need to check `isHooked`.
> 
> It's been upgraded to a Medium, and we're not going to argue with this at this stage. As such, we're acknowledging rather than confirming or disputing simply to put a cap on the report.
### Notes & Impressions

I presume it could be the following scenario. The auditors read the code and identified the `onQueueWithdrawal` function in the FixedTermLoanHooks and AccessControlHooks contracts. Upon careful examination, they noticed that one of them contained a judgement of hook market while the other did not. Subsequently, they further investigated whether this judgement would constitute a problem for the other contract. code: AccessControlHooks.sol

```
function onQueueWithdrawal(
    address lender,
    uint32 /* expiry */,
    uint /* scaledAmount */,
    MarketState calldata /* state */,
    bytes calldata hooksData
  ) external override {
    LenderStatus memory status = _lenderStatus[lender];
    if (
      !isKnownLenderOnMarket[lender][msg.sender] && !_tryValidateAccess(status, lender, hooksData)
    ) {
      revert NotApprovedLender();
    }
  }
```

FixedTermLoanHooks.sol

```
function onQueueWithdrawal(
    address lender,
    uint32 /* expiry */,
    uint /* scaledAmount */,
    MarketState calldata /* state */,
    bytes calldata hooksData
  ) external override {
    HookedMarket memory market = _hookedMarkets[msg.sender];
    if (!market.isHooked) revert NotHookedMarket();
    if (market.fixedTermEndTime > block.timestamp) {
      revert WithdrawBeforeTermEnd();
    }
    LenderStatus memory status = _lenderStatus[lender];
    if (market.withdrawalRequiresAccess) {
      if (
        !isKnownLenderOnMarket[lender][msg.sender] && !_tryValidateAccess(status, lender, hooksData)
      ) {
        revert NotApprovedLender();
      }
    }
  }
```

### Refine

[[common_issues#[05] Inconsistent Validation in Critical Functionality]]

---
## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}