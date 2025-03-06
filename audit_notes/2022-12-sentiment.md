# 2022-12-sentiment
---
- Category: #liquid_staking #CDP #services #yield_aggregator #rwa_lending
- Note Create 2025-03-06
- Platform: sherlock
- Report Url: [2022-12-sentiment](https://audits.sherlock.xyz/contests/28/report)
---
# Critical & High Risk Findings (xx)

---
# Medium Risk Findings (xx)

---
## [M-01] `getRewards()` can be triggered by external parties which will result in the rewards not be tracking properly by the system
----
- **Tags**: #business_logic #financial_bypass #access_control 
- Number of finders: 1
- Difficulty: Medium
---
### Summary

`ConvexRewardPool#getReward(address)` can be called by any address besides the owner themself.
### Detail

The reward tokens will only be added to the assets list when `getReward()` is called.

If there is a third party that is "helping" the `account` to call `getReward()` from time to time, by keeping the value of unclaimed rewards low, the account owner may not have the motivation to take the initiative to call `getReward()` via the `AccountManager`.

As a result, the reward tokens may never get added to the account's assets list.

## Impact

If the helper/attacker continuously claims the rewards on behalf of the victim, the rewards will not be accounted for in the victim's total assets.

As a result, the victim's account can be liquidated while actual there are enough assets in their account, it is just that these are not accounted for.
### Proof of Concept

[ConvexBoosterController.sol#L31-L46](https://github.com/sentimentxyz/controller/blob/507274a0803ceaa3cbbaf2a696e2458e18437b2f/src/convex/ConvexBoosterController.sol#L31-L46)
```solidity
    function canDeposit(bytes calldata data)
        internal
        view
        returns (bool, address[] memory, address[] memory)
    {
        (uint pid, ) = abi.decode(data, (uint, uint));
        (address lpToken, , address rewardPool, ,) = IBooster(BOOSTER).poolInfo(pid);

        address[] memory tokensIn = new address[](1);
        tokensIn[0] = rewardPool;

        address[] memory tokensOut = new address[](1);
        tokensOut[0] = lpToken;

        return (true, tokensIn, tokensOut);
    }
```
### Recommended Mitigation

Consider adding all the reward tokens to the account's assets list in `ConvexBoosterController.sol#canDeposit()`.

```solidity
    function canDeposit(bytes calldata data)
        internal
        view
        returns (bool, address[] memory, address[] memory)
    {
        (uint pid, ) = abi.decode(data, (uint, uint));
        (address lpToken, , address rewardPool, ,) = IBooster(BOOSTER).poolInfo(pid);

-       address[] memory tokensIn = new address[](1);
+       uint len = IRewardPool(rewardPool).rewardLength();

+       address[] memory tokensIn = new address[](len + 1);
        tokensIn[0] = rewardPool;

+       for(uint i = 1; i <= len; ++i) {
+           tokensIn[i] = IRewardPool(rewardPool).rewards(i - 1).reward_token;
+       }
+ 
        address[] memory tokensOut = new address[](1);
        tokensOut[0] = lpToken;

        return (true, tokensIn, tokensOut);
    }
```

### Discussion

### Notes & Impressions

#### Notes 
- A user deposits funds into a Convex pool through the system
- Rewards start accumulating but aren't yet counted in the user's official asset list
- A third party (either a well-meaning helper or an attacker) periodically calls `getReward(address)` for the user
- This claims the rewards but since it doesn't go through the `AccountManager`, these tokens never get added to the user's asset list
- From the system's perspective, these assets don't exist for collateral calculations
##### How the System Should Work

1. Alice's deposit begins earning rewards in CRV and CVX tokens
2. After a month, she's earned 500 CRV (worth $400) and 200 CVX (worth $300)
3. Alice goes to the platform's interface and clicks "Claim Rewards"
4. The system calls `getReward()` through the `AccountManager`
5. The rewards are claimed AND added to Alice's tracked assets
6. Alice's account now shows $10,700 worth of assets ($10,000 deposit + $700 rewards)

```
function canDeposit(bytes calldata data)
    internal
    view
    returns (bool, address[] memory, address[] memory)
{
    (uint pid, ) = abi.decode(data, (uint, uint));
    (address lpToken, , address rewardPool, ,) = IBooster(BOOSTER).poolInfo(pid);
    
    // Get the number of different reward tokens this pool offers
    uint len = IRewardPool(rewardPool).rewardLength();
    
    // Create an array large enough for all reward tokens plus the reward pool
    address[] memory tokensIn = new address[](len + 1);
    tokensIn[0] = rewardPool;
    
    // Add each potential reward token address to the tracking list
    for(uint i = 1; i <= len; ++i) {
        tokensIn[i] = IRewardPool(rewardPool).rewards(i - 1).reward_token;
    }
 
    address[] memory tokensOut = new address[](1);
    tokensOut[0] = lpToken;
    return (true, tokensIn, tokensOut);
}
```
##### How the Vulnerability Works

1. Alice deposits 10,000 USDC as before
2. Her deposit earns the same rewards: 500 CRV and 200 CVX
3. Bob (either maliciously or thinking he's helping) writes a script that calls `getReward(Alice's address)`
4. Because this call doesn't go through the `AccountManager`, the tokens are sent to Alice but NOT added to her tracked assets
5. Alice receives the reward tokens in her wallet but the system doesn't register them
6. Alice's account still only shows $10,000 worth of assets in the system
#### Impressions

When a financial protocol has functions that can be called directly (no access control) that handle value but don't properly update internal accounting systems, critical financial invariants can break.

### Tools

- [[Financial_Bypass]]
### Refine

- [[1-Business_Logic]]
- [[14-Accrss_Control]]
---
---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}