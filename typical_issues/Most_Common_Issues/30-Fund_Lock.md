# Fund Lock

Fund Lock refers to a scenario where funds become inaccessible or locked within a smart contract due to improper handling of withdrawal or transfer functions

1. Incomplete Token Transfers, Remaining Tokens Stay in contract
	- [[2022-10-lifi#[M-9] What if the receiver of Axelar `_executeWithToken()` doesn’t claim all tokens]]
2. Update escrow address, but incorrect token transfers
	- [[2023-07-nounsdao#[M-02] If DAO updates `forkEscrow` before `forkThreshold` is reached, the user's escrowed Nounns will be lost]]
3. Early withdrawals when the market is closed.
	- [[2024-08-wildact#[H-01] User could withdraw more than supposed to, forcing last user withdraw to fail]]