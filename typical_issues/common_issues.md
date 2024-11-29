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

## [04] State Transition Synchronization

### Problem pattern:

- Incomplete update of system parameters during critical status changes
- Failure to synchronize interdependent states
- Inconsistent propagation of status change implications
### Common scenarios:

- Market closure with unresolved time-locks
- Withdrawal batches with unupdated rate calculations
- Administrative state changes that don't fully reset system constraints
- Time-based restrictions that persist after triggering events
### Typical Code:

```solidity
function closeMarket() external {
    // Vulnerable implementation
    marketState = CLOSED;
    // Missing: 
    // - Clear time locks
    // - Update withdrawal rates
    // - Synchronize all dependent states
}

function executeWithdrawal() external {
    // Potential synchronization issue
    require(marketState == OPEN, "Market closed");
    // Missing context of how closed state affects withdrawal
    calculateWithdrawalRate(); // May use stale calculations
}
```

### Real Cases
- [[2024-08-wildact#[M-06] No lender is able to exit even after the market is closed]]
- [[2024-08-wildact#[H-01] User could withdraw more than supposed to, forcing last user withdraw to fail]]]
### Audit Key Points:

1. Identification Points
	- Identify administrative status change mechanisms
	- Locate time-based or conditional state variables
	- Find complex interactions between system components
1. Check Points
	- Verify all state variables are updated during status changes
	- Ensure time-locks are properly cleared or adjusted
	- Check calculation methods for rate-sensitive operations
	- Validate that user actions are consistently handled across all states
	- Confirm no residual constraints exist after state transition
	- Test edge cases of status changes with partial user interactions

---
## [05] Inconsistent Validation in Critical Functionality

### Problem pattern:

- Inconsistent implementation of critical validation checks across similar functions in related contracts.

### Common scenarios:

- A function in one contract includes an essential validation (e.g., verifying caller permissions), while a similar function in another contract omits it.
- This inconsistency allows unauthorized access or unintended behavior when interacting with the unprotected function.

### Typical Code:

```solidity
// Function with validation
function onQueueWithdrawal(
  address lender,
  uint32 /* expiry */,
  uint /* scaledAmount */,
  MarketState calldata /* state */,
  bytes calldata hooksData
) external override {
  HookedMarket memory market = _hookedMarkets[msg.sender];
  if (!market.isHooked) revert NotHookedMarket();
  // Additional logic
}

// Function without validation
function onQueueWithdrawal(
  address lender,
  uint32 /* expiry */,
  uint /* scaledAmount */,
  MarketState calldata /* state */,
  bytes calldata hooksData
) external override {
  LenderStatus memory status = _lenderStatus[lender];
  if (!isKnownLenderOnMarket[lender][msg.sender] && !_tryValidateAccess(status, lender, hooksData)) {
    revert NotApprovedLender();
  }
}
```

### Real Cases

- [[2024-08-wildact#[M-08] `AccessControlHooks` `onQueueWithdrawal()` does not check if market is hooked which could lead to unexpected errors such as temporary DoS]]

### Audit Key Points:

1. **Identification Points**:
    - Compare similar functions across related contracts to spot missing or inconsistent validations.
    - Identify roles or permissions (e.g., "hooked market") that should consistently be enforced.
    
2. **Check Points**:
    - Verify if all critical functions validate the caller's role or permissions as expected.
    - Test the impact of omitting the validation, especially for scenarios involving external input or credential verification.