# Typical Common Issues in Smart Contract Audits

---

## Precision Loss

### Problem pattern:

The problem of loss of precision usually occurs when performing division operations. Since Solidity does not support floating-point numbers, all division operations will be rounded down. When the dividend is less than the divisor, the result will be truncated to `0`, resulting in distorted calculation results.
### Common scenarios:

1. Reward Calculation
	- Token reward distribution
	- Liquidity yield calculation
	- Staking reward distribution
2. Share Calculation
	- LP token
	- Share ratio calculation
	- Voting weight calculation
3. Price Calculation
	- Token price conversion
	- Transaction slippage calculation
	- Fee calculation
### Typical Code:

Issue code:

```solidity
// Low-precision calculation
uint256 reward = (amount * rate) / total;

// Unsafe price calculation
uint256 price = (tokenAmount * basePrice) / denomination;

// Share calculation prone to loss of precision
uint256 shares = (depositAmount * totalShares) / totalDeposits;
```

Repair mode:
```solidity
// Use higher precision
uint256 reward = (amount * rate * PRECISION) / total;

// Safe price calculation
uint256 price = (tokenAmount * basePrice * PRICE_PRECISION) / denomination;

// Safe share calculation
uint256 shares = (depositAmount * totalShares * SHARE_PRECISION) / totalDeposits;

// Common precision definition
uint256 constant PRECISION = 1e18;
uint256 constant PRICE_PRECISION = 1e30;
uint256 constant SHARE_PRECISION = 1e27;
```
### Real Cases

- [[2024-05-canto-findings#M-01] secRewardsPerShare Insufficient precision](https //github.com/code-423n4/2024-01-canto-findings/issues/12)|secRewardsPerShare Insufficient precision]]

### Audit Key Points:

1. Identification Points
	- Check all mathematical operations involving division
	- Pay special attention to the calculation of token quantity, price and share.
	- Look for calculations that may produce decimal results.
	- Pay attention to the conversion between tokens of different precisions.
	- Check the calculation logic related to reward distribution.
2. Check Points
	1. Precision matching check
		- Confirm the precision (decimals) of all tokens.
		- Verify whether intermediate calculation steps maintain sufficient precision.
		- Check whether the precision of the final result is suitable for business need.
	2. Numerical range check
		- Ensure that multiplication does not overflow.
		- Verify that division does not cause serious loss of precision.
		- Check if protection against division by zero is needed.
	3. Business Logic check
### The key points to remember are:
- Always be aware of the potential loss of precision caused by division operations.
- Consider appropriate precision when designing
- Avoid loss of precision by increasing the precision of intermediate calculations.
- Pay special attention to all calculation logics involving division during auditing.

---