
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
	- State Variables Mapping before and after critical operation.
- [[2023-08-Smoothly#[H-02] Operator can still claim rewards after being removed from governance|[H-02] Operator can still claim rewards after being removed from governance]]
	- `delte-` or `close` --> **right** and **money**
- [[2023-07-Meta#[M-01] `MetaManager.unclaimedRewards` should work with shares instead of asset amounts.|[M-01] `MetaManager.unclaimedRewards` should work with shares instead of asset amounts.]]
	- amount ≠ share 