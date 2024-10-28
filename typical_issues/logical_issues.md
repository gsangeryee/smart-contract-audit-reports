# Typical Logical Issues in Smart Contract Audits

---
## Interval calculation boundary alignment

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

- [[2024-01-canto-findings#[ [H-02 ] update_market() nextEpoch calculation incorrect](https //github.com/code-423n4/2024-01-canto-findings/issues/10)|update_market() nextEpoch calculation incorrect]]

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
