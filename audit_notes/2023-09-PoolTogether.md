# 2023-09-PoolTogether
---
- Category: #liquid_staking #Dexes #Bridge #CDP #yield 
- Note Create 2024-12-16
- Platform: code4rena
- Report Url: [2023-08-pooltogether](https://code4rena.com/reports/2023-08-pooltogether)
---
# High Risk Findings (xx)

---
## [H-01] Too many rewards are distributed when a draw is closed

----
- **Tags**: #wrong_math #business_logic 
- Number of finders: 1
- Difficulty: Hard
---
### Code Location

[RngRelayAuction.sol#L154-L157)](https://github.com/GenerationSoftware/pt-v5-draw-auction/blob/f1c6d14a1772d6609de1870f8713fb79977d51c1/src/RngRelayAuction.sol#L154-L157)
```solidity
    uint32 drawId = prizePool.closeDraw(_randomNumber);


    uint256 futureReserve = prizePool.reserve() + prizePool.reserveForOpenDraw();
    uint256[] memory _rewards = RewardLib.rewards(auctionResults, futureReserve);
```

[RngRelayAuction.sol#L178-L184](https://github.com/GenerationSoftware/pt-v5-draw-auction/blob/f1c6d14a1772d6609de1870f8713fb79977d51c1/src/RngRelayAuction.sol#L178-L184)
```solidity
  /// @notice Computes the actual rewards that will be distributed to the recipients using the current Prize Pool reserve.
  /// @param __auctionResults The auction results to use for calculation
  /// @return rewards The rewards that will be distributed
  function computeRewards(AuctionResult[] calldata __auctionResults) external returns (uint256[] memory) {
    uint256 totalReserve = prizePool.reserve() + prizePool.reserveForOpenDraw();
    return _computeRewards(__auctionResults, totalReserve);
  }
```

[PrizePool.sol#L366](https://github.com/GenerationSoftware/pt-v5-prize-pool/blob/26557afa439934afc080eca6165fe3ce5d4b63cd/src/PrizePool.sol#L366)
```solidity
    _nextDraw(_nextNumberOfTiers, uint96(_contributionsForDraw(lastClosedDrawId + 1)));
```

[TieredLiquidityDistributor.sol#L374](https://github.com/GenerationSoftware/pt-v5-prize-pool/blob/26557afa439934afc080eca6165fe3ce5d4b63cd/src/abstract/TieredLiquidityDistributor.sol#L374)
```solidity
    _reserve += newReserve;
```
### Impact

A relayer completes a prize pool draw by calling `rngComplete` in `RngRelayAuction.sol`. This method closes the prize pool draw with the relayed random number and distributes the rewards to the RNG auction recipient and the RNG relay auction recipient. These rewards are calculated based on a fraction of the prize pool reserve rather than an actual value.

However, the current reward calculation mistakenly includes an extra `reserveForOpenDraw` amount just after the draw has been closed. Therefore the fraction over which the rewards are being calculated includes tokens that have not been added to the reserve and will actually only be added to the reserve when the next draw is finalised. As a result, the reward recipients are rewarded too many tokens.
### Proof of Concept

Before deciding whether or not to relay an auction result, a bot can call `computeRewards` to calculate how many rewards they'll be getting based on the size of the reserve, the state of the auction and the reward fraction of the RNG auction recipient:

```solidity
  function computeRewards(AuctionResult[] calldata __auctionResults) external returns (uint256[] memory) {
    uint256 totalReserve = prizePool.reserve() + prizePool.reserveForOpenDraw();
    return _computeRewards(__auctionResults, totalReserve);
  }
```

Here, the total reserve is calculated as the sum of the current reserve and and amount of new tokens that will be added to the reserve once the currently open draw is closed. This method is correct and correctly calculates how many rewards should be distributed when a draw is closed.

A bot can choose to close the draw by calling `rngComplete` (via a relayer), at which point the rewards are calculated and distributed. Below is the interesting part of this method:

```solidity
    uint32 drawId = prizePool.closeDraw(_randomNumber);

    uint256 futureReserve = prizePool.reserve() + prizePool.reserveForOpenDraw();
    uint256[] memory _rewards = RewardLib.rewards(auctionResults, futureReserve);
```

As you can see, the draw is first closed and then the future reserve is used to calculate the rewards that should be distributed. However, when `closeDraw` is called on the pool, the `reserveForOpenDraw` for the previously open draw is added to the existing reserves. So `reserve()` is now equal to the `totalReserve` value in the earlier call to `computeRewards`. By including `reserveForOpenDraw()` when computing the actual reward to be distributed we've accidentally counted the tokens that are only going to be added in when the next draw is closed. So now the rewards distribution calculation includes the pending reserves for 2 draws rather than 1.

### Recommended Mitigation Steps

When distributing rewards in the call to `rngComplete`, the rewards should not be calculated with the new value of `reserveForOpenDraw` because the previous `reserveForOpenDraw` value has already been added to the reserves when `closeDraw` is called on the prize pool. Below is a suggested diff:

```bash
diff --git a/src/RngRelayAuction.sol b/src/RngRelayAuction.sol
index 8085169..cf3c210 100644
--- a/src/RngRelayAuction.sol
+++ b/src/RngRelayAuction.sol
@@ -153,8 +153,8 @@ contract RngRelayAuction is IRngAuctionRelayListener, IAuction {
 
     uint32 drawId = prizePool.closeDraw(_randomNumber);
 
-    uint256 futureReserve = prizePool.reserve() + prizePool.reserveForOpenDraw();
-    uint256[] memory _rewards = RewardLib.rewards(auctionResults, futureReserve);
+    uint256 reserve = prizePool.reserve();
+    uint256[] memory _rewards = RewardLib.rewards(auctionResults, reserve);
 
     emit RngSequenceCompleted(
       _sequenceId,

```

### Notes

#### Notes 
1. **Before Closing the Draw**    
```solidity
uint32 drawId = prizePool.closeDraw(_randomNumber);
```
   When `closeDraw()` is called, an important internal process happens:
 - The pending reserve (`reserveForOpenDraw`) is automatically added to the main reserve
 - This means `prizePool.reserve()` now includes the tokens that were previously in `reserveForOpenDraw()`

2.  **Immediately After `closeDraw()`**
```solidity
uint256 futureReserve = prizePool.reserve() + prizePool.reserveForOpenDraw();
```
   By adding `reserveForOpenDraw()` again, you're now double-counting those tokens:	
- The tokens are already in `prizePool.reserve()`
- You're adding them again with `+ prizePool.reserveForOpenDraw()`

Imagine your bank account:

- You have $100 in your account
- Someone promises to deposit $50 soon
- When that $50 arrives, your balance becomes $150

In the original contract logic, it's like saying:

- You have $150 (the $100 + $50 promised)
- Then you add the $50 again, making it look like you have $200
#### Impressions

*It is pretty hard to spot this problem.*

- Critical operation
	- close market
	- close draw
- State Variables Mapping before and after critical operation.

### Refine
- [[1-Business_Logic]]
- [[3-Wrong_Math]]
---

---

# Medium Risk Findings (xx)

---

{{Copy from Medium Risk Finding Template.md}}

---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}