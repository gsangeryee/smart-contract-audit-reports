# 2023-04-blueberry
---
- Category: #Lending #leveraged_farming #options_vault 
- Note Create 2024-12-27
- Platform: sherlock
- Report Url: [2023-04-blueberry](https://audits.sherlock.xyz/contests/69/report)
---
# High Risk Findings (xx)

---
## [H-01] Attackers will keep stealing the `rewards` from Convex SPELL
----
- **Tags**:  #Deposit_or_Reward_tokens #Coding-Bug #business_logic #PCPvsSCP 
- Number of finders: 2
- Difficulty: Medium
---
### Summary

On [WConvexPools.burn()](https://github.com/sherlock-audit/2023-04-blueberry/blob/main/blueberry-core/contracts/wrapper/WConvexPools.sol#L201-L235) transfer [CRV + CVX + the extra rewards](https://docs.convexfinance.com/convexfinance/general-information/why-convex/convex-for-liquidity-providers) to Convex SPELL
### Detail

But [ConvexSpell.openPositionFarm()](https://github.com/sherlock-audit/2023-04-blueberry/blob/main/blueberry-core/contracts/spell/ConvexSpell.sol#L67-L138) only refund CVX to the user.  
So the rest rewards will stay in the SPELL intel if someone (could be an attacker) invokes `_doRefund()` within `closePositionFarm()` with the same address tokens
### Impact

- Convex SPELL steals the user rewards
- the protocol will lose some fees
- attackers will keep stealing the rewards from Convex SPELL
### Proof of Concept

`WConvexPools.burn()` transfer CRV + CVX + the extra rewards

[WConvexPools.sol#L201-L235](https://github.com/sherlock-audit/2023-04-blueberry/blob/main/blueberry-core/contracts/wrapper/WConvexPools.sol#L201-L235)
```solidity
	// Transfer LP Tokens
	IERC20Upgradeable(lpToken).safeTransfer(msg.sender, amount);

	// Transfer Reward Tokens
	(rewardTokens, rewards) = pendingRewards(id, amount);

	for (uint i = 0; i < rewardTokens.length; i++) {
		IERC20Upgradeable(rewardTokens[i]).safeTransfer(
			msg.sender,
			rewards[i]
		);
	}
```

only refund CVX to the user

[ConvexSpell.sol#LL127C1-L138C10](https://github.com/sherlock-audit/2023-04-blueberry/blob/96eb1829571dc46e1a387985bd56989702c5e1dc/blueberry-core/contracts/spell/ConvexSpell.sol#LL127C1-L138C10)
```solidity
	// 6. Take out existing collateral and burn
	IBank.Position memory pos = bank.getCurrentPositionInfo();
	if (pos.collateralSize > 0) {
		(uint256 pid, ) = wConvexPools.decodeId(pos.collId);
		if (param.farmingPoolId != pid)
			revert Errors.INCORRECT_PID(param.farmingPoolId);
		if (pos.collToken != address(wConvexPools))
			revert Errors.INCORRECT_COLTOKEN(pos.collToken);
		bank.takeCollateral(pos.collateralSize);
		wConvexPools.burn(pos.collId, pos.collateralSize);
		_doRefundRewards(CVX); //@audit-info Only refunds CVX tokens
	}
```
### Recommended Mitigation

you should Refund all Rewards (CRV + CVX + the extra rewards)

### Discussion
**Ch-301**

> Escalate for 10 USDC

> Convex docs are confirming this point

```
Convex allows liquidity providers to earn trading fees and claim boosted CRV without locking CRV themselves. Liquidity providers can receive boosted CRV and liquidity mining rewards with minimal effort:
Earn claimable CRV with a high boost without locking any CRV
Earn CVX rewards
Zero deposit and withdraw fees
Zero fees on extra incentive tokens (SNX, etc)
```

>and [WConvexPools.burn()](https://github.com/sherlock-audit/2023-04-blueberry/blob/main/blueberry-core/contracts/wrapper/WConvexPools.sol#L201-L235) handle this properly

>so Convex SPELL should refund all the rewards
### Notes

#### Notes 
- `WConvexPools.burn()` transfer CRV + CVX + the extra rewards 
- only refund CVX to the user

#### Impressions
- [[logical_issues#[01] PCP vs SCP]]

### Tools
- [[Map_Value_Transfers]]
- [[Source_and_Sink_Analysis]]
- [[Balance_Sheet_Mentality]]
### Refine
- [[1-Business_Logic]]

---
# Medium Risk Findings (xx)

---
## [M-05] `getPositionRisk()` will return a wrong value of risk
----
- **Tags**: #liquidation #external_contract #external_call #configuration #business_logic #simple_issue_hard_to_detect 
- Number of finders: 1
- Difficulty: Hard
---
### Summary

In order to interact with SPELL the users need to `lend()` some collateral which is known as **Isolated Collateral** and the SoftVault will deposit them into Compound protocol to generate some lending interest (to earn passive yield)

### Detail

to [liquidate](https://github.com/sherlock-audit/2023-04-blueberry/blob/main/blueberry-core/contracts/BlueBerryBank.sol#L487-L548) a position this function `isLiquidatable()` should return `true`

```solidity
    function isLiquidatable(uint256 positionId) public view returns (bool) {
        return
            getPositionRisk(positionId) >=
            banks[positions[positionId].underlyingToken].liqThreshold;
    }
```

and it is subcall to `getPositionRisk()`

```solidity
    function getPositionRisk(
        uint256 positionId
    ) public view returns (uint256 risk) {
        uint256 pv = getPositionValue(positionId);          
        uint256 ov = getDebtValue(positionId);             
        uint256 cv = getIsolatedCollateralValue(positionId);

        if (
            (cv == 0 && pv == 0 && ov == 0) || pv >= ov // Closed position or Overcollateralized position
        ) {
            risk = 0;
        } else if (cv == 0) {
            // Sth bad happened to isolated underlying token
            risk = Constants.DENOMINATOR;
        } else {
            risk = ((ov - pv) * Constants.DENOMINATOR) / cv;
        }
    }
```

as we can see the `cv` is a critical value in terms of the calculation of `risk` the `cv` is returned by `getIsolatedCollateralValue()`

```solidity
    function getIsolatedCollateralValue(
        uint256 positionId
    ) public view override returns (uint256 icollValue) {
        Position memory pos = positions[positionId];
        // NOTE: exchangeRateStored has 18 decimals.
        uint256 underlyingAmount;
        if (_isSoftVault(pos.underlyingToken)) {
            underlyingAmount =                                              
                (ICErc20(banks[pos.debtToken].bToken).exchangeRateStored() * 
                    pos.underlyingVaultShare) /
                Constants.PRICE_PRECISION; 
        } else {
            underlyingAmount = pos.underlyingVaultShare;
        }
        icollValue = oracle.getTokenValue(
            pos.underlyingToken,
            underlyingAmount
        );
    }
```

and it uses `exchangeRateStored()` to ask Compound (CToken.sol) for the exchange rate  
[from CToken contract](https://github.com/compound-finance/compound-protocol/blob/master/contracts/CToken.sol#LL281C18-L281C18)

```solidity
This function does not accrue interest before calculating the exchange rate
```

so the `getPositionRisk()` will return a wrong value of risk because the interest does not accrue for this position
### Impact

the user (position) could get liquidated even if his position is still healthy
### Proof of Concept

[CToken.sol#LL270C1-L286C6](https://github.com/compound-finance/compound-protocol/blob/master/contracts/CToken.sol#LL270C1-L286C6)

```solidity
    /**
     * @notice Accrue interest then return the up-to-date exchange rate
     * @return Calculated exchange rate scaled by 1e18
     */
    function exchangeRateCurrent() override public nonReentrant returns (uint) {
        accrueInterest();
        return exchangeRateStored();
    }

    /**
     * @notice Calculates the exchange rate from the underlying to the CToken
     * @dev This function does not accrue interest before calculating the exchange rate
     * @return Calculated exchange rate scaled by 1e18
     */
    function exchangeRateStored() override public view returns (uint) {
        return exchangeRateStoredInternal();
    }
```
### Recommended Mitigation

You should use `exchangeRateCurrent()` to Accrue interest first.
### Discussion

**Gornutz**

Since we are using a view function we are unable to use `exchangeRateCurrent()` we have to use `exchangeRateStored()`

**Ch-301**

Escalate for 10 USDC

The sponsor confirms that. so the user could get liquidated even in case his position is still healthy.  
I believe the rules are clear on that  
He decided to not fix it but the risk still exists
### Notes & Impressions

#### Notes 

They needed to use a vie function to check the position's risk. The ideal function `exchangeRateCurrent()` modifies state by accruing interest, so it can't be used in a view function like `getPositionRisk()`.

So, they decided to not fix it but the risk still exists.

#### Impressions

No, this issue is not easy to detect. Looking at the tags in the report, it's marked as having only 1 finder and a "Hard" difficulty level. This makes sense because finding it requires:

1. Deep understanding of Compound's exchange rate mechanics
2. Knowledge that `exchangeRateStored()` and `exchangeRateCurrent()` behave differently
3. Ability to trace how inaccurate exchange rates impact liquidation risk calculations

This kind of issue is especially challenging because it requires understanding both protocol-specific logic and external protocol (Compound) implementation details.

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