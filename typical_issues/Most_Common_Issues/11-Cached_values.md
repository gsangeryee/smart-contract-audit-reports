The key risks with cached values are:

1. Staleness - Cached values can become outdated if not frequently updated
2. Value divergence - Critical calculations using stale cache may differ from actual protocol state
3. Financial impact - In DeFi, outdated values can lead to incorrect liquidations, loan amounts, or other financial operations

Best practices:
- Use real-time values for critical financial calculations
- If caching is needed, implement frequent cache updates
- Add cache staleness checks
- Document cache dependencies clearly



## Example
- [[2023-03-Morpho#[M-14] Compound liquidity computation uses outdated cached borrowIndex]]
	- In this case, using Compound's live borrowIndex instead of Morpho's cached version would ensure accurate liquidation calculations.