
This represents a broader issue of **asymmetric access control** where:

- Users can enter a system through multiple authorization pathways
- But exit routes are more restricted than entry routes
- Result: Funds can become trapped

## How to Find Similar Issues

1. Map all entry and exit points in a protocol
2. Compare authorization logic between matching functions:
    - Deposit vs. withdraw(redeem)
    - Mint vs. burn
    - Lock vs. unlock
    - Buy vs. sell
3. Check if any authorization method available for entry is missing from the corresponding exit

## Red Flags

- Different hook/modifier implementations between paired functions
- Authorization logic that's more complex for exiting than entering
- Comments about "governance control" over exit functions
- Multiple protocol roles with different permissions

## Testing Approach

Test every authorized user type for their ability to complete the full lifecycle of interactions, especially exits and withdrawals.

## Example Cases

-[[2022-12-prePO#[M-04] PrePO NFT holders will not be able to redeem collateral|[M-04] PrePO NFT holders will not be able to redeem collatera]]