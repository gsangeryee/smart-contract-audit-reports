Start by mapping out all the important state variables and their relationships. In this case, we had several critical state variables:

- `tree.merkleRoot`: The current Merkle root
- `lastTree.merkleRoot`: The previous Merkle root
- `endOfDisputePeriod`: Timestamp when disputes can no longer be raised
- `disputer`: Address of the entity disputing the current tree

For each state variable, ask yourself: 
- "What other state variables should be considered alongside this one when making decisions?" 
- This helps identify missing validation checks.