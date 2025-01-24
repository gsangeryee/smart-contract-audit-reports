105 findings util 2024-12-13

## Definition
*Wrong Math refers to a potential issue where mathematical operations within a smart contract are implemented incorrectly, leading to inaccurate calculations.*
## List of cases
1. [[2023-08-moonwell_finance-compound_vault_security_assessment#[M-02] Incorrect Use of Borrow Cap Instead of Supply Cap In `maxmint` function|[M-02] Incorrect Use of Borrow Cap Instead of Supply Cap In `maxmint` function]]
	- `max mint <= supply cap - totalSupply < borrowCap - totalBorrow`
2. [[2023-09-pooltogether#[H-01] Too many rewards are distributed when a draw is closed|[H-01] Too many rewards are distributed when a draw is closed]]
	- Critical operation
		- close market
		- close draw
	- State Variables Mapping before and after critical operation.
3. [[2023-02-astaria#[H-20] `commitToLiens` transfers extra assets to the borrower when protocol fee is present|[H-20] `commitToLiens` transfers extra assets to the borrower when protocol fee is present]]
	- We should repeatedly verify whether the financial calculations(such as interest and fees) are correctly implemented in the code during future audit tasks.
4. [[2023-01-ajna#[M-04] Incorrect MOMP calculation in neutral price calculation|[M-04] Incorrect MOMP calculation in neutral price calculation]]
	- Error Type: Part for Whole
5. [[2023-01-UXD#[M-06] Inaccurate Perp debt calculation|[M-06] Inaccurate Perp debt calculation]]
	1. *Double-check the complex calculation*