
13/225 findings till 2024-12-13

*Business Logic - Logic vulnerabilities involve flaws in the business logic or protocols of a smart contract, where the implementation matches the developer's intention, but the underlying logic is inherently flawed.*

- The technical implementation matches the developer's intent
- The underlying logic can be strategically manipulated.
- The code does exactly what it was programmed to do.
- The vulnerability emerges from how the rules interact, not from a coding mistake.
## List of cases

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