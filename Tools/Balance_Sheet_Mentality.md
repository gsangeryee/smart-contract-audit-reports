# Balance Sheet Mentality: Applying Accounting Principles

## Concept
This strategy involves applying basic accounting principles at the smart contract level. Think of each smart contract as having its own mini "balance sheet." The core idea is that for every transaction involving value, the total amount of assets entering the contract must equal the total amount of assets leaving the contract, plus any change in the contract's internal balances.

## How to Implement

- **Track Inflows and Outflows:** For each function that handles value (deposits, withdrawals, transfers, etc.), identify the assets being received and the assets being sent.
- **Monitor Internal Balances:** Keep track of the contract's internal balances for various assets. How do these balances change after each transaction?
- **Focus on Transfer Functions:** Pay close attention to transfer, transferFrom, safeTransfer, and similar functions, as these are the primary mechanisms for value movement.
- **Use Events for Tracking:** Leverage event logs to reconstruct the history of value transfers and balance changes.
- **Consider Different Asset Types Separately:** Maintain separate "balance sheets" for each type of token or asset managed by the contract.

## Practical Example

Consider a simple token vault contract:

- **Inflows:** `deposit()` function where users send tokens to the vault.
- **Outflows:** `withdraw()` function where users retrieve their tokens.
- **Internal Balance:** The total amount of tokens held by the vault.

Applying a balance sheet mentality, you would verify:

- That the amount of tokens deposited correctly increases the vault's internal balance.
- That the amount of tokens withdrawn correctly decreases the vault's internal balance.
- That there are no functions or scenarios where tokens can be added to or removed from the vault without a corresponding deposit or withdrawal.

## Example
- [[2023-04-blueberry#[H-01] Attackers will keep stealing the `rewards` from Convex SPELL]]