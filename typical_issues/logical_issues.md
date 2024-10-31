# Typical Logical Issues in Smart Contract Audits

---
## [01] PCP vs SCP

### Problem pattern:

- Inconsistency between Process Control Points (Business requirements) and System Control Points (Code implementation)
- Critical business logic requirements are not properly reflected in the actual code implementation
- State transition boundaries in smart contracts are not correctly captured in code
- Discrepancy between documentation (`@natspec`, `comments`) and actual code behavior
### Common scenarios:

- Epoch / period transitions where different rules should apply
- Token reward rate changes at specific block numbers
- Protocol parameter updates at predetermined thresholds
- Vesting schedule transitions
- Staking / unstaking period boundaries
- Governance proposal phase transitions
- Function modifiers missing or incorrectly applied
- Input validation requirements not properly implemented
### Typical Code:

```solidity
// Typical code
```

### Real Cases

- [[2024-01-canto#[ [H-02 ] update_market() nextEpoch calculation incorrect](https //github.com/code-423n4/2024-01-canto-findings/issues/10)|2024-01-canto#[ [H-02 ] update_market() nextEpoch calculation incorrect]]
- [[2024-10-sablier_flow#[H-01] Sender can brick stream by forcing overflow in debt calculation]]

### Audit Key Points:

1. Identification Points
	- Look for time-based or block-based state transitions
	- Identify critical business rules that depend on boundaries or thresholds
	- Review documentation for special cases at transition points
	- Check for requirements involving different rules at different periods
	- Analyze state-changing functions that should behave differently at boundaries
	- Compare `@natspec` documentation with actual implementation
2. Check Points
	- Verify boundary conditions are explicitly handled in code
	- Ensure transition logic matches business requirements exactly
	- Check for off-by-one errors in boundary calculations
	- Validate edge cases at state transitions
	- Test boundary scenarios with specific values
	- Compare whitepaper / documentation requirements with actual implementation
	- Review all state-changing functions for correct boundary handling
	- Verify epoch / period calculations account for exact transition points
	- Ensure modifiers are consistently applied across similar functions
	- Test function behavior with edge cases (e.g., non-existent IDs)
	- Verify `@natspec` promises are fulfilled by the implementation

---
## [02] Interval calculation boundary alignment

### Problem pattern:

- When calculations need to be performed according to a fixed interval (epoch, time period, batch, etc).
- The calculation process crosses the interval boundary.
- The code does not correctly align to the interval boundary.
### Common scenarios:

- Block reward calculation.
- Interest rate calculation (calculating interest by period).
- Lookup unlocking (in batches).
- Vote weight statistics (by period).
### Typical Code

```solidity
// Wrong: Offset by one interval from the current position 
nextPoint = currentPoint + INTERVAL;

// Correct: Align to the interval boundary 
currentInterval = (currentPoint / INTERVAL) * INTERVAL; 
nextPoint = currentInterval + INTERVAL;
```

The essence of such problem is that the calculation is not anchored to the reference point designed by the system, but instead, a certain point in the process is wrongly used as the reference.

### Real Cases

- [[2024-01-canto#[ [H-02 ] update_market() nextEpoch calculation incorrect](https //github.com/code-423n4/2024-01-canto-findings/issues/10)|update_market() nextEpoch calculation incorrect]]

### Audit Key Points:

1. Identification Points
	- Code involving interval calculations
	- Scenarios of cumulative calculations
	- Time/Block-related calculations
2. Check Points
	- Whether interval boundaries are correctly aligned
	- Whether the calculation reference point is correct
	- Whether boundary conditions are handled

---

