# Min/Max Cap Validation

Min/Max Cap Validation refers to the practice of setting an lower or upper limit on certain parameters within a smart contract to ensure they do not exceed a specified threshold

### Example

1. [[2023-01-UXD#[H-03] RageTrade senior vault USDC deposits are subject to utilization caps which can lock deposits for long periods of time leading to UXD instability|[H-03] RageTrade senior vault USDC deposits are subject to utilization caps which can lock deposits for long periods of time leading to UXD instability]]
	1. *The core issue revolves around the **utilization cap** (max cap) implemented in the RageTrade senior vault, which is designed to ensure solvency but inadvertently introduces a liquidity risk by potentially blocking withdrawals during periods of **high demand**.*

## ERC721A Mint Cap

The `ERC721A` contract (which `ERC721SeaDrop` inherits from) uses an optimization technique called storage packing. This means it efficiently stores multiple pieces of data in a single storage slot to save gas. Specifically, it packs four different values for each address into a single 256-bit storage slot:

1. Token balance (64 bits)
2. Number of tokens minted (64 bits)
3. Number of tokens burned (64 bits)
4. Extra data (64 bits)

This means each of these values has an inherent maximum cap of 2^64-1 (approximately 18.4 quintillion). While this seems enormous, the issue is that the `mintSeaDrop` function doesn't check if a mint would exceed this limit.

### Examples
- [[2022-11-seadrop#[M-05] `ERC721A` has mint caps that are not checked by `ERC721SeaDrop`]]