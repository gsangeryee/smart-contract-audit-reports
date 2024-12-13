
225 findings till 2024-12-13

*Business Logic - Logic vulnerabilities involve flaws in the business logic or protocols of a smart contract, where the implementation matches the developer's intention, but the underlying logic is inherently flawed.*

- The technical implementation matches the developer's intent
- The underlying logic can be strategically manipulated.
- The code does exactly what it was programmed to do.
- The vulnerability emerges from how the rules interact, not from a coding mistake.
## List of cases

- [[2023-08-immutable-securityreview#[M-05] Withdrawal queue can be forcibly activated to hinder bridge operation|Withdrawal queue can be forcibly activated to hinder bridge operation]]
	- Withdraw queue mechanism -> Denial-of-Service
- [[2023-07-Primitive-Spearbit-Security-Review#[M-01] `getSpotPrice, approximateReservesGivenPrice, getStartegyData` ignore time to maturity|[M-01] `getSpotPrice, approximateReservesGivenPrice, getStartegyData` ignore time to maturity]]
	- time-based-logic
- [[2023-08-Moonwell_Finance-Compound_Vault_Security_Assessment#[M-02] Incorrect Use of Borrow Cap Instead of Supply Cap In `maxmint` function|[M-02] Incorrect Use of Borrow Cap Instead of Supply Cap In `maxmint` function]]
	- `max mint <= supply cap - totalSupply < borrowCap - totalBorrow`
- [[2023-08-Blueberry_Update#[H-2] CurveTricryptoOracle incorrectly assumes that WETH is always the last token in the pool which leads to bad LP pricing|[H-2] CurveTricryptoOracle incorrectly assumes that WETH is always the last token in the pool which leads to bad LP pricing]]
	- Never hardcode assumptions about token order in multi-token pools
- [[2023-09-PoolTogether#[H-01] Too many rewards are distributed when a draw is closed|[H-01] Too many rewards are distributed when a draw is closed]]
	- Critical operation
		- close market
		- close draw
	- [[State_Transition_Maps]]
- [[2023-08-Smoothly#[H-02] Operator can still claim rewards after being removed from governance|[H-02] Operator can still claim rewards after being removed from governance]]
	- `delte-` or `close` --> **right** and **money**
- [[2023-07-Meta#[M-01] `MetaManager.unclaimedRewards` should work with shares instead of asset amounts.|[M-01] `MetaManager.unclaimedRewards` should work with shares instead of asset amounts.]]
	- amount ≠ share 
- [[2023-06-Dinari#[M-01] In case of stock split and reverse split, the Dshare token holder will gain or loss his Dshare token value|[M-01] In case of stock split and reverse split, the Dshare token holder will gain or loss his Dshare token value]]
	- When smart contracts are associated with the real economy (stock, reserve, futures), it is necessary to consider the features and risks of the real economy.
- [[2023-07-nounsdao#[M-02] If DAO updates `forkEscrow` before `forkThreshold` is reached, the user's escrowed Nounns will be lost]]
	- Hard
	- Contract Change, Where is tokens?, who can withdraw?
- [[2023-07-nounsdao#[M-03] `NounsDAOV3Proposals.cancel()` should allow to cancel the proposal of the Expired state|[M-03] `NounsDAOV3Proposals.cancel()` should allow to cancel the proposal of the Expired state]]
	- Using [[State_Transition_Maps]]
- [[2023-07-Baton_Launchpad#[H-01] Protocol fees from NFT mints can't be claimed in `BatonLaunchpad`|[H-01] Protocol fees from NFT mints can't be claimed in `BatonLaunchpad`]]
	- can `receive` fee, can not `withdraw` fee
	- similar a piggy bank
	- simply and serious problem