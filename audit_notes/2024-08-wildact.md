# [2024-08-wildact](https://github.com/code-423n4/2024-08-wildcat-findings/blob/main/report.md)
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
## [H-01] User could withdraw more than supposed to, forcing last user withdraw to fail
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

##  [M-01] Users are incentivized to not withdraw immediately after the market is closed

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

## [M-02] `FixedTermLoanHooks` allow Borrower to update Annual Interest before end of the "Fixed Term Period"

----
- **Tags**: refer from #PCPvsSCP 
- Number of finders: 3
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
- **Tags**: refer from #consistency
- Number of finders: 6
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

核心问题：
1. 合约中存在多个具有还款功能的函数：
2. 但是这些函数的处理顺序不一致：有的是“先更改状态，再转账”，有的是“先转账，再更改状态”
3. 这些不一致最终导致相同的还款，最终金额不一致。
4. 为什么不同的处理顺序会导致金额不一致：因为状态更新时会计算累积的利息和费用
5. 项目方设计初衷：不同的函数，使用者是不同的。但是又没有做角色控制。

感想：
这是一个典型的 Consisitency（一致性）的问题。
- **一致性原则**: 相同的业务操作应该有统一的处理模式
- **最小惊讶原则**: 用户不应该因为调用不同函数而得到意外的结果
- **代码复用**: 应该将共同的业务逻辑抽象成统一的函数来处理
Checklist：
1. 检查合约中是否存在多个相同业务的函数（还款，存款）。
2. 如果存在，检查这些函数的业务操作是否一致。
3. 如果不一致，判断这种不一致的结果是否严重。
4. 如果发现多个相同业务的函数，检查是否有角色控制的需求
5. 检查相关函数的文档说明是否清晰指出了预期的使用者
6. 考察是否可以通过统一的内部函数来处理共同逻辑

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
## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}