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
- [[2024-08-wildact#[M-02] [`FixedTermLoanHooks` allow Borrower to update Annual Interest before end of the "Fixed Term Period"]|FixedTermLoanHooks` allow Borrower to update Annual Interest before end of the "Fixed Term Period"]]

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
## [03] Consistency Issues

### Problem pattern:
- Multiple functions handling the same business logic but with inconsistent implementations
- Inconsistency in state management across similar operations
- Lack of role-based access control for functionally equivalent operations
- Different execution paths leading to different results for the same business operation
- Code duplication with variations in critical business logic

### Common scenarios:
- Multiple repayment functions with different state management patterns
- Deposit/withdrawal functions implemented differently across the protocol
- Reward distribution functions with inconsistent calculation methods
- Price update mechanisms varying across different parts of the protocol
- State transition logic implemented differently for similar operations
- Multiple entry points for the same operation without standardization

### Typical Code:

```solidity
contract InconsistentImplementation {
    // Pattern 1: Transfer first, then update state
    function operation1() external {
        asset.transferFrom(msg.sender, address(this), amount);
        State memory state = getLatestState();
        // Update state...
    }
    
    // Pattern 2: Update state first, then transfer
    function operation2() external {
        State memory state = getLatestState();
        // Update state...
        asset.transferFrom(msg.sender, address(this), amount);
    }
}

// Better Implementation
contract ConsistentImplementation {
    // Unified internal logic
    function _handleOperation(uint256 amount) internal {
        // Standardized operation flow
    }
    
    // Different entry points but consistent internal logic
    function operation1() external onlyRole1 {
        _handleOperation(amount);
    }
    
    function operation2() external onlyRole2 {
        _handleOperation(amount);
    }
}
```

### Real Cases

- [[2024-08-wildact#[M-03] Inconsistency across multiple repaying functions causing lender to pay extra fees]]

### Audit Key Points:
1. Identification Points
    - Look for multiple functions with similar names or purposes
    - Identify operations that handle the same business logic
    - Search for duplicated code with slight variations
    - Check for similar state mutations across different functions
    - Review functions that interact with the same state variables

2. Check Points
    - Compare the execution flow of similar operations
    - Verify state update sequences across similar functions
    - Check role-based access control implementation
    - Analyze the impact of different implementations on results
    - Review documentation for intended behavior
    - Test same operations through different entry points
    - Compare results of similar operations for consistency

3. Risk Assessment
    - Evaluate potential loss from inconsistent implementations
    - Assess impact on user experience and expectations
    - Consider exploitability of inconsistencies
    - Review impact on protocol's economic model
---
## [04] Time-based Logic & Business Flow

### Problem Pattern: 
- Mismatches between parameter usage and business logic in time-sensitive operations
- Time control mechanisms that may not align with user expectations
- Configuration parameters affecting time-based behaviors
- Implicit dependencies between different time-related components

### Common Scenarios:
- Time-locked withdrawals or deposits
- Fixed-term financial products with withdrawal cycles
- Vesting schedules with multiple time checkpoints
- Multi-step operations with time dependencies
- Systems involving both request time and execution time

### Typical Code:
```solidity
// Time-sensitive function with multiple time parameters
function onTimeBasedOperation(
    address user,
    uint32 executionTime,    // Often passed but unused
    uint256 amount,
    bytes calldata data
) external {
    // Single time check that might miss business requirements
    if (config.endTime > block.timestamp) {
        revert TooEarly();
    }
    
    // Time-sensitive operation
    // Risk: May not consider executionTime parameter
    performOperation(user, amount);
    
    // Configuration that affects timing
    // Risk: Poor configuration could lead to unexpected behavior
    config.nextExecutionTime = block.timestamp + config.operationCycle;
}

// Configuration setting that impacts time behavior
function setTimeConfig(uint256 endTime, uint256 operationCycle) external {
    config.endTime = endTime;
    config.operationCycle = operationCycle;
    // Risk: No validation of relationship between endTime and operationCycle
}
```
### Real Cases

- [[2024-08-wildact#[M-04] `FixedTermLoanHook` looks at `block.timestamp` instead of `expiry`]]
### Audit Key Points:
1. Identification Points
   - Functions with multiple time-related parameters
   - Unused time parameters in function signatures
   - Time-based configuration settings
   - Block timestamp usage
   - Time-dependent state transitions
   - Cycles or periodic operations
   - Multi-step processes with time constraints

2. Code Review Focus
   - Time parameter usage and relationships
   - Time check logic completeness
   - Configuration parameter validation
   - Time calculation accuracy
   - Edge cases in time-based transitions

3. Business Logic Analysis
   - Understand the full timeline of operations
   - Map user expectations to actual behavior
   - Verify time constraint appropriateness
   - Check configurability impact
   - Validate multi-step process timing

4. Testing Scenarios
   - Normal operation flow
   - Boundary conditions
   - Configuration edge cases
   - Time manipulation scenarios
   - Multi-step process sequences

5. Risk Assessment
   - User experience impact
   - System state consistency
   - Configuration risk
   - Time manipulation vulnerability
   - Process deadlock potential

6. Check Points
   - Are all time parameters properly utilized?
   - Is time check logic complete and correct?
   - Do configurations match business requirements?
   - Are time calculations safe from manipulation?
   - Is documentation clear about time behavior?
   - Are there adequate safeguards against misconfiguration?
   - Is the relationship between different time parameters clearly defined?
   - Are edge cases properly handled?

7. Documentation Review
   - Time-related parameter documentation
   - Configuration guidelines
   - Time constraint explanations
   - User expectations management
   - System behavior descriptions

8. Mitigation Strategies
   - Add parameter validation
   - Implement configuration checks
   - Enhance time logic completeness
   - Add safety checks
   - Improve documentation clarity
   - Consider adding time-based invariants
---
## [05] Multi-Step Bypass via OR Logic in Access Controls

### Problem Pattern:
- Multiple conditions connected by `OR` logic in access control or state changes
- One condition can be used to gain position to satisfy another condition
- Step-by-step privilege escalation through legitimate operations

### Common Scenarios:
- Role/permission management systems
- Time-based access controls
- State-dependent operations
- Provider/authority changes

### Typical Code:
```solidity
function sensitiveOperation() {
    if (
        !previousProviderValid ||    // Condition 1
        msg.sender == prevProvider || // Condition 2
        newValue > currentValue      // Condition 3: Can be used first to satisfy Condition 2
    ) {
        // Update critical state/permission
        prevProvider = msg.sender;  // State change that enables second step
        value = newValue;
    }
}
```

### Real Cases:
- [[2024-08-wildact#[M-05] Role provide can bypass intended restrictions and lower expiry set by other providers]]

### Audit Key Points:

1. Identification Points
    - Look for OR (`||`) operators in permission checks
    - Multiple conditions controlling same critical operation
    - State changes that affect who can meet conditions
    - Functions that modify credentials/permissions/roles

2. Check Points
    - Can satisfying one condition help meet others later?
    - Does meeting a condition change who's authorized?
    - Can legitimate operations be chained into attack?
    - Test multi-step sequences through different conditions
    - Map out state changes from each condition