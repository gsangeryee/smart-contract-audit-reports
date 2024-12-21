105 findings util 2024-12-13

## Definition
*Wrong Math refers to a potential issue where mathematical operations within a smart contract are implemented incorrectly, leading to inaccurate calculations.*
## List of cases
- [[2023-08-moonwell_finance-compound_vault_security_assessment#[M-02] Incorrect Use of Borrow Cap Instead of Supply Cap In `maxmint` function|[M-02] Incorrect Use of Borrow Cap Instead of Supply Cap In `maxmint` function]]
	- `max mint <= supply cap - totalSupply < borrowCap - totalBorrow`
- [[2023-09-pooltogether#[H-01] Too many rewards are distributed when a draw is closed|[H-01] Too many rewards are distributed when a draw is closed]]
	- Critical operation
		- close market
		- close draw
	- State Variables Mapping before and after critical operation.
