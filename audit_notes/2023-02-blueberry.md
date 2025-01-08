# 2023-02-blueberry
---
- Category: #leveraged_farming #Dexes #CDP #yield #cross-chain 
- Note Create 2025-01-08
- Platform: Sherlock
- Report Url: [2023-02-blueberry](https://audits.sherlock.xyz/contests/41/report)
---
# High Risk Findings (xx)

---
## [H-07] Users can be liquidated prematurely because calculation understates value of underlying position
----
- **Tags**:  #liquidation #business_logic 
- Number of finders: 1
- Difficulty: 
---
### Summary

When the value of the underlying asset is calculated in `getPositionRisk()`, it uses the `underlyingAmount`, which is the amount of tokens initially deposited, without any adjustment for the interest earned. This can result in users being liquidated early, because the system undervalues their assets.
### Detail

A position is considered liquidatable if it meets the following criteria:

```solidity
((borrowsValue - collateralValue) / underlyingValue) >= underlyingLiqThreshold
```

The value of the underlying tokens is a major factor in this calculation. However, the calculation of the underlying value is performed with the following function call:

```solidity
uint256 cv = oracle.getUnderlyingValue(
    pos.underlyingToken,
    pos.underlyingAmount //@audit This only reflects initial deposit!
);
```

If we trace it back, we can see that `pos.underlyingAmount` is set when `lend()` is called (ie when underlying assets are deposited). This is the only place in the code where this value is moved upward, and it is only increased by the amount deposited. It is never moved up to account for the **interest payments** made on the deposit, which can materially change the value.
### Impact

Users can be liquidated prematurely because the value of their underlying assets are calculated incorrectly.
### Code Snippet

[BlueBerryBank.sol#L485-L488](https://github.com/sherlock-audit/2023-02-blueberry/blob/0828dd2afbc1fd0feb137c78048a445d9cf0eabe/contracts/BlueBerryBank.sol#L485-L488)
```solidity
        uint256 cv = oracle.getUnderlyingValue(
            pos.underlyingToken,
            pos.underlyingAmount 
        );
```

[CoreOracle.sol#L182-L189](https://github.com/sherlock-audit/2023-02-blueberry/blob/0828dd2afbc1fd0feb137c78048a445d9cf0eabe/contracts/oracle/CoreOracle.sol#L182-L189)
```solidity
    function getUnderlyingValue(address token, uint256 amount)
        external
        view
        returns (uint256 collateralValue)
    {
        uint256 decimals = IERC20MetadataUpgradeable(token).decimals();
        collateralValue = (_getPrice(token) * amount) / 10**decimals;
    }
```

[BlueBerryBank.sol#L644](https://github.com/sherlock-audit/2023-02-blueberry/blob/0828dd2afbc1fd0feb137c78048a445d9cf0eabe/contracts/BlueBerryBank.sol#L644)
```solidity
        pos.underlyingAmount += amount;
```
### Recommended Mitigation

Value of the underlying assets should be derived from the vault shares and value, rather than being stored directly.
### Discussion

### Notes

#### Example
- Initial deposit: 100 USDC
- After 6 months: Actually worth 105 USDC due to interest
- Borrowed amount: 80 USDC
- Collateral value: 90 USDC
- Liquidation threshold: 20%

Using actual value (105 USDC):
```solidity
((80 - 90) / 105) = -0.095 (Position is healthy)
```

Using stored value (100 USDC):
```solidity
((80 - 90) / 100) = -0.10 (Position appears riskier than it really is)
```

#### Impressions
When calculating, check the variables involved in the calculations: 
* Check if the definitions are correct. 
* Check for any changes.

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