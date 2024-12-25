
13/225 findings till 2024-12-13

*Business Logic - Logic vulnerabilities involve flaws in the business logic or protocols of a smart contract, where the implementation matches the developer's intention, but the underlying logic is inherently flawed.*

- The technical implementation matches the developer's intent
- The underlying logic can be strategically manipulated.
- The code does exactly what it was programmed to do.
- The vulnerability emerges from how the rules interact, not from a coding mistake.
## List of cases

- [[2023-08-immutable-security_review#[M-05] Withdrawal queue can be forcibly activated to hinder bridge operation|Withdrawal queue can be forcibly activated to hinder bridge operation]]
	- Withdraw queue mechanism -> Denial-of-Service
- [[2023-07-primitive-spearbit-security-review#[M-01] `getSpotPrice, approximateReservesGivenPrice, getStartegyData` ignore time to maturity|[M-01] `getSpotPrice, approximateReservesGivenPrice, getStartegyData` ignore time to maturity]]
	- time-based-logic
- [[2023-08-moonwell_finance-compound_vault_security_assessment#[M-02] Incorrect Use of Borrow Cap Instead of Supply Cap In `maxmint` function|[M-02] Incorrect Use of Borrow Cap Instead of Supply Cap In `maxmint` function]]
	- `max mint <= supply cap - totalSupply < borrowCap - totalBorrow`
- [[2023-08-blueberry_update#[H-2] CurveTricryptoOracle incorrectly assumes that WETH is always the last token in the pool which leads to bad LP pricing|[H-2] CurveTricryptoOracle incorrectly assumes that WETH is always the last token in the pool which leads to bad LP pricing]]
	- Never hardcode assumptions about token order in multi-token pools
- [[2023-09-pooltogether#[H-01] Too many rewards are distributed when a draw is closed|[H-01] Too many rewards are distributed when a draw is closed]]
	- Critical operation
		- close market
		- close draw
	- [[State_Transition_Maps]]
- [[2023-08-smoothly#[H-02] Operator can still claim rewards after being removed from governance|[H-02] Operator can still claim rewards after being removed from governance]]
	- `delte-` or `close` --> **right** and **money**
- [[2023-07-meta#[M-01] `MetaManager.unclaimedRewards` should work with shares instead of asset amounts.|[M-01] `MetaManager.unclaimedRewards` should work with shares instead of asset amounts.]]
	- amount ≠ share 
- [[2023-06-dinari#[M-01] In case of stock split and reverse split, the Dshare token holder will gain or loss his Dshare token value|[M-01] In case of stock split and reverse split, the Dshare token holder will gain or loss his Dshare token value]]
	- When smart contracts are associated with the real economy (stock, reserve, futures), it is necessary to consider the features and risks of the real economy.
- [[2023-07-nounsdao#[M-02] If DAO updates `forkEscrow` before `forkThreshold` is reached, the user's escrowed Nounns will be lost]]
	- Hard
	- Contract Change, Where is tokens?, who can withdraw?
- [[2023-07-nounsdao#[M-03] `NounsDAOV3Proposals.cancel()` should allow to cancel the proposal of the Expired state|[M-03] `NounsDAOV3Proposals.cancel()` should allow to cancel the proposal of the Expired state]]
	- Using [[State_Transition_Maps]]
- [[2023-07-baton_launchpad#[H-01] Protocol fees from NFT mints can't be claimed in `BatonLaunchpad`|[H-01] Protocol fees from NFT mints can't be claimed in `BatonLaunchpad`]]
	- can `receive` fee, can not `withdraw` fee
	- similar a piggy bank
	- simply and serious problem
- [[2023-06-lybra#[H-01] There is a vulnerability in the `executeFlashloan` function of the `PeUSDMainnet` contract. Hackers can use this vulnerability to burn other people's eUSD token balance without permission|[H-01] There is a vulnerability in the `executeFlashloan` function of the `PeUSDMainnet` contract. Hackers can use this vulnerability to burn other people's eUSD token balance without permission]]
	- flash loan `receiver` -> `msg.sender`
- [[2023-05-maia#[M-31] Incorrect accounting logic for `fallback` gas will lead to insolvency|[M-31] Incorrect accounting logic for `fallback` gas will lead to insolvency]]
	- Reserve fallback gas upfront when starting cross-chain operations
- [[2023-05-maia#[M-05] Replenishing gas is missing in `_payFallbackGas` of `RootBridgeAgent`|[M-05] Replenishing gas is missing in `_payFallbackGas` of `RootBridgeAgent`]]
	- Any call Gas management - cross-chain 
- [[2023-05-stella#[H-01] Incorrect implementation of `getProfitSharingE18()` greatly reduces Lender's yield|[H-01] Incorrect implementation of `getProfitSharingE18()` greatly reduces Lender's yield]]
	- When APR is low: Lenders should get a larger share of profits (to incentivize lending)
	- When APR is high: Lenders should get a smaller share (as they're already earning well from interest)
- [[2023-05-stella#[H-02] On liquidation, if netPnLE36 <= 0, the premium paid by the liquidator is locked in the contract.|[H-02] On liquidation, if netPnLE36 <= 0, the premium paid by the liquidator is locked in the contract.]]
	- premium ≠ profit
- [[2023-05-stella#[H-06] An attacker can increase liquidity to the position's UniswapNFT to prevent the position from being closed|[H-06] An attacker can increase liquidity to the position's UniswapNFT to prevent the position from being closed]]
	- *A combination of factors (logics) contributed to this issue*
	- Uniswap V3 Pay attention:
		- remove liquidity
- [[2023-05-stella#[H-07] Pending position fees miscalculation may result in increased PnL|[H-07] Pending position fees miscalculation may result in increased PnL]]
	- Uniswap V3
- [[2023-05-stella#[H-08] “Exact output” swaps cannot be executed, blocking repayment of debt|[H-08] “Exact output” swaps cannot be executed, blocking repayment of debt]]
	- Uniswap V3
- [[2023-05-liquid_collective#[H-01] `_pickNextValidatorsToExitFromActiveOperators` uses the wrong index to query stopped validator|[H-01] `_pickNextValidatorsToExitFromActiveOperators` uses the wrong index to query stopped validator]]
	- Array Index
	- Track data flow across function calls
