42 findings

## Example:

1. [[2023-01-popcorn#[H-09] Attacker can steal 99% of total balance from any reward token in any Staking contract|[H-09] Attacker can steal 99% of total balance from any reward token in any Staking contract]]
	- I think the core of this finding is that we should check whether crucial parameters have limits(such as rate, speed, ratio,)
2. [[2022-11-isomorph#[H-07] User can steal rewards from other users by withdrawing their Velo Deposit NFTs from other users' depositors|[H-07] User can steal rewards from other users by withdrawing their Velo Deposit NFTs from other users' depositors]]
	1. Missing authentication checks
	2. Check `DepositReceipt`  same?
3.  [[2022-12-sentiment#[M-01] `getRewards()` can be triggered by external parties which will result in the rewards not be tracking properly by the system|[M-01] `getRewards()` can be triggered by external parties which will result in the rewards not be tracking properly by the system]]
	1. #financial_bypass 
	2. When a financial protocol has functions that can be called directly (no access control) that handle value but don't properly update internal accounting systems, critical financial invariants can break.
