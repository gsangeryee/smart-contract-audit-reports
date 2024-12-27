# Map Value Transfers: Tracing the Flow of Assets

## Concept 
This strategy involves explicitly tracing the movement of specific assets (tokens, NFTs, ether, etc.) throughout the entire decentralized application (dApp) ecosystem. It's about creating a detailed visual or mental map of where these assets originate, where they are held, how they are transformed, and where they ultimately end up. Think of it like following the money trail in a traditional financial audit.

## How to Implement

- **Diagramming:** Create visual diagrams or flowcharts that illustrate the movement of key assets between contracts and external entities (EOAs, other protocols). Use arrows to represent transfers and label them with the asset type and quantity.
- **Transaction Tracing (Manual or Automated):** For critical transactions, manually trace the execution path using tools like block explorers. Pay close attention to TRANSFER events emitted by token contracts. Consider using automated tools that can help visualize transaction flows.
- **Focus on Key Functions:** Identify functions that are responsible for transferring, minting, burning, or otherwise manipulating significant amounts of assets. These are prime targets for mapping.
- **Follow the Events:** Smart contracts often emit events when assets are transferred. Analyze these events to reconstruct the history of asset movements.
- **Consider Different Asset Types:** Map the flow of all relevant asset types independently. Different tokens might have different handling logic.

## Example

- [[2023-04-blueberry#[H-01] Attackers will keep stealing the `rewards` from Convex SPELL|[H-01] Attackers will keep stealing the `rewards` from Convex SPELL]]