# 2023-08-Blueberry_Update
---
- Category: #rwa #leveraged_farming
- Note Create 2024-12-16
- Platform: sherlock
- Report Url: [2023-07-blueberry-judging](https://github.com/sherlock-audit/2023-07-blueberry-judging)
---
# High Risk Findings (xx)

---
## [H-2] CurveTricryptoOracle incorrectly assumes that WETH is always the last token in the pool which leads to bad LP pricing

----
- **Tags**:  #business_logic #oracle #configuration
- Number of finders: 2
- Difficulty: Easy
---

CurveTricryptoOracle assumes that WETH is always the last token in the pool (`tokens[2]`). This is incorrect for a majority of tricrypto pools and will lead to LP being highly overvalued.
### Vulnerability Detail

[CurveTricryptoOracle.sol#L53-L63](https://github.com/sherlock-audit/2023-07-blueberry/blob/main/blueberry-core/contracts/oracle/CurveTricryptoOracle.sol#L53-L63)

```solidity
    if (tokens.length == 3) {
        /// tokens[2] is WETH
        uint256 ethPrice = base.getPrice(tokens[2]);
        return
            (lpPrice(
                virtualPrice,
                base.getPrice(tokens[1]),
                ethPrice,
                base.getPrice(tokens[0])
            ) * 1e18) / ethPrice;
    }
```

When calculating LP prices, `CurveTricryptoOracle#getPrice` always assumes that WETH is the second token in the pool. This isn't the case which will cause the LP to be massively overvalued.

There are 6 tricrypto pools currently deployed on mainnet. Half of these pools have an asset other than WETH as token[2]:

```
    0x4ebdf703948ddcea3b11f675b4d1fba9d2414a14 - CRV
    0x5426178799ee0a0181a89b4f57efddfab49941ec - INV
    0x2889302a794da87fbf1d6db415c1492194663d13 - wstETH
```
### Impact

LP will be massively overvalued leading to overborrowing and protocol insolvency
### Recommended Mitigation

There is no need to assume that WETH is the last token. Simply pull the price for each asset and input it into lpPrice.

### Discussion

**IAm0x52**

Escalate

This is not a dupe of #105. This will cause a large number of tricrypto pools to be overvalued which presents a serious risk to the protocol.

**sherlock-admin2**

> Escalate
> 
> This is not a dupe of #105. This will cause a large number of tricrypto pools to be overvalued which presents a serious risk to the protocol.

You've created a valid escalation!

To remove the escalation from consideration: Delete your comment.

You may delete or edit your escalation comment anytime before the 48-hour escalation window closes. After that, the escalation becomes final.

**Shogoki**

Agree.  
This is not a duplicate of #105  
This can become its own main report and #20 is a duplicate of it.

There were some issues with (de)duplication. I would resolve like this.  
#98 is the duplicate with #20  
#105 is duplicate with #42

**hrishibhat**

Result:  
High  
Has duplicates  
This is a valid high issue based on the description

**sherlock-admin2**

Escalations have been resolved successfully!

Escalation status:

- [IAm0x52](https://github.com/sherlock-audit/2023-07-blueberry-judging/issues/98/#issuecomment-1694746548): accepted
### Notes

**Assumption vs. Reality**: The vulnerability stems from an incorrect business assumption - that WETH will always be in a specific position in the pool. This shows a misalignment between the protocol's internal logic and the actual structure of different crypto pools.
#### Impressions
- Never hardcode assumptions about token order in multi-token pools

### Refine

- [[1-Business_Logic]]

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