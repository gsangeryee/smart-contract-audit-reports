*Summary from typical issues.*
# Typical Common Issues

- Check all code related to funds
- Check multiplications calculations are stored in limited-size integers
- Precision Loss and  Insufficient Precision
	- Always be aware of the potential loss of precision caused by division operations.
	- Pay special attention to all calculation logics involving division during auditing.
	- Hidden "division before a multiplication"
		- Track the **complete** calculation process of variables

# Typical Logical Issues

- Process Control Points vs. System Control Points
	- Interval calculation boundary alignment
	- Compare `@natspec` and code comment with actual implementation code
- Consistency
	- Look for multiple functions with similar names or purposes
    - Identify operations that handle the same business logic
    - Search for duplicated code with slight variations
    - Check for similar state mutations across different functions
    - Review functions that interact with the same state variables
- Multi-Step Bypass vie OR logic
	- Find all `OR` (`||`) condition in access controls
	- Can satisfying one condition affect other conditions?
	- Map out the relationship between each condition: `Condition A -> Changes State -> Enables Condition B?`
	- Try two-step attack