47 findings util 2025-01-08

Don't update state refers to a guideline that advises against modifying the contract's state or storage within certain functions, as doing so may lead to unintended consequences for users and other contracts interacting with it.
## Examples
1.  [[2023-02-astaria#[H-03] `VaultImplementation.buyoutLien` does not update the new public vault's parameters and does not transfer assets between the vault and the borrower]]
2. [[2023-01-ajna#[M-11] Settled collateral of a borrower aren't available for lenders until borrower's debt is fully cleared]]
	- 1. Key warning signs:
			- Single-condition state updates (`if (x == 0)` rather than handling all cases)
			- Asset transfers without corresponding state updates
			- Functions that handle partial operations without proper cleanup
			- Discrepancies between accounting systems (e.g., user balances vs. pool balances)
3. [[2022-11-stakehouse#[M-21] EIP1559 rewards received by syndicate during the period when it has no registered knots can be lost|[M-21] EIP1559 rewards received by syndicate during the period when it has no registered knots can be lost]]
	1. **Always handle all possible states of your system, especially edge cases like "zero" or "empty" states**.