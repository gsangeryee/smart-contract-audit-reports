When performing bitwise operations on packed data structures, ensure the bit shifting exactly isolates the intended components, accounting for any padding that occurs during type conversions.

### Key Audit Flags to Watch For:

1. **Bit shifting operations** on custom data types or packed structures
2. **Non-standard sized types** (anything not uint256/bytes32)
3. **XOR comparisons** followed by bit shifting
4. **Type conversion** between different sizes of data

### Practical Audit Questions:

When reviewing similar code, ask:

- Does the bit shifting account for the actual memory layout?
- Is the code considering how the EVM handles types smaller than 32 bytes?
- Are there any conversions happening during operations that could affect bit positioning?
- Does the bit math correctly isolate only the fields intended for comparison?

## Cases
- [[2022-12-connext#[M-10] `TypedMemView.sameType` does not use the correct right shift value to compare two `bytes29`s|[M-10] `TypedMemView.sameType` does not use the correct right shift value to compare two `bytes29`s]]