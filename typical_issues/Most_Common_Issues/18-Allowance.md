# Allowance

Allowance vulnerability arises when a user grants excessive spending permissions to a third-party address, potentially allowing unauthorized access to their tokens and enabling malicious actions. Allowances are necessary in Ethereum to enable certain functionalities like decentralized exchanges or lending platforms, where smart contracts need limited access to a user's tokens for specific operations, but if not properly managed, it can lead to security risks.

15 findings

## Example

1.  [[2023-01-UXD#[H-01] `PerpDespository reblance` and `rebalanceLite` can be called to drain funds from anyone who has approved `PerpDepository`|[H-01] `PerpDespository reblance` and `rebalanceLite` can be called to drain funds from anyone who has approved `PerpDepository`]]
	1. **The victim pays the shortfall**: 
	2. **The victim’s allowance is drained**:  
    