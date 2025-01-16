Since many DeFi contracts involve time-based operations, analyze all time-dependent logic by asking:

1. What happens before a timestamp?
2. What happens after a timestamp?
3. What happens if an action occurs exactly at the timestamp?
4. What state changes persist across these time boundaries?
5. Check how duration changes affect existing process


## Example
- [[2023-06-angle#[H-03] Poor detection of disputed trees allows claiming tokens from a disputed tree]]
- [[2023-02-astaria#[M-05] If auction time is reduced, `withdrawProxy` can lock funds from final auctions|[M-05] If auction time is reduced, `withdrawProxy` can lock funds from final auctions]]
	- Check how duration changes affect existing process