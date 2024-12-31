
**Key Points**
- Market Status (Deprecated/Closed)
    - Interaction restrictions
    - Order of operations during deprecation
    - Proper cleanup mechanisms
- Liquidation Status
    - Pause/unpause conditions
    - Emergency controls
    - Impact on protocol solvency
- Additional Critical Areas:
    - State transitions between market statuses
    - Oracle price feed reliability
    - Collateral value calculations
    - Fee mechanisms during market changes
    - Access control for status changes
    - Event emissions for status changes

## Examples
- [[2023-03-Morpho#[M-01] A market could be deprecated but still prevent liquidators to liquidate borrowers if `isLiquidateBorrowPaused` is `true`]]