
# 2023-08-Moonwell_Finance-Compound_Vault_Security_Assessment
---
- Category: chose from [[protocol_categories]]
- Note Create 2024-12-16
- Platform: [Halborn](https://www.halborn.com/)
- Report Url: [Moonwell_Finance_Compound_Vault_Smart_Contract_Security_Assessment_Report_Halborn_Final](https://github.com/HalbornSecurity/PublicReports/blob/master/Solidity%20Smart%20Contract%20Audits/Moonwell_Finance_Compound_Vault_Smart_Contract_Security_Assessment_Report_Halborn_Final.pdf)
---
# High Risk Findings (xx)

---

{{Copy from High Risk Finding Template.md}}

---

# Medium Risk Findings (xx)

---
## [M-02] Incorrect Use of Borrow Cap Instead of Supply Cap In `maxmint` function

----
- **Tags**: #wrong_math #business_logic 
- Number of finders: nnn
- Difficulty: Medium
---
### Description: 
The `maxMint` function is currently designed to use the `borrowCap` for determining the maximum amount that can be minted, which is inconsistent with the expected behavior. Ideally, the function should be using the `supplyCap` to calculate this limit. This inconsistency could lead to incorrect calculations and potential imbalances in the system.

### Code Location:

[CompoundERC4626.sol#L159](https://github.com/moonwell-fi/moonwell-contracts-v2/blob/6c4ea1e30c89632f9e0ad5c3b9dd3a505a101854/src/4626/CompoundERC4626.sol#L159)

```solidity
    function maxMint(address) public view override returns (uint256) {
        if (comptroller.mintGuardianPaused(address(mToken))) {
            return 0;
        }

        uint256 borrowCap = comptroller.borrowCaps(address(mToken));
        if (borrowCap != 0) {
            uint256 totalBorrows = mToken.totalBorrows();
            return borrowCap - totalBorrows;
        }

        return type(uint256).max;
    }
```

### Recommendation: 
Replace the use of `borrowCap` with `supplyCap` in the `maxMint` function to ensure accurate calculations for the maximum `mintable` amount. 

### Remediation Plan: 
SOLVED: The Moonwell Finance team solved the issue by changing `borrowCap` with `supplyCap`.

```solidity
    function maxMint(address) public view override returns (uint256) {
        if (comptroller.mintGuardianPaused(address(mToken))) {
            return 0;
        }

        uint256 supplyCap = comptroller.supplyCaps(address(mToken));
        if (supplyCap != 0) {
            uint256 currentExchangeRate = mToken.viewExchangeRate();
            uint256 totalSupply = MToken(address(mToken)).totalSupply();
            uint256 totalSupplies = (totalSupply * currentExchangeRate) / 1e18; /// exchange rate is scaled up by 1e18, so needs to be divided off to get accurate total supply
    
            // uint256 totalCash = MToken(address(mToken)).getCash();
            // uint256 totalBorrows = MToken(address(mToken)).totalBorrows();
            // uint256 totalReserves = MToken(address(mToken)).totalReserves();

            // // (Pseudocode) totalSupplies = totalCash + totalBorrows - totalReserves
            // uint256 totalSupplies = (totalCash + totalBorrows) - totalReserves;

            // supply cap is      3
            // total supplies is  1
            /// no room for additional supplies

            // supply cap is      3
            // total supplies is  0
            /// room for 1 additional supplies

            // supply cap is      4
            // total supplies is  1
            /// room for 1 additional supplies

            /// total supplies could exceed supply cap as interest accrues, need to handle this edge case
            /// going to subtract 2 from supply cap to account for rounding errors
            if (totalSupplies + 2 >= supplyCap) {
                return 0;
            }

            return supplyCap - totalSupplies - 2;
        }

        return type(uint256).max;
    }
```
### Notes & Impressions

**Notes**
- Over-minting
- **Borrow caps** control borrowing
- **Supply caps** control token creation (minting)

**Incorrect Calculation**:

- Borrow Cap: 1,000,000 tokens
- Total Borrows: 600,000 tokens
- Calculated Mintable: 400,000 tokens ❌

**Correct Calculation**:

- Supply Cap: 500,000 tokens
- Current Total Supply: 400,000 tokens
- Actually Mintable: 100,000 tokens ✅

*So, roughly speaking: `max mint <= supply cap - totalSupply < borrowCap - totalBorrow`*

### Refine

- [[1-Business_Logic]]
- [[3-Wrong_Math]]

---

---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}