# Min/Max Cap Validation

Min/Max Cap Validation refers to the practice of setting an lower or upper limit on certain parameters within a smart contract to ensure they do not exceed a specified threshold

# Example

1. [[2023-01-UXD#[H-03] RageTrade senior vault USDC deposits are subject to utilization caps which can lock deposits for long periods of time leading to UXD instability|[H-03] RageTrade senior vault USDC deposits are subject to utilization caps which can lock deposits for long periods of time leading to UXD instability]]
	1. *The core issue revolves around the **utilization cap** (max cap) implemented in the RageTrade senior vault, which is designed to ensure solvency but inadvertently introduces a liquidity risk by potentially blocking withdrawals during periods of **high demand**.*