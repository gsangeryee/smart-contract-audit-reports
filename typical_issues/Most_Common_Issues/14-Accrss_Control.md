42 findings

## Example:

1. [[2023-01-popcorn#[H-09] Attacker can steal 99% of total balance from any reward token in any Staking contract|[H-09] Attacker can steal 99% of total balance from any reward token in any Staking contract]]
	- I think the core of this finding is that we should check whether crucial parameters have limits(such as rate, speed, ratio,)
2. [[2022-11-isomorph#[H-07] User can steal rewards from other users by withdrawing their Velo Deposit NFTs from other users' depositors|[H-07] User can steal rewards from other users by withdrawing their Velo Deposit NFTs from other users' depositors]]
	1. Missing authentication checks
	2. Check `DepositReceipt`  same?