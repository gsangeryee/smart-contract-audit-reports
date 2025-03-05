Functions that modify shared state (like arrays/sets) where transaction ordering matters:

- Multiple parties can call the same function
- State changes affect subsequent operations
- No mechanism to handle concurrent modifications

## Example
- [[2022-12-liquid-collective#[H-2] Order of calls to `removeValidators` can affect the resulting validator keys set]]
- [[2023-05-liquid_collective#[H-01] `_pickNextValidatorsToExitFromActiveOperators` uses the wrong index to query stopped validator]]