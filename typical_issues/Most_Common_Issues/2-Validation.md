
123 findings util 2024-12-13

 1. [[2022-12-liquid-collective#[C-3] `OperatorsRegistry._getNextValidatorsFromActiveOperators` can DOS Alluvial staking if there's an operator with `funded==stopped` and `funded == min(limit, keys)`|[C-3] `OperatorsRegistry._getNextValidatorsFromActiveOperators` can DOS Alluvial staking if there's an operator with `funded==stopped` and `funded == min(limit, keys)`]]
	1. *Mathematical equivalence doesn't mean functional equivalence.*
2. [[2022-12-connext#[H-01] `swapInternal()` shouldn't use `msg.sender`|[H-01] `swapInternal()` shouldn't use `msg.sender`]]
	1. `replyer A ---> BridgeFacet.execute() - msg.sender = A ---> BridgeFacet._handleExecuteLiquidity() - msg.sender = A ---> AssetLogic.swapFromLocalAssetIfNeeded() - msg.sender = A ---> AssetLogic._swapAsset() - msg.sender = A ---> SwapUtils.swapInternal msg.sender = A`
	2. Checks relayer's balance instead of pool's balance
3. [[2022-11-stakehouse#[M-28] Funds are not claimed from syndicate for valid BLS keys of first key is invalid (no longer part of syndicate).|[M-28] Funds are not claimed from syndicate for valid BLS keys of first key is invalid (no longer part of syndicate).]]
	1. The Single Point of Failure Anti-Pattern
		This issue exemplifies a broader principle in smart contract design: **avoid making the execution of critical business logic dependent on a single validation check that isn't directly related to that logic**.