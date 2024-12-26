# 2023-05-blueberry
---
- Category: #Lending #leveraged_farming #options_vault
- Note Create 2024-12-26
- Platform: sherlock
- Report Url: [2023-05-blueberry](https://audits.sherlock.xyz/contests/77/report)
---
# High Risk Findings (xx)

---

{{Copy from High Risk Finding Template.md}}

---

# Medium Risk Findings (xx)

---
## [M-03] Updating the `feeManager` on config will cause `desync` between bank and vaults
----
- **Tags**: #business_logic #configuration 
- Number of finders: 1
- Difficulty: Easy
---
### Summary

When the `bank` is initialized it caches the current `config.feeManager`. This is problematic since `feeManger` can be updated in `config`. Since it is pre-cached the address in bank will not be updated leading to a `desync` between contracts the always pull the freshest value for `feeManger` and `bank`.
### Detail

```solidity
    feeManager = config_.feeManager();
```

Above we see that `feeManger` is cached during initialization.

```solidity
    withdrawAmount = config.feeManager().doCutVaultWithdrawFee(
        address(uToken),
        shareAmount
    );
```

This is in direct conflict with other contracts the always use the freshest value. This is problematic for a few reasons. The `desync` will lead to inconsistent fees across the ecosystem either charging users too many fees or not enough.
### Impact

After update users will experience inconsistent fees across the ecosystem

### Recommended Mitigation

BlueBerryBank should always use config.feeManger instead of caching it.

### Discussion

### Notes & Impressions

#### Notes 
- desynchronization -> pre-cache state variable (eg.address)

### Tools
### Refine
- [[1-Business_Logic]]

---

---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}