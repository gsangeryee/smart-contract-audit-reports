# 2023-05-dodo-judging
---
- Category: chose from [[protocol_categories]]
- Note Create 2024-12-26
- Platform: sherlock
- Report Url: [2023-05-dodo-judging](https://audits.sherlock.xyz/contests/78/report)
---
# High Risk Findings (xx)

---

{{Copy from High Risk Finding Template.md}}

---

# Medium Risk Findings (xx)

---
## [M-01] `MarginTrading.sol` the whole balance and not just the traded funds are deposited into Aave when a trade is opened
----
- **Tags**: #Aave #business_logic 
- Number of finders: 1
- Difficulty: Hard
---
### Summary
It's expected by the protocol that funds can be in the `MarginTrading` contract without being deposited into Aave as margin.

We can see this by looking at the `MarginTradingFactory.depositMarginTradingETH` and `MarginTradingFactory.depositMarginTradingERC20` functions.

If the user sets `margin=false` as the parameter, the funds are only sent to the `MarginTrading` contract but NOT deposited into Aave.

[MarginTradingFactory.sol#L203-L211](https://github.com/sherlock-audit/2023-05-dodo/blob/930565dd875dac24609441423c7c76c2ae4719a8/dodo-margin-trading-contracts/contracts/marginTrading/MarginTradingFactory.sol#L203-L211)
```solidity
    function depositMarginTradingETH(
	    address _marginTradingAddress, 
	    bool _margin, 
	    uint8 _flag
	) public payable {
        require(IMarginTrading(_marginTradingAddress).user() == msg.sender, "factory:caller is not the user");
        WETH.deposit{value: msg.value}();
        WETH.transfer(_marginTradingAddress, msg.value);
        if (_margin) {
            IMarginTrading(_marginTradingAddress).lendingPoolDeposit(address(WETH), msg.value, _flag);
        }
        emit DepositMarginTradingETH(_marginTradingAddress, msg.value, _margin, _flag);
    }
```

[MarginTradingFactory.sol#L259-L272](https://github.com/sherlock-audit/2023-05-dodo/blob/930565dd875dac24609441423c7c76c2ae4719a8/dodo-margin-trading-contracts/contracts/marginTrading/MarginTradingFactory.sol#L259-L272)
```solidity
    function _depositMarginTradingERC20(
        address _marginTradingAddress,
        address _marginAddress,
        uint256 _marginAmount,
        bool _margin,
        uint8 _flag
    ) internal {
        require(IMarginTrading(_marginTradingAddress).user() == msg.sender, "factory:caller is not the user");
        DODOApprove.claimTokens(_marginAddress, msg.sender, _marginTradingAddress, _marginAmount);
        if (_margin) {
            IMarginTrading(_marginTradingAddress).lendingPoolDeposit(_marginAddress, _marginAmount, _flag);
        }
        emit DepositMarginTradingERC20(_marginTradingAddress, _marginAddress, _marginAmount, _margin, _flag);
    }
```

So clearly there is the expectation for funds to be in the `MarginTrading` contract that should not be deposited into Aave.

This becomes an issue when a trade is opened.

### Vulnerability Detail

Let's look at the `MarginTrading._openTrade` function that is called when a trade is opened:

[MarginTrading.sol#L257-L279](https://github.com/sherlock-audit/2023-05-dodo/blob/930565dd875dac24609441423c7c76c2ae4719a8/dodo-margin-trading-contracts/contracts/marginTrading/MarginTrading.sol#L257-L279)
```solidity
    function _opentrade(
        address _swapAddress,
        address _swapApproveTarget,
        address[] memory _swapApproveToken,
        bytes memory _swapParams,
        address[] memory _tradeAssets
    ) internal {
        if (_swapParams.length > 0) {
            // approve to swap route
            for (uint256 i = 0; i < _swapApproveToken.length; i++) {
                IERC20(_swapApproveToken[i]).approve(_swapApproveTarget, type(uint256).max);
            }


            (bool success,) = _swapAddress.call(_swapParams);
            require(success, "dodoswap fail");
        }
        uint256[] memory _tradeAmounts = new uint256[](_tradeAssets.length);
        for (uint256 i = 0; i < _tradeAssets.length; i++) {
            _tradeAmounts[i] = IERC20(_tradeAssets[i]).balanceOf(address(this));
            _lendingPoolDeposit(_tradeAssets[i], _tradeAmounts[i], 1);
        }
        emit OpenPosition(_swapAddress, _swapApproveToken, _tradeAssets, _tradeAmounts);
    }
```

The whole balance of the token will be deposited into Aave:

```solidity
_tradeAmounts[i] = IERC20(_tradeAssets[i]).balanceOf(address(this)); 
_lendingPoolDeposit(_tradeAssets[i], _tradeAmounts[i], 1); 
```

Not just those funds that have been acquired by the swap. This means that funds that should stay in the `MarginTrading` contract might also be deposited as margin.
### Impact

When opening a trade funds can be deposited into Aave unintentionally. Thereby the funds act as margin and the trade can incur a larger loss than expected.
### Recommended Mitigation

It is necessary to differentiate the funds that are acquired by the swap and those funds that were there before and should stay in the contract:

```solidity
diff --git a/dodo-margin-trading-contracts/contracts/marginTrading/MarginTrading.sol b/dodo-margin-trading-contracts/contracts/marginTrading/MarginTrading.sol
index f68c1f3..42f96cf 100644
--- a/dodo-margin-trading-contracts/contracts/marginTrading/MarginTrading.sol
+++ b/dodo-margin-trading-contracts/contracts/marginTrading/MarginTrading.sol
@@ -261,6 +261,10 @@ contract MarginTrading is OwnableUpgradeable, IMarginTrading, IFlashLoanReceiver
         bytes memory _swapParams,
         address[] memory _tradeAssets
     ) internal {
+        int256[] memory _amountsBefore = new uint256[](_tradeAssets.length);
+        for (uint256 i = 0; i < _tradeAssets.length; i++) {
+            _amountsBefore[i] = IERC20(_tradeAssets[i]).balanceOf(address(this));
+        }
         if (_swapParams.length > 0) {
             // approve to swap route
             for (uint256 i = 0; i < _swapApproveToken.length; i++) {
@@ -272,8 +276,10 @@ contract MarginTrading is OwnableUpgradeable, IMarginTrading, IFlashLoanReceiver
         }
         uint256[] memory _tradeAmounts = new uint256[](_tradeAssets.length);
         for (uint256 i = 0; i < _tradeAssets.length; i++) {
-            _tradeAmounts[i] = IERC20(_tradeAssets[i]).balanceOf(address(this));
-            _lendingPoolDeposit(_tradeAssets[i], _tradeAmounts[i], 1);
+            if (_amountsBefore[i] < IERC20(_tradeAssets[i]).balanceOf(address(this))) {
+                _tradeAmounts[i] = IERC20(_tradeAssets[i]).balanceOf(address(this)) - _amountsBefore[i];
+                _lendingPoolDeposit(_tradeAssets[i], _tradeAmounts[i], 1);
+            }
         }
         emit OpenPosition(_swapAddress, _swapApproveToken, _tradeAssets, _tradeAmounts);
     }
```

If funds that were in the contract prior to the swap should be deposited there is the separate `MarginTrading.lendingPoolDeposit` function to achieve this.
### Discussion

**Zack995**

In terms of product design, users do not have a separate concept of balance. However, the contract is designed to be more flexible and allows for balances to be maintained. Users will not perceive or interact with balances in terms of user experience or operations.

**roguereddwarf**

Based on the smart contract logic there is clearly the notion of balance that is not intended to be used as collateral (but e.g. used to repay a loan).  
If this notion of a separate balance is not exposed on the front-end this is not a sufficient mitigation of the issue since the issue is clearly present in the smart contract.

**securitygrid**

Escalate for 10 USDC  
This is valid low/info as stated by the sponsor. No bad impact.

**sherlock-admin**

> Escalate for 10 USDC  
> This is valid low/info as stated by the sponsor. No bad impact.

You've created a valid escalation for 10 USDC!

To remove the escalation from consideration: Delete your comment.

You may delete or edit your escalation comment anytime before the 48-hour escalation window closes. After that, the escalation becomes final.

**ctf-sec**

can consider #80 duplicate of this one

**hrishibhat**

Result:  
Medium  
Has duplicates  
Considering this issue as valid medium based on the above comments from smart contract perspective and enforcing in the front end is not a mitigation as mentioned above.
### Notes & Impressions

#### Notes 
- A user deposits 100 USDC with margin=false, meaning they want to keep it in the contract
- They then open a trade that swaps some ETH for 50 USDC
- When the trade executes, the contract will deposit all 150 USDC into Aave, including the 100 USDC that was supposed to stay in the contract

#### Impressions
- Pay Attention to special boolean parameter: `_margin`

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