# 2022-10-inverse
---
- Category: #liquid_staking #CDP #services #Synthetics 
- Note Create 2025-03-14
- Platform: code4rena
- Report Url: [2022-10-inverse](https://code4rena.com/reports/2022-10-inverse)
---
# Critical & High Risk Findings (xx)

---

{{Copy from High Risk Finding Template.md}}

---

# Medium Risk Findings (xx)

---
## [M-06] User can free from liquidation fee if its escrow balance is less than the calculated liquidation fee
----
- **Tags**: #business_logic #partilly_payback 
- Number of finders: 5
- Difficulty: Medium
---
### Detail

User can free from liquidation fee if its escrow balance less than the calculated liquidation fee.
### Proof of Concept

If the `liquidationFeeBps` is enabled, the `gov` should receive the liquidation fee. But if user's escrow balance is less than the calculated liquidation fee, `gov` got nothing.

```solidity
	if(liquidationFeeBps > 0) {
		uint liquidationFee = repaidDebt * 1 ether / price * liquidationFeeBps / 10000;
		if(escrow.balance() >= liquidationFee) {
			escrow.pay(gov, liquidationFee);
		}
	}
```
### Recommended Mitigation

User should pay all the remaining escrow balance if the calculated liquidation fee is greater than its escrow balance.

```
        if(liquidationFeeBps > 0) {
            uint liquidationFee = repaidDebt * 1 ether / price * liquidationFeeBps / 10000;
            if(escrow.balance() >= liquidationFee) {
                escrow.pay(gov, liquidationFee);
            } else {
                escrow.pay(gov, escrow.balance());
            }
        }
```

### Discussion

**0xean (judge) commented:**

> This should amount to dust.

**08xmt (Inverse) confirmed and commented:**

> Fixed in 

```solidity
	if(liquidationFeeBps > 0) {
		uint liquidationFee = repaidDebt * 1 ether / price * liquidationFeeBps / 10000;
+       uint balance = escrow.balance();
+       if(balance >= liquidationFee) {
-		if(escrow.balance() >= liquidationFee) {
			escrow.pay(gov, liquidationFee);
+       } else if(balance > 0) {   
+           escrow.pay(gov, balance);
-		} else {
-			escrow.pay(gov, escrow.balance());
		}
	}
```

### Notes & Impressions

#### Notes 
The problem occurs in the fee collection logic. The code only transfers the fee if the user's escrow balance is sufficient to cover the entire calculated fee. If the balance is less than the fee, the contract simply skips the fee payment entirely.

This creates a loophole where users could intentionally maintain a low escrow balance to avoid paying liquidation fees completely, even if they have some balance that could partially cover the fee.
#### Impressions

- Always handle partial payment scenarios in fee collection mechanisms.
- Consider what happens when a user has insufficient funds to cover the full fee amount. (partial payment)

### Tools
### Refine

- [[1-Business_Logic]]

---
## [M-12] Users could get some DOLA even if they are on liquidation position
----
- **Tags**: #business_logic 
- Number of finders: 1
- Difficulty: Hard
---
### Impact

Users ables to invoke `forceReplenish()` when they are on liquidation position
### Proof of Concept

On `Market.sol` ==> `forceReplenish()` On this line

```solidity
uint collateralValue = getCollateralValueInternal(user);
```

`getCollateralValueInternal(user)` only return the value of the collateral

```solidity
    function getCollateralValueInternal(address user) internal returns (uint) {
        IEscrow escrow = predictEscrow(user);
        uint collateralBalance = escrow.balance();
        return collateralBalance * oracle.getPrice(address(collateral), collateralFactorBps) / 1 ether; 
```

So if the user have `1.5 wETH` at the price of `1 ETH = 1600 USD` It will return `1.5 * 1600` and this value is the real value we can’t just check it directly with the debt like this

```solidity
 require(collateralValue >= debts[user], "Exceeded collateral value");
```

This is no longer `over collateralized` protocol The value needs to be multiplied by `collateralFactorBps / 10000`

- So depending on the value of `collateralFactorBps` and `liquidationFactorBps` the user could be in the liquidation position but he is able to invoke `forceReplenish()` to cover all their `dueTokensAccrued[user]` on `DBR.sol` and get more `DOLA`
- or it will lead a healthy debt to be in the liquidation position after invoking `forceReplenish()`
### Recommended Mitigation

Use `getCreditLimitInternal()` rather than `getCollateralValueInternal()`.

### Discussion

### Notes & Impressions

#### Notes 
- collateral factors
- Always use risk-adjusted valuations for credit decisions, not raw asset values.

### Tools
### Refine

- [[1-Business_Logic]]
---
## [M-16] Calling repay function sends less DOLA to Market contract when `forceReplenish` function is not called while it could be called
----
- **Tags**: #business_logic 
- Number of finders: 8
- Difficulty: Medium
---
### Impact

When a user incurs a DBR deficit, a replenisher can call the `forceReplenish` function to force the user to replenish DBR. However, there is no guarantee that the `forceReplenish` function will always be called. When the `forceReplenish` function is not called, such as because that the replenisher does not notice the user's DBR deficit promptly, the user can just call the `repay` function to repay the original debt and the `withdraw` function to receive all of the deposited collateral even when the user has a DBR deficit already. Yet, in the same situation, if the `forceReplenish` function has been called, more debt should be added for the user, and the user needs to repay more in order to get back all of the deposited collateral. Hence, when the `forceReplenish` function is not called while it could be called, the `Market` contract would receive less DOLA if the user decides to repay the debt and withdraw the collateral both in full.

`forceReplenish`
```solidity
    function forceReplenish(address user, uint amount) public {
        uint deficit = dbr.deficitOf(user);
        require(deficit > 0, "No DBR deficit");
        require(deficit >= amount, "Amount > deficit");
        uint replenishmentCost = amount * dbr.replenishmentPriceBps() / 10000;
        uint replenisherReward = replenishmentCost * replenishmentIncentiveBps / 10000;
        debts[user] += replenishmentCost;
        uint collateralValue = getCollateralValueInternal(user);
        require(collateralValue >= debts[user], "Exceeded collateral value");
        totalDebt += replenishmentCost;
        dbr.onForceReplenish(user, amount);
        dola.transfer(msg.sender, replenisherReward);
        emit ForceReplenish(user, msg.sender, amount, replenishmentCost, replenisherReward);
    }
```

`repay`
```solidity
    function repay(address user, uint amount) public {
        uint debt = debts[user];
        require(debt >= amount, "Insufficient debt");
        debts[user] -= amount;
        totalDebt -= amount;
        dbr.onRepay(user, amount);
        dola.transferFrom(msg.sender, address(this), amount);
        emit Repay(user, msg.sender, amount);
    }
```

`withdraw`
```solidity
    function withdraw(uint amount) public {
        withdrawInternal(msg.sender, msg.sender, amount);
    }
```

`withdrawInternal`
```solidity
    function withdrawInternal(address from, address to, uint amount) internal {
        uint limit = getWithdrawalLimitInternal(from);
        require(limit >= amount, "Insufficient withdrawal limit");
        IEscrow escrow = getEscrow(from);
        escrow.pay(to, amount);
        emit Withdraw(from, to, amount);
    }
```
### Proof of Concept

Please add the following test in `src\test\Market.t.sol`. This test will pass to demonstrate the described scenario.

```solidity
    function testRepayAndWithdrawInFullWhenIncurringDBRDeficitIfNotBeingForcedToReplenish() public {
        gibWeth(user, wethTestAmount);
        gibDBR(user, wethTestAmount);
        vm.startPrank(user);
        // user deposits wethTestAmount WETH and borrows wethTestAmount DOLA
        deposit(wethTestAmount);
        market.borrow(wethTestAmount);
        assertEq(DOLA.balanceOf(user), wethTestAmount);
        assertEq(WETH.balanceOf(user), 0);
        vm.warp(block.timestamp + 60 weeks);
        // after some time, user incurs DBR deficit
        assertGt(dbr.deficitOf(user), 0);
        // yet, since no one notices that user has a DBR deficit and forces user to replenish DBR,
        //   user is able to repay wethTestAmount DOLA that was borrowed previously and withdraw wethTestAmount WETH that was deposited previously
        market.repay(user, wethTestAmount);
        market.withdraw(wethTestAmount);
        vm.stopPrank();
        // as a result, user is able to get back all of the deposited WETH, which should not be possible if user has been forced to replenish DBR
        assertEq(DOLA.balanceOf(user), 0);
        assertEq(WETH.balanceOf(user), wethTestAmount);
    }
```
### Recommended Mitigation

When calling the `repay` function, the user's DBR deficit can also be checked. If the user has a DBR deficit, an amount, which is similar to `replenishmentCost` that is calculated in the `forceReplenish` function, can be calculated; it can then be used to adjust the `repay` function's `amount` input for updating the states regarding the user's and total debts in the relevant contracts.

### Discussion

### Notes & Impressions

#### DBR (Dola Borrowing Rights)

DBR is a core component of the FiRM protocol's borrowing mechanism. It works like this:

One DBR token gives a user the right to borrow one DOLA stablecoin for one year. This creates a time-based borrowing rights system rather than the traditional interest rate model used by many lending protocols.

Path 1 (Expected behavior):
```
1. Alice has 1,000 DOLA debt and 100 DBR deficit
2. Replenisher calls forceReplenish(alice, 100)
3. Alice's debt increases to 1,050 DOLA
4. Alice must repay 1,050 DOLA to withdraw her 1 ETH
5. Protocol receives 1,050 DOLA (minus 5 DOLA reward)
```

Path 2 (Vulnerability):
```
1. Alice has 1,000 DOLA debt and 100 DBR deficit
2. Alice quickly calls repay(alice, 1000)
3. Alice then calls withdraw(1 ETH)
4. Alice's debt is cleared, she gets back her 1 ETH
5. Protocol only receives 1,000 DOLA
```
#### Impressions

**Ensure consistency across all paths that modify user positions**. In particular:
1. Any condition that should affect a user's debt or position must be checked in all relevant functions that modify that position.
2. Users shouldn't be able to evade penalties or additional costs by timing their actions to avoid certain mechanisms.
3. Protocol mechanisms like penalties or additional costs should be applied automatically rather than relying on external actors to trigger them.
4. When designing a protocol with multiple ways to modify a user's position, ensure that all paths lead to consistent economic outcomes.
### Tools
### Refine

- [[1-Business_Logic]]

---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}