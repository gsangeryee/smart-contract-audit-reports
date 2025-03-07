# 2022-11-Rage Trade
---
- Category: #Dexes #CDP #yield #services #staking_pool 
- Note Create 2025-03-07
- Platform: sherlock
- Report Url: [2022-11-Rage Trade](https://audits.sherlock.xyz/contests/16/report)
---
# Critical & High Risk Findings (xx)

---
## [H-02] `DnGmxJuniorVaultManager._rebalanceBorrow` logic is flawed and could result in vault liquidation
----
- **Tags**: #business_logic 
- Number of finders: 2
- Difficulty: Medium
---
### Summary

`DnGmxJuniorVaultManager._rebalanceBorrow` fails to rebalance correctly if only one of the two assets needs a rebalance. In the case where one assets increases rapidly in price while the other stays constant, the vault may be liquidated.
### Detail

```solidity
    // If both eth and btc swap amounts are not beyond the threshold then no flashloan needs to be executed | case 1
    if (btcAssetAmount == 0 && ethAssetAmount == 0) return;

    if (repayDebtBtc && repayDebtEth) {
        // case where both the token assets are USDC
        // only one entry required which is combined asset amount for both tokens
        assets = new address[](1);
        amounts = new uint256[](1);

        assets[0] = address(state.usdc);
        amounts[0] = (btcAssetAmount + ethAssetAmount);
    } else if (btcAssetAmount == 0 || ethAssetAmount == 0) {
        // Exactly one would be true since case-1 excluded (both false) | case-2
        // One token amount = 0 and other token amount > 0
        // only one entry required for the non-zero amount token
        assets = new address[](1);
        amounts = new uint256[](1);

        if (btcAssetAmount == 0) {
            assets[0] = (repayDebtBtc ? address(state.usdc) : address(state.wbtc));
            amounts[0] = btcAssetAmount;
        } else {
            assets[0] = (repayDebtEth ? address(state.usdc) : address(state.weth));
            amounts[0] = ethAssetAmount;
        }
```

The logic above is used to determine what assets to borrow using the flashloan. If the rebalance amount is under a threshold then the `assetAmount` is set equal to zero. The first check `if (btcAssetAmount == 0 && ethAssetAmount == 0) return;` is a short circuit that returns if neither asset is above the threshold. The third check `else if (btcAssetAmount == 0 || ethAssetAmount == 0)` is the point of interest. Since we short circuit if both are zero then to meet this condition exactly one asset needs to be rebalanced. The logic that follows is where the error is. In the comments it indicates that it needs to enter with the non-zero amount token but the actual logic reflects the opposite. If `btcAssetAmount == 0` it actually tries to enter with wBTC which would be the zero amount asset.

The result of this can be catastrophic for the vault. If one token increases in value rapidly while the other is constant the vault will only ever try to rebalance the one token but because of this logical error it will never actually complete the rebalance. If the token increase in value enough the vault would actually end up becoming liquidated.
### Impact

Vault is unable to rebalance correctly if only one asset needs to be rebalanced, which can lead to the vault being liquidated
### Recommended Mitigation

Small change to reverse the logic and make it correct:

```solidity
-       if (btcAssetAmount == 0) {
+       if (btcAssetAmount != 0) {
            assets[0] = (repayDebtBtc ? address(state.usdc) : address(state.wbtc));
            amounts[0] = btcAssetAmount;
        } else {
            assets[0] = (repayDebtEth ? address(state.usdc) : address(state.weth));
            amounts[0] = ethAssetAmount;
        }
```

### Discussion

### Notes

#### Initial State:

- The vault holds 1 BTC and 15 ETH
- The target ratio is 50% BTC value and 50% ETH value
- Everything is balanced
#### Market Movement:

- BTC price doubles suddenly
- ETH price stays the same
- Now the portfolio is imbalanced: ~67% BTC value, ~33% ETH value
#### Rebalancing Needed:

- The system detects that rebalancing is required
- Only ETH needs adjustment (we need more ETH to restore balance)
- The system calculates `btcAssetAmount = 0` (no BTC adjustment needed)
- The system calculates `ethAssetAmount = X` (a positive value representing how much ETH we need)
#### The Bug Kicks In:

1. The code enters the `else if (btcAssetAmount == 0 || ethAssetAmount == 0)` branch
2. Since `btcAssetAmount == 0`, it enters the first condition
3. Instead of working with ETH (the asset that needs rebalancing), it attempts to work with BTC
4. It sets up a flash loan with `assets[0] = address(state.wbtc)` (borrowing BTC)
5. But sets `amounts[0] = btcAssetAmount` which equals zero

*This is a total logic error.*
**Principle**: Verify that conditional logic correctly aligns actions with intended outcomes across all possible input scenarios, especially in multi-variable systems.
### Tools
### Refine

- [[1-Business_Logic]]

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