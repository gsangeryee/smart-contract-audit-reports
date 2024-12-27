# Source and Sink Analysis: Tracking the Lifecycle of Value

## Concept
This approach focuses on identifying the origin ("source") and the ultimate destination ("sink") of specific assets within the system. It's about understanding the complete lifecycle of a particular unit of value, from its creation to its potential destruction or final resting place.

## How to Implement

- **Identify Creation Points (Sources):** Determine the contracts and functions responsible for minting, depositing, or otherwise bringing new assets into the system. Examples include token minting functions, deposit functions for stablecoins, or initial distribution mechanisms.
- **Identify Termination Points (Sinks):** Determine the contracts and functions responsible for burning, withdrawing, or otherwise removing assets from the system. Examples include token burning functions, withdrawal functions, or transfers to external addresses.
- **Trace the Paths Between Source and Sink:** Analyze the intermediate steps and transformations that occur between the source and the sink. This involves examining inter-contract calls, state changes, and conditional logic.
- **Consider Different Scenarios:** Analyze the source and sink under various conditions and user interactions. What happens under normal circumstances? What happens during edge cases or error conditions?

## Examples

- [[2023-04-blueberry#[H-01] Attackers will keep stealing the `rewards` from Convex SPELL|[H-01] Attackers will keep stealing the `rewards` from Convex SPELL]]

## Practical Example

Consider a stablecoin protocol:

- **Source:** The contract that mints new stablecoins when users deposit collateral.
    
- **Sink:** The contract that burns stablecoins when users withdraw their collateral.
    

By analyzing the path between the source and sink, you can verify:

- That new stablecoins are only minted when valid collateral is deposited.
    
- That the correct amount of stablecoins is burned upon withdrawal.
    
- That there are no alternative pathways for minting or burning stablecoins that bypass the intended logic.