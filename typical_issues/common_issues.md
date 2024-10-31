# Typical Common Issues in Smart Contract Audits

---

## [01] Precision Loss

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

- [[2024-01-canto#M-01] secRewardsPerShare Insufficient precision](https //github.com/code-423n4/2024-01-canto-findings/issues/12)|secRewardsPerShare Insufficient precision]]

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

## [02] Batch Average Pricing Conflicts with Market Status (One-size-fits-all(一刀切))

### Problem pattern:

- In specific market states (such as when the market is closed), the batch pricing mechanism causes conflicts of interest among users.
- Creates user incentives contrary to the protocol's goals.
### Common scenarios:

- Using batch processing mechanism
- Uniform price within batches (interest rate / exchange rate, etc.).
- There is market state transition (such as open -> closed).
### Real Cases

- [[2024-08-wildact#M-01] Users are incentivized to not withdraw immediately after the market is closed](https //github.com/code-423n4/2024-08-wildcat-findings/issues/121)|[M-01] Users are incentivized to not withdraw immediately after the market is closed]]

### Audit Key Points:

1. Check Points
	- Does there exist batch processing + average pricing mechanism
	- Does the market have state transitions?
	- When there is a state transition, will the pricing mechanism within batches lead to misaligned user incentives?

This essence of this issue is the inapplicability of the batch processing "one-size-fits-all(一刀切)" mechanism in specific market conditions. During audits, special attention must be paid to the interaction logic between batch processing and market states.

---
## [03] Integer Overflow

### Problem pattern:

- Using smaller uint types (`uint128`) for intermediate calculations that could overflow
- Multiplication results being constrained to the same size as inputs
### Common scenarios:

- Token streaming contracts with rate-based calculations
- Contracts handling high-precision or large number caculations
### Typical Code:

```solidity
// Vulnerable pattern
uint128 ratePerSecond;  // Could be set to very high value
uint128 elapsedTime;    // Time difference
uint128 scaledDebt = elapsedTime * ratePerSecond;  // Can overflow

// Safe pattern
uint256 ratePerSecond;  // or keep as uint128
uint256 elapsedTime;    // or keep as uint128
uint256 scaledDebt = uint256(elapsedTime) * uint256(ratePerSecond);  // Safe multiplication
```

### Real Cases

- [[2024-10-sablier_flow#[H-01] Sender can brick stream by forcing overflow in debt calculation|[H-01] Sender can brick stream by forcing overflow in debt calculation]]

### Audit Key Points:

1. Identification Points
	- Look for multiplication operations using fixed-size integers
	- Review mathematical operations where inputs are user-controlled
	- Identify critical functions that can't be reversed/recovered if they fail
	- Look for missing overflow checks in financial calculations
2. Check Points
	- Verify integer size aer appropriate for all possible calculation results.
	- Ensure overflow protection exists for all mathematical operations.
	- Verify recovery mechanisms exist for critical operations.
	- Test edge cases with maximum possible values

---

