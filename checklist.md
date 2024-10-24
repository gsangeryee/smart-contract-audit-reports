*Summary from typical issues.*
# Typical Common Issues

- Precision Loss and  Insufficient Precision
	- Always be aware of the potential loss of precision caused by division operations.
	- Pay special attention to all calculation logics involving division during auditing.
	- Hidden "division before a multiplication"
		- Track the **complete** calculation process of variables

# Typical Logical Issues

- Process Control Points vs. System Control Points
	- Interval calculation boundary alignment