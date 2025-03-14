# Mutual Consent Mechanisms

Mutual consent mechanisms are a common pattern in blockchain applications, but they come in various forms and implementations. Let me explain their broader context and how they're used in different scenarios.

## Mutual Consent Mechanisms in Blockchain

Mutual consent mechanisms are a design pattern used when transactions require approval from multiple parties before execution. This pattern appears in many blockchain applications, though the specific implementation in the code you shared has some unique characteristics.

### Common Applications of Mutual Consent

1. **Multisignature Wallets**: Perhaps the most common application of mutual consent in blockchain. These wallets require multiple private keys to authorize transactions, typically implemented as "m-of-n" signatures (e.g., 2-of-3, where any 2 out of 3 designated signers must approve).
2. **DAO Governance**: Many decentralized autonomous organizations implement proposal and voting systems where changes require consent from multiple stakeholders.
3. **Escrow Services**: Smart contracts that hold assets until multiple parties agree to release them, often used in decentralized marketplaces.
4. **Cross-Chain Bridges**: Systems that require validators from multiple chains to agree before assets are minted or released.
5. **DeFi Protocols**: Many lending, borrowing, and liquidity protocols require multiple approvals for certain high-risk operations.

### Implementation Approaches

The specific implementation in your code sample is one approach, but there are several common patterns:

1. **Signature Collection**: The most common approach gathers cryptographic signatures off-chain and submits them in a single transaction. This is gas-efficient but requires off-chain coordination.
2. **On-Chain Consent Registry**: The approach used in your sample, where approvals are stored on-chain as separate transactions. This is more gas-intensive but doesn't require off-chain coordination.
3. **Timelock Mechanisms**: Where one party initiates a transaction that only executes after a time delay, during which other parties can review and approve or cancel.
4. **Role-Based Access Control**: Where specific actions require approval from accounts with particular roles (e.g., admin and operator must both approve).

## The Specific Implementation in Your Code

The implementation in your code sample is somewhat unusual in its specific approach:

1. It uses a transaction data hash as a consent identifier, which is clever but introduces complications.
2. It allows the function to be called directly by either party, rather than having separate "approve" and "execute" functions.
3. It deletes the consent record after execution, which prevents replay attacks but also means there's no persistent record of who approved what.
4. It doesn't use a proper time-lock mechanism, which is a common safety feature in multi-signature systems.

The fundamental issue with this implementation is that it doesn't properly separate the consent logic from the execution logic, especially for functions that involve asset transfers.

## Best Practices for Mutual Consent

Better implementations of mutual consent typically:

1. **Separate Approval from Execution**: Have dedicated functions for registering approval and executing the action.
2. **Handle Asset Transfers Properly**: Only transfer assets during the execution phase, not during the approval phase.
3. **Include Timeouts**: Approvals should expire after a certain period to prevent stale approvals from being used.
4. **Provide Cancellation Mechanisms**: Allow parties to revoke their approval before execution.
5. **Emit Detailed Events**: Log who approved what and when, for transparency and auditability.
    

The vulnerability in your code exists because the implementation didn't follow these best practices, particularly by not separating the approval logic from the asset transfer logic.

In more mature protocols like Gnosis Safe, OpenZeppelin Governor, or Compound's Timelock, you'll find more robust implementations of mutual consent that address these issues. These have undergone extensive auditing and real-world testing, making them safer to use or adapt for specific needs.

## Cases

- [[2022-11-debtdao#[H-03] `addCredit` / `increaseCredit` cannot be called by lender first when token is ETH]]