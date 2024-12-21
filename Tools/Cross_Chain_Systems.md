1. State Flow Analysis Create detailed flow diagrams for assets and resources:
	- Map out how gas moves through the system
	- Identify all points where resources are consumed
	- Track where fees are collected
	- Document all possible paths for failed transactions
2. Economic Invariant Testing Define and verify economic invariants:
	For any transaction T:
	Total Gas Consumed <= Total Gas Deposited
	Where:
	- Total Gas Consumed = Execution Gas + Fallback Gas + Fees
	- Total Gas Deposited = Initial User Deposit
3. Cross-Chain State Matrix Create a matrix of possible states across chains:
```text
Chain A State | Chain B State | Valid/Invalid | Required Resources
Success       | Success       | Valid         | Execution Gas
Success       | Fail          | Valid         | Execution Gas + Fallback Gas
Fail          | Success       | Valid         | Execution Gas + Fallback Gas
Fail          | Fail          | Valid         | Execution Gas + Fallback Gas
```
4. Resource Reservation Analysis For each operation that consumes resources:
	- Identify when the resource need is determined
	- Verify when the resource is reserved
	- Check when the resource is consumed
	- Confirm when excess resources are released
5. Failure Path Testing Create comprehensive test scenarios:
	- Test all possible failure points
	- Verify resource accounting in each failure scenario 
	- Check system solvency after failed transactions
	- Validate fee collection doesn't compromise safety
6. Component Interaction Checklist For each component:
	- List all other components it interacts with
	- Document resources it can consume
	- Identify resources it can reserve
	- Note any fees it can collect




## List of cases
- [[2023-05-maia#[M-31] Incorrect accounting logic for `fallback` gas will lead to insolvency|[M-31] Incorrect accounting logic for `fallback` gas will lead to insolvency]]