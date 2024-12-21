1. Numerical Edge Cases
    - Test with zero values
    - Test with one (the smallest meaningful value)
    - Test with maximum possible values (type(uint256).max)
    - Test with values that might cause rounding or precision loss
    - Test with values just below and just above important thresholds
2. State Transition Edge Cases
    - Test rapid state changes (quick deposits/withdrawals)
    - Test maximum number of state changes
    - Test concurrent operations from different users
    - Test operations that might conflict with each other
3. Boundary Conditions
    - Test exactly at limits (like LTV ratios)
    - Test slightly above and below limits
    - Test with minimum and maximum allowed values
    - Test transitions between different states
4. Protocol Interaction Edge Cases
    - Test reentrancy scenarios
    - Test interactions with malicious tokens
    - Test complex multi-contract interactions
    - Test failed external calls
5. Time-Based Edge Cases
    - Test at block boundaries
    - Test at day/year boundaries
    - Test with maximum time intervals
    - Test with minimum time intervals

The key to effective edge case testing is to think like an attacker: 
- what unusual situations could be exploited? 
- What assumptions are the developers making that might not always hold true? 
- When could multiple edge cases interact to create unexpected behavior?
## Example
- [[2023-06-angle#[H-03] Poor detection of disputed trees allows claiming tokens from a disputed tree]]