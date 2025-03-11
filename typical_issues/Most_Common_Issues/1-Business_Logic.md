
13/226 findings till 2025-2-24

*Business Logic - Logic vulnerabilities involve flaws in the business logic or protocols of a smart contract, where the implementation matches the developer's intention, but the underlying logic is inherently flawed.*

- The technical implementation matches the developer's intent
- The underlying logic can be strategically manipulated.
- The code does exactly what it was programmed to do.
- The vulnerability emerges from how the rules interact, not from a coding mistake.
## List of cases

### 1-50
1. [[2023-08-immutable-security_review#[M-05] Withdrawal queue can be forcibly activated to hinder bridge operation|Withdrawal queue can be forcibly activated to hinder bridge operation]]
	- Withdraw queue mechanism -> Denial-of-Service
2. [[2023-07-primitive-spearbit-security-review#[M-01] `getSpotPrice, approximateReservesGivenPrice, getStartegyData` ignore time to maturity|[M-01] `getSpotPrice, approximateReservesGivenPrice, getStartegyData` ignore time to maturity]]
	- time-based-logic
3. [[2023-08-moonwell_finance-compound_vault_security_assessment#[M-02] Incorrect Use of Borrow Cap Instead of Supply Cap In `maxmint` function|[M-02] Incorrect Use of Borrow Cap Instead of Supply Cap In `maxmint` function]]
	- `max mint <= supply cap - totalSupply < borrowCap - totalBorrow`
4. [[2023-08-blueberry_update#[H-2] CurveTricryptoOracle incorrectly assumes that WETH is always the last token in the pool which leads to bad LP pricing|[H-2] CurveTricryptoOracle incorrectly assumes that WETH is always the last token in the pool which leads to bad LP pricing]]
	- Never hardcode assumptions about token order in multi-token pools
5. [[2023-09-pooltogether#[H-01] Too many rewards are distributed when a draw is closed|[H-01] Too many rewards are distributed when a draw is closed]]
	- Critical operation
		- close market
		- close draw
	- [[State_Transition_Maps]]
6. [[2023-08-smoothly#[H-02] Operator can still claim rewards after being removed from governance|[H-02] Operator can still claim rewards after being removed from governance]]
	- `delte-` or `close` --> **right** and **money**
7. [[2023-07-meta#[M-01] `MetaManager.unclaimedRewards` should work with shares instead of asset amounts.|[M-01] `MetaManager.unclaimedRewards` should work with shares instead of asset amounts.]]
	- amount ≠ share 
8. [[2023-06-dinari#[M-01] In case of stock split and reverse split, the Dshare token holder will gain or loss his Dshare token value|[M-01] In case of stock split and reverse split, the Dshare token holder will gain or loss his Dshare token value]]
	- When smart contracts are associated with the real economy (stock, reserve, futures), it is necessary to consider the features and risks of the real economy.
9. [[2023-07-nounsdao#[M-02] If DAO updates `forkEscrow` before `forkThreshold` is reached, the user's escrowed Nounns will be lost]]
	- Hard
	- Contract Change, Where is tokens?, who can withdraw?
10. [[2023-07-nounsdao#[M-03] `NounsDAOV3Proposals.cancel()` should allow to cancel the proposal of the Expired state|[M-03] `NounsDAOV3Proposals.cancel()` should allow to cancel the proposal of the Expired state]]
	- Using [[State_Transition_Maps]] 
11. [[2023-07-baton_launchpad#[H-01] Protocol fees from NFT mints can't be claimed in `BatonLaunchpad`|[H-01] Protocol fees from NFT mints can't be claimed in `BatonLaunchpad`]]
	- can `receive` fee, can not `withdraw` fee
	- similar a piggy bank
	- simply and serious problem
12. [[2023-06-lybra#[H-01] There is a vulnerability in the `executeFlashloan` function of the `PeUSDMainnet` contract. Hackers can use this vulnerability to burn other people's eUSD token balance without permission|[H-01] There is a vulnerability in the `executeFlashloan` function of the `PeUSDMainnet` contract. Hackers can use this vulnerability to burn other people's eUSD token balance without permission]]
	- flash loan `receiver` -> `msg.sender`
13. [[2023-05-maia#[M-31] Incorrect accounting logic for `fallback` gas will lead to insolvency|[M-31] Incorrect accounting logic for `fallback` gas will lead to insolvency]]
	- Reserve fallback gas upfront when starting cross-chain operations
14. [[2023-05-maia#[M-05] Replenishing gas is missing in `_payFallbackGas` of `RootBridgeAgent`|[M-05] Replenishing gas is missing in `_payFallbackGas` of `RootBridgeAgent`]]
	- Any call Gas management - cross-chain 
15. [[2023-05-stella#[H-01] Incorrect implementation of `getProfitSharingE18()` greatly reduces Lender's yield|[H-01] Incorrect implementation of `getProfitSharingE18()` greatly reduces Lender's yield]]
	- When APR is low: Lenders should get a larger share of profits (to incentivize lending)
	- When APR is high: Lenders should get a smaller share (as they're already earning well from interest)
16. [[2023-05-stella#[H-02] On liquidation, if netPnLE36 <= 0, the premium paid by the liquidator is locked in the contract.|[H-02] On liquidation, if netPnLE36 <= 0, the premium paid by the liquidator is locked in the contract.]]
	- premium ≠ profit
17. [[2023-05-stella#[H-06] An attacker can increase liquidity to the position's UniswapNFT to prevent the position from being closed|[H-06] An attacker can increase liquidity to the position's UniswapNFT to prevent the position from being closed]]
	- *A combination of factors (logics) contributed to this issue*
	- Uniswap V3 Pay attention:
		- remove liquidity
18. [[2023-05-stella#[H-07] Pending position fees miscalculation may result in increased PnL|[H-07] Pending position fees miscalculation may result in increased PnL]]
	- Uniswap V3
19. [[2023-05-stella#[H-08] “Exact output” swaps cannot be executed, blocking repayment of debt|[H-08] “Exact output” swaps cannot be executed, blocking repayment of debt]]
	- Uniswap V3
20. [[2023-05-liquid_collective#[H-01] `_pickNextValidatorsToExitFromActiveOperators` uses the wrong index to query stopped validator|[H-01] `_pickNextValidatorsToExitFromActiveOperators` uses the wrong index to query stopped validator]]
	- Array Index
	- Track data flow across function calls
21. [[2023-05-dodo-judging#[M-01] `MarginTrading.sol` the whole balance and not just the traded funds are deposited into Aave when a trade is opened|[M-01] `MarginTrading.sol` the whole balance and not just the traded funds are deposited into Aave when a trade is opened]]
	- Pay Attention to special boolean parameter: `_margin`
22. [[2023-05-blueberry#[M-03] Updating the `feeManager` on config will cause `desync` between bank and vaults|[M-03] Updating the `feeManager` on config will cause `desync` between bank and vaults]]
	- desynchronization -> pre-cache state variable (eg.address)
23. [[2023-04-blueberry#[H-01] Attackers will keep stealing the `rewards` from Convex SPELL|[H-01] Attackers will keep stealing the `rewards` from Convex SPELL]]
	- Coding bug
	- Pcp Vs Scp
24. [[2023-04-blueberry#[M-05] `getPositionRisk()` will return a wrong value of risk|[M-05] `getPositionRisk()` will return a wrong value of risk]]
	- Simple issue, hard to detect #simple_issue_hard_to_detect
25. [[2023-04-blueberry#[M-12] `rewardTokens` removed from `WAuraPool/WConvexPools` will be lost forever|[M-12] `rewardTokens` removed from `WAuraPool/WConvexPools` will be lost forever]]
	- Verify that reward accounting remains accurate if reward tokens are added/removed from underlying protocols.
26. [[2023-04-blueberry#[H-11] `ShortLongSpell openPosition` can cause user unexpected liquidation when increasing position size|[H-11] `ShortLongSpell openPosition` can cause user unexpected liquidation when increasing position size]]
	- **Dangerous Pattern**
		1. Complete collateral removal: Takes out ALL collateral first.
		2. Position replacement: Close existing position entirely, opens new larger position
27. [[2023-04-11-lifi#[M-02] The optional version `_depositAndSwap()` isn't always uded|[M-02] The optional version `_depositAndSwap()` isn't always uded]]
	- Watch out for native tokens, such as ETH.
	- Be mindful of unused functions.
28. [[2023-03-Morpho#[M-3] User `withdrawals` can fail if Morpho position is close to liquidation|[M-3] User `withdrawals` can fail if Morpho position is close to liquidation]]
	- Pay attention to withdraw operations,
	- Monitor the maximum LTV ratio,
	- Be mindful of the liquidation threshold.
29. [[2023-03-Morpho#[M-01] A market could be deprecated but still prevent liquidators to liquidate borrowers if `isLiquidateBorrowPaused` is `true`|[M-01] A market could be deprecated but still prevent liquidators to liquidate borrowers if `isLiquidateBorrowPaused` is `true`]]
	- Market Status (Deprecated/Closed)
	    - Interaction restrictions
	    - Order of operations during deprecation
	    - Proper cleanup mechanisms
	- Liquidation Status
	    - Pause/unpause conditions
	    - Emergency controls
	    - Impact on protocol solvency
30. [[2023-03-Morpho#[M-13] `claimToTreasury`(COMP) steals users' COMP rewards|[M-13] `claimToTreasury`(COMP) steals users' COMP rewards]]
	- COMP has two special characteristics that make this situation unique:
		1. COMP tokens are distributed as rewards to users of Compound protocol
		2. COMP itself can be used as a market asset (cCOMP) within Compound
	- Compound's reward claiming mechanism
		- Anyone can trigger reward claims on behalf of others.
31. [[2023-03-Morpho#[M-11] In Compound implementation, P2P indexes can be stale|[M-11] In Compound implementation, P2P indexes can be stale]]
	  - a subtle issue 
32. [[2023-03-Morpho#[M-04] P2P borrower's rate can be reduced|[M-04] P2P borrower's rate can be reduced]]
	- the special rate calculations
	- Issues caused by the special mechanism
33. [[2023-03-Morpho#[M-12] Turning off an asset as collateral on Morpho-Aave still allows seizing of that collateral on Morpho|[M-12] Turning off an asset as collateral on Morpho-Aave still allows seizing of that collateral on Morpho]] 
	- Position Aggregation: The aggregation contract combines all user positions into one large position on underlying protocols(Aave, compound).
		- The underlying protocols see one large pool of collateral owned by the aggregation contract
		- The aggregation contract internally tracks individual user positions
	- Multi-Protocol Integration
		- interact
		- collateral 
		- liquidation
	- Liquidation Mechanics
		- How: How can liquidation happen?
		- When: When can liquidation occur?
		- What: What prevents liquidation?
34. [[2023-03-Morpho#[M-14] Compound liquidity computation uses outdated cached borrowIndex|[M-14] Compound liquidity computation uses outdated cached borrowIndex]]
	- In this case, using Compound's live borrowIndex instead of Morpho's cached version would ensure accurate liquidation calculations.
35. [[2023-03-Morpho#[M-07] Users can continue to borrow from a deprecated market|[M-07] Users can continue to borrow from a deprecated market]]
	- Before critical operations (such as closing the market, deprecating the market), you should check wether the conditions for closing or deprecating are fulfilled (such as wether there are any pending loans).
36. [[2023-03-Morpho#[M-06] Differences between Morpho and Compound `borrow` validation logic|[M-06] Differences between Morpho and Compound `borrow` validation logic]]
	- Three Key difference between Morpho and Compound:
		1. borrowing caps
		2. deprecated markets
		3. `borrowGuardianPaused` feature
37. [[2023-02-seaport#[M-01] The spent offer amounts provided to `OrderFulfilled` for collection of (advanced) orders is not the actual amount spent in general|[M-01] The spent offer amounts provided to `OrderFulfilled` for collection of (advanced) orders is not the actual amount spent in general]]
	- *event emission issues*
	- all unspent offer amounts
38. [[2023-02-seaport#[M-02] The spent offer item amounts shared with a `zone` for restricted (advanced) orders or with a contract `offerer` for orders of `CONTRACT` order type is not the actual spent amount in general|[M-02] The spent offer item amounts shared with a `zone` for restricted (advanced) orders or with a contract `offerer` for orders of `CONTRACT` order type is not the actual spent amount in general]] 
	- same as above
39. [[2023-02-seaport#[M-03] Empty `criteriaResolvers` for criteria-based contract orders[M-03] Empty `criteriaResolvers` for criteria-based contract orders|[M-03] Empty `criteriaResolvers` for criteria-based contract orders[M-03] Empty `criteriaResolvers` for criteria-based contract orders]]
	- #bait_and_switch scenario
40. [[2023-02-seaport#[M-04] Advance orders of CONTRACT order types can generate orders with less consideration items that would break the aggregation routine|[M-04] Advance orders of CONTRACT order types can generate orders with less consideration items that would break the aggregation routine]]
	1. State Changes Between Preview and Execution
	2. Array Index Validation
41. [[2023-02-blueberry#[H-07] Users can be liquidated prematurely because calculation understates value of underlying position|[H-07] Users can be liquidated prematurely because calculation understates value of underlying position]]
	- When calculating, check the variables involved in the calculations: 
	* Check if the definitions are correct. 
	* Check for any changes.
42. [[2023-02-clober#[M-01] Group claim clashing condition|[M-01] Group claim clashing condition]]
	- *This is a typical issue, and we need to pay attention to it, especially when auditing transactions within a for-loop.*
43. [[2023-02-astaria#[H-03] `VaultImplementation.buyoutLien` does not update the new public vault's parameters and does not transfer assets between the vault and the borrower|[H-03] `VaultImplementation.buyoutLien` does not update the new public vault's parameters and does not transfer assets between the vault and the borrower]]
	- Check the updates of states  
		- Correctness of the update.
		- Whether all updates have been made
44. [[2023-02-astaria#[H-05] A borrower can list their collateral on Seaport and receive almost all the listing price without paying back their liens|[H-05] A borrower can list their collateral on Seaport and receive almost all the listing price without paying back their liens]]
	- Subtlety: The vulnerability is complex because it involves:
	    - Interaction between multiple contracts (CollateralToken, ClearingHouse, Seaport)
	    - Lack of state updates (auctionData not being populated)
	    - A non-obvious control flow where the fallback function fails silently
	    - Different execution paths for self-listing vs liquidator auctions
45. [[2023-02-astaria#[H-11] `processEpoch()` needs to be called regularly|[H-11] `processEpoch()` needs to be called regularly]]
	- Check whether time-based epochs increase as expected
		- Epoch/period increments
		- Required sequential processing
		- Blocking conditions
46. [[2023-02-astaria#[H-01] Collateral owner can steal funds by taking liens while asset is listed for sale on Seaport|[H-01] Collateral owner can steal funds by taking liens while asset is listed for sale on Seaport]]
	- same as [[2023-02-astaria#[H-05] A borrower can list their collateral on Seaport and receive almost all the listing price without paying back their liens|[H-05] A borrower can list their collateral on Seaport and receive almost all the listing price without paying back their liens]]
47. [[2023-02-astaria#[M-07] Call to Royalty Engine can block NFT auction|[M-07] Call to Royalty Engine can block NFT auction]]
	- The same function was called twice with different parameters
	- One instance had error handling while the other didn't
49. [[2023-02-astaria#[H-20] `commitToLiens` transfers extra assets to the borrower when protocol fee is present|[H-20] `commitToLiens` transfers extra assets to the borrower when protocol fee is present]]
	- we should repeatedly verify whether the financial calculations(such as interest and fees) are correctly implemented in the code during future audit tasks.
50. [[2023-02-astaria#[H-02] Inequalities involving `liquidationInitialAsk` and `potentialDebt` can be broken when `buyoutLien` is called|[H-02] Inequalities involving `liquidationInitialAsk` and `potentialDebt` can be broken when `buyoutLien` is called]]
### 51-100
51. [[2023-02-astaria#[H-21] `WithdrawProxy` allows redemptions before `PublicVault` calls `transferWithdrawReserve`|[H-21] `WithdrawProxy` allows redemptions before `PublicVault` calls `transferWithdrawReserve`]]
	1. Pay attention to `withdraw` operation.
	2. ERC4626 withdrawal system, shares and underlying assets
	3. Fixed Share Price 
52. [[2023-02-astaria#[H-06] Incorrect auction end validation in `liquidatorNFTClaim()`|[H-06] Incorrect auction end validation in `liquidatorNFTClaim()`]]
	1. *In smart contracts, time is not reliable; it can be altered.*
53. [[2023-02-astaria#[M-05] If auction time is reduced, `withdrawProxy` can lock funds from final auctions|[M-05] If auction time is reduced, `withdrawProxy` can lock funds from final auctions]]
	- Check how duration changes affect existing process
54. [[2023-02-astaria#[H-10] Refactor `_paymentAH()`|[H-10] Refactor `_paymentAH()`]]
	1. Check array parameter types (memory vs storage)
	2. Look for redundant state updates before deletions 
	3. Trace parameter values after state changes
	4. Review function call requirements and permissions
	5. Look for overly complex conditional logic
55. [[2023-02-astaria#[M-04] UniV3 tokens with fees can bypass strategist checks|[M-04] UniV3 tokens with fees can bypass strategist checks]]
	1. Special attention should be given to situations where multiple conditions are connected with 'and' during the audit. We can use a truth table to analyze whether all conditions match the expected results.
56. [[2023-02-astaria#[H-22] Withdraw proxy's `claim()` endpoint updates public vault's `yIntercept` incorrectly||[H-22] Withdraw proxy's `claim()` endpoint updates public vault's `yIntercept` incorrectly]]
	The current code only handles the case when `balance < s.expected`, but it should handle both cases:
	1. When `balance < s.expected`: The vault received less than expected
	2. When `balance > s.expected`: The vault received more than expected (e.g., from high-value auction sales)
57. [[2023-02-astaria#[M-10] `redeemFutureEpoch` transfers the shares from the `msg.sender` to the vault instead of from the `owner`|[M-10] `redeemFutureEpoch` transfers the shares from the `msg.sender` to the vault instead of from the `owner`]]
	1. `owner ≠ msg.sender`
58. [[2023-01-popcorn#[H-09] Attacker can steal 99% of total balance from any reward token in any Staking contract|[H-09] Attacker can steal 99% of total balance from any reward token in any Staking contract]]
	1. I think the core of this finding is that we should check whether crucial parameters have limits(such as rate, speed, ratio,)
59.  [[2023-01-ajna#[M-04] Incorrect MOMP calculation in neutral price calculation|[M-04] Incorrect MOMP calculation in neutral price calculation]]
	- Error Type: Part Vs Whole
60. [[2023-01-ajna#[M-16] Auction timers following liquidity can fall through the floor price causing pool insolvency|[M-16] Auction timers following liquidity can fall through the floor price causing pool insolvency]]
	1. The lack of a minimum price floor in the liquidation auction mechanism
61. [[2023-01-ajna#[H-07] ERC721Pool's `mergeOrRemoveCollateral` allows to remove collateral while auction is clearable|[H-07] ERC721Pool's `mergeOrRemoveCollateral` allows to remove collateral while auction is clearable]]
	1. The key point of this findings is that we should ensure that all necessary requirements are met before any critical process, especially those involving finance.
62. [[2023-01-ajna#[M-08] Claiming accumulated rewards while the contract is underfunded can lead to a loss of rewards|[M-08] Claiming accumulated rewards while the contract is underfunded can lead to a loss of rewards]]
	1. *Unfairly capped rewards*
63. [[2023-01-ajna#[M-22] Memorializing an NFT position on the same bucket of a previously memorialized NFT locks redemption|[M-22] Memorializing an NFT position on the same bucket of a previously memorialized NFT locks redemption]]
	1. Error Type: Part Vs Whole
64. [[2023-01-ajna#[M-11] Settled collateral of a borrower aren't available for lenders until borrower's debt is fully cleared|[M-11] Settled collateral of a borrower aren't available for lenders until borrower's debt is fully cleared]]
	1. Key warning signs:
		- Single-condition state updates (`if (x == 0)` rather than handling all cases)
		- Asset transfers without corresponding state updates
		- Functions that handle partial operations without proper cleanup
		- Discrepancies between accounting systems (e.g., user balances vs. pool balances)
65. [[2023-01-ajna#[M-12] Deposits are eliminated before currently unclaimed reserves when there is no reserve auction|[M-12] Deposits are eliminated before currently unclaimed reserves when there is no reserve auction]]
	1. pay attention to edge cases (unclaimed)
66. [[2023-01-liquid-collective#[M-01] Coverage funds might be pulled not only for the purpose of covering slashing losses|[M-01] Coverage funds might be pulled not only for the purpose of covering slashing losses]]
	1. #PCPvsSCP 
	2. *A critical misalignment between the code's logic and the Coverage Fund's intended purpose.*
67. [[2023-01-cooler#[H-03] Fully repaying a loan will result in debt payment being lost]]
	1. Danger of `delete` on Structs
		- In Solidity, when you delete a struct from storage, all its fields are reset to their default values. So loan.lender becomes address(0) because that's the default for address types.
	2. Funds First, Delete Last
		- **Always finalize financial transactions** _before_ modifying or deleting state variables they depend on.
68. [[2023-01-cooler#[M-02] Loan is rollable by default|[M-02] Loan is rollable by default]]
	1. *Is Loan rollable by default？*
69. [[2023-01-cooler#[M-04] Dust amounts can cause payments to fail, leading to default|[M-04] Dust amounts can cause payments to fail, leading to default]]
	- Repayments **cannot exceed the remaining loan balance**
70. [[2023-01-cooler#[H-02] Loans can be rolled an unlimited number of times|[H-02] Loans can be rolled an unlimited number of times]]
	1. Even if a lender allows rolling, there's no cap on the number of times a borrower can roll the loan. This could lead to indefinite extensions, especially problematic with depreciating collateral.
71. [[2023-01-UXD#[M-06] Inaccurate Perp debt calculation|[M-06] Inaccurate Perp debt calculation]]
	1. #Double-check_the_complex_calculation 
72. [[2023-01-UXD#[H-01] `PerpDespository reblance` and `rebalanceLite` can be called to drain funds from anyone who has approved `PerpDepository`|[H-01] `PerpDespository reblance` and `rebalanceLite` can be called to drain funds from anyone who has approved `PerpDepository`]]
	1. **The victim pays the shortfall**: 
	2. **The victim’s allowance is drained**:  
73. [[2023-01-UXD#[H-03] RageTrade senior vault USDC deposits are subject to utilization caps which can lock deposits for long periods of time leading to UXD instability|[H-03] RageTrade senior vault USDC deposits are subject to utilization caps which can lock deposits for long periods of time leading to UXD instability]]
	1. *The core issue revolves around the **utilization cap** (max cap) implemented in the RageTrade senior vault, which is designed to ensure solvency but inadvertently introduces a liquidity risk by potentially blocking withdrawals during periods of **high demand**.*
74. [[2023-01-UXD#[H-05] USDC deposited to `PerpDepository.sol` are irretrievable and effectively causes UDX to become `undercollateralized`|[H-05] USDC deposited to `PerpDepository.sol` are irretrievable and effectively causes UDX to become `undercollateralized`]]
	1. *Untracked USDC in Rebalancing*
75. [[2023-01-UXD#[M-02] `PerpDepository._rebalanceNegativePnlWithSwap()` shouldn't use a `sqrtPriceLimitX96` twice.|[M-02] `PerpDepository._rebalanceNegativePnlWithSwap()` shouldn't use a `sqrtPriceLimitX96` twice.]]
	1. Different pool have different `sqrtPriceLimitX96` (**maximum/minimum price** a swap will accept) in Uniswap V3
76. [[2024-10-Primodium#[C-02] The portion of the pot corresponding to locked points is not distributed to the players|[C-02] The portion of the pot corresponding to locked points is not distributed to the players]]
	1. calculating portions or shares using fractions
77. [[2022-12-liquid-collective#[H-2] Order of calls to `removeValidators` can affect the resulting validator keys set|[H-2] Order of calls to `removeValidators` can affect the resulting validator keys set]]
	1. Functions that modify shared state (like arrays/sets) where transaction ordering matters:
		- Multiple parties can call the same function
		- State changes affect subsequent operations
		- No mechanism to handle concurrent modifications
78. [[2022-12-liquid-collective#[C-3] `OperatorsRegistry._getNextValidatorsFromActiveOperators` can DOS Alluvial staking if there's an operator with `funded==stopped` and `funded == min(limit, keys)`|[C-3] `OperatorsRegistry._getNextValidatorsFromActiveOperators` can DOS Alluvial staking if there's an operator with `funded==stopped` and `funded == min(limit, keys)`]]
	1. *Mathematical equivalence doesn't mean functional equivalence.*
79. [[2022-12-liquid-collective#[M-2] `_getNextValidatorsFromActiveOperators` can be tweaked to find an operator with a better validator pool|[M-2] `_getNextValidatorsFromActiveOperators` can be tweaked to find an operator with a better validator pool]]
	1. same as 79
80. [[2022-12-liquid-collective#[M-8] `OperatorsRegistry._getNextValidatorsFromActiveOperators`should not consider `stopped` when picking a validator|[M-8] `OperatorsRegistry._getNextValidatorsFromActiveOperators`should not consider `stopped` when picking a validator]]
	1. same as 79
81. [[2022-12-liquid-collective#[M-11] `OracleV1.getMemberReportStatus` returns true for non existing oracles]]
82. [[2022-11-backed#[H-01] Borrowers may earn auction proceeds without filling the debt shortfall|[H-01] Borrowers may earn auction proceeds without filling the debt shortfall]]
	1. Ensure all potential contributions to a final outcome are fully accounted for before making irreversible decisions.
83. [[2022-11-backed#[M-02] Disabled NFT collateral should not be used to mint debt|[M-02] Disabled NFT collateral should not be used to mint debt]]
	1. Checks when adding but missing checks when updating (increasing)
84. [[2022-11-backed#[M-05] `PaprController.buyAndReduceDebt msg.sender` can lose paper by paying the debt twice|[M-05] `PaprController.buyAndReduceDebt msg.sender` can lose paper by paying the debt twice]]
	- In debt process: `msg.sender` and `account` can be different addresses such that one can repay anyone's debt.
	- Pay attention `msg.sender` and `account`
	- Who provides the funds (`pay` or `burns from`)?
	- Who receives the benefit (`recipoent`,`to`)?
85. [[2022-11-backed#[M-06] `PaprController` pays swap fee in `buyAndReduceDebt`, not user|[M-06] `PaprController` pays swap fee in `buyAndReduceDebt`, not user]]
	1. *Always verify which entity (contract or user) should be the source of funds in any token transfer operation.*
		- **Transfer Method Mismatch**: Using `transfer()` when `transferFrom()` is needed, or vice versa
		    - `transfer()` = contract's own funds
		    - `transferFrom()` = user's pre-approved funds
		- **Fee Payment Responsibility**: When implementing fee mechanisms, be explicit about who pays:
		    - User pays fee → use `transferFrom(msg.sender, recipient, amount)`
		    - Protocol pays fee → use `transfer(recipient, amount)` with proper accounting
86. [[2022-12-connext#[H-01] `swapInternal()` shouldn't use `msg.sender`|[H-01] `swapInternal()` shouldn't use `msg.sender`]]
	1. `replyer A ---> BridgeFacet.execute() - msg.sender = A ---> BridgeFacet._handleExecuteLiquidity() - msg.sender = A ---> AssetLogic.swapFromLocalAssetIfNeeded() - msg.sender = A ---> AssetLogic._swapAsset() - msg.sender = A ---> SwapUtils.swapInternal msg.sender = A`
	2. Checks relayer's balance instead of pool's balance
87. [[2022-12-connext#[H-7] No way to update a Stable Swap once assigned to a key|[H-7] No way to update a Stable Swap once assigned to a key]]
	1. *Smart contracts should implement complete lifecycle management for all critical system components*
		1. Initialization mechanisms
		2. Update mechanisms
		3. Removal/deprecation mechanisms
		4. Emergency pause/shutdown mechanisms
88. [[2022-12-connext#[H-09] No way of removing Fraudulent Roots|[H-09] No way of removing Fraudulent Roots]]
	1. See above
89. [[2022-12-connext#[H-11] Missing mirrorConnector check on Optimism hub connector|[H-11] Missing mirrorConnector check on Optimism hub connector]]
	1. always check for alternative entry points to critical functionality
90. [[2022-12-connext#[M-06] The set of tokens in an internal swap pool cannot be updated|[M-06] The set of tokens in an internal swap pool cannot be updated]]
	1. See 
		1. [[2022-12-connext#[H-07] No way to update a Stable Swap once assigned to a key|[H-07] No way to update a Stable Swap once assigned to a key]]
		2. [[2022-12-connext#[H-09] No way of removing Fraudulent Roots|[H-09] No way of removing Fraudulent Roots]]
91. [[2022-12-connext#[M-10] `TypedMemView.sameType` does not use the correct right shift value to compare two `bytes29`s|[M-10] `TypedMemView.sameType` does not use the correct right shift value to compare two `bytes29`s]]
	1. *When performing bitwise operations on packed data structures, ensure the bit shifting exactly isolates the intended components, accounting for any padding that occurs during type conversions.*
92. [[2022-12-prePO#[H-01] griefing / blocking / delaying users to withdraw|[H-01] griefing / blocking / delaying users to withdraw]]
	1. When a protocol manages user-specific operations (like withdrawals or deposits), each user's critical state variables should be isolated in mappings rather than sharing global variables that affect multiple users.
		1. [[State_Isolation_vs_Sharing]]
93. [[2022-12-prePO#[M-04] PrePO NFT holders will not be able to redeem collateral|[M-04] PrePO NFT holders will not be able to redeem collateral]]
	1. #authorization_asymmetry 
94.  [[2022-12-prePO#[M-05] `PrePOMarket.setFinalLongPayout()` shouldn't be called twice.|[M-05] `PrePOMarket.setFinalLongPayout()` shouldn't be called twice.]]
	- Once user actions (like token redemptions) are taken based on a contract state, that state should either be immutable or changes to it must account for all previous actions.
95. [[2022-12-prePO#[M-07] Users do not receive owed tokens if `TokenSender` contract cannot cover their owed amount.|[M-07] Users do not receive owed tokens if `TokenSender` contract cannot cover their owed amount.]]
	1. *The `TokenSender` contract silently fails when it lacks sufficient tokens to pay user rebates, without tracking unpaid amounts or providing a mechanism for users to claim them later.*
96. [[2022-11-isomorph#[H-01] User is unable to partially payback loan if they aren't able to post enough isoUSD to bring them back to minOpeningMargin|[H-01] User is unable to partially payback loan if they aren't able to post enough isoUSD to bring them back to minOpeningMargin]]
	1. #Excessive_Constraint_Propagation
97. [[2022-11-isomorph#[H-02] The calculation of `totalUSDborrowed` in `openLoan()` is not correct|[H-02] The calculation of `totalUSDborrowed` in `openLoan()` is not correct]]
	1. #Double-check_the_complex_calculation 
98. [[2022-11-isomorph#[H-07] User can steal rewards from other users by withdrawing their Velo Deposit NFTs from other users' depositors|[H-07] User can steal rewards from other users by withdrawing their Velo Deposit NFTs from other users' depositors]]
	1. Missing authentication checks
	2. Check `DepositReceipt`  same?
99. [[2022-11-isomorph#[H-09] Swapping 100 tokens in `DepositReceipt_ETH` and `DepositReciept_USDC` breaks usage of `WBTC LP` and other high value tokens|[H-09] Swapping 100 tokens in `DepositReceipt_ETH` and `DepositReciept_USDC` breaks usage of `WBTC LP` and other high value tokens]]
	1. Dynamic vs. Fixed Parameters
100. [[2022-11-isomorph#[M-05] `increaseCollateralAmount` User is not allowed to increase collateral freely.|[M-05] `increaseCollateralAmount` User is not allowed to increase collateral freely.]]
	1. #Excessive_Constraint_Propagation 
### 101-150
101. [[2022-12-NounsDAO#[M-07] Payer cannot withdraw accidental extra funds sent to the contract without canceling|[M-07] Payer cannot withdraw accidental extra funds sent to the contract without canceling]]
	1. Streaming Token should be `rescue`
102. [[2022-12-maple#[M-01] Users depositing to a pool with unrealized losses will take on the losses|[M-01] Users depositing to a pool with unrealized losses will take on the losses]]
	1.  _Inconsistent or incomplete valuation mechanisms in transaction pricing can lead to mispricing and unfair outcomes for participants._
103. [[2022-12-maple#[M-03] Unaccounted collateral is mishandled in `triggerDefault`|[M-03] Unaccounted collateral is mishandled in `triggerDefault`]]
	1. *Always verify on-chain state for critical operations, especially when handling external assets or user inputs.*
		1. The balances maintained by ERC20 contract are considered trustworthy. 代币合约中的余额更可信。
104. [[2022-12-sentiment#[M-01] `getRewards()` can be triggered by external parties which will result in the rewards not be tracking properly by the system|[M-01] `getRewards()` can be triggered by external parties which will result in the rewards not be tracking properly by the system]]
	1. #financial_bypass 
	2. When a financial protocol has functions that can be called directly (no access control) that handle value but don't properly update internal accounting systems, critical financial invariants can break.
105. [[2022-11-redactedcartel#[H-06] fee loss in `AutoPxGmx` and `AutoPxGlp` and reward loss in `AutoPxGlp` by calling `PirexRewards.claim(pxGmx/pxGpl, AutoPx*)` directly which transfers rewards to `AutoPx`* pool without compound logic get executed and fee calculation logic and `pxGmx` wouldn't be executed for those rewards|[H-06] fee loss in `AutoPxGmx` and `AutoPxGlp` and reward loss in `AutoPxGlp` by calling `PirexRewards.claim(pxGmx/pxGpl, AutoPx*)` directly which transfers rewards to `AutoPx`* pool without compound logic get executed and fee calculation logic and `pxGmx` wouldn't be executed for those rewards]]
	1. #financial_bypass 
106. [[2022-11-redactedcartel#[M-12] Reward tokens mismanagement can cause users losing rewards|[M-12] Reward tokens mismanagement can cause users losing rewards]]
	1. Hard-coded list in one contract (`PirexGmx`)
	2. Dynamic, owner-controlled list in another contract (`PirexRewards`)
	3. **State Update Before Action Completion**: User's reward state is reset to 0 _before_ rewards are actually transferred
107. [[2022-11-frankendao#[M-06] Staking `changeStakeTime` and `changeStakeAmount` are problematic given current staking design|[M-06] Staking `changeStakeTime` and `changeStakeAmount` are problematic given current staking design]]
	1. *When a protocol stores calculated values based on global parameters instead of calculating them on-demand, parameter changes can create permanent inequities between users.*
108. [[2022-11-frankendao#[M-07] `castVote` can be called by anyone even those without votes|[M-07] `castVote` can be called by anyone even those without votes]]
	1. The smart contract allows users with zero voting power to cast votes and receive refunds, enabling an attacker to create multiple addresses and drain the vault through mass zero-vote submissions.
109. [[2022-11-buffer#[M-03 ] `resolveQueuedTrades`is intended to be non atomic but invalid signature can still cause entire transaction to revert|[M-03 ] `resolveQueuedTrades`is intended to be non atomic but invalid signature can still cause entire transaction to revert]]
	1. `ECDSA.recover` need `try` statement.
110. [[2022-11-rage_trade#[H-02] `DnGmxJuniorVaultManager._rebalanceBorrow` logic is flawed and could result in vault liquidation|[H-02] `DnGmxJuniorVaultManager._rebalanceBorrow` logic is flawed and could result in vault liquidation]]
	1. *This is a total logic error.*
	2. **Principle**: Verify that conditional logic correctly aligns actions with intended outcomes across all possible input scenarios, especially in multi-variable systems.
111. [[2022-11-stakehouse#[H-01] Any user being the first to claim rewards from `GiantMevAndFeesPool` can unexepectedly collect them all|[H-01] Any user being the first to claim rewards from `GiantMevAndFeesPool` can unexepectedly collect them all]]
	1. The core vulnerability is indeed about how to properly handle rewards that arrive before any users have deposited into the pool.
112. [[2022-11-stakehouse#[H-03] Theft of ETH of free floating SLOT holders|[H-03] Theft of ETH of free floating SLOT holders]]
	1. **Always ensure proper accounting in cumulative financial systems**.  `+=` vs `=`
113. [[2022-11-stakehouse#[H-08] function `withdrawETH` from `GiantMevAndFeesPool` can steal most of `eth` because of `idleETH` is reduced before burning token|[H-08] function `withdrawETH` from `GiantMevAndFeesPool` can steal most of `eth` because of `idleETH` is reduced before burning token]]
	1. State variables must be updated in the correct sequence, especially when those variables are used in financial calculations that might be triggered by subsequent operations in the same function.
114. [[2022-11-stakehouse#[M-21] EIP1559 rewards received by syndicate during the period when it has no registered knots can be lost|[M-21] EIP1559 rewards received by syndicate during the period when it has no registered knots can be lost]]
	1. **Always handle all possible states of your system, especially edge cases like "zero" or "empty" states**.
115. [[2022-11-stakehouse#[M-22] ETH sent when calling executeAsSmartWallet function can be lost|[M-22] ETH sent when calling executeAsSmartWallet function can be lost]]
	1. In Ethereum and Solidity, when you call a function with ETH (using `{value: amount}`), that ETH is transferred directly to the contract being called. However, that ETH doesn't automatically "flow through" to any subsequent contract calls unless you explicitly forward it.
116. [[2022-11-stakehouse#[M-25] Incorrect checking in `_assertUserHasEnoughGiantLPToClaimVaultLP`|[M-25] Incorrect checking in `_assertUserHasEnoughGiantLPToClaimVaultLP`]]
	1. When validating state conditions for specific token operations, always ensure that the state being checked corresponds directly to the specific token being operated on, not a global or unrelated token.
	2. programming error
117. [[2022-11-stakehouse#[M-28] Funds are not claimed from syndicate for valid BLS keys of first key is invalid (no longer part of syndicate).|[M-28] Funds are not claimed from syndicate for valid BLS keys of first key is invalid (no longer part of syndicate).]]
	1. The Single Point of Failure Anti-Pattern
		This issue exemplifies a broader principle in smart contract design: **avoid making the execution of critical business logic dependent on a single validation check that isn't directly related to that logic**.







