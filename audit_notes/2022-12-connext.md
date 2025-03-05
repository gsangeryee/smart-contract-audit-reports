# 2022-12-connext
---
- Category: #Dexes #Bridge #CDP #services #cross-chain 
- Note Create 2025-02-28
- Platform: spearbit
- Report Url: [2022-12-connext](https://github.com/spearbit/portfolio/blob/master/pdfs/ConnextNxtp-Spearbit-Security-Review.pdf)
---
# Critical & High Risk Findings (xx)

---
## [H-01] `swapInternal()` shouldn't use `msg.sender`
----
- **Tags**: #validation #business_logic 
- Number of finders: 5
- Difficulty: Medium
---
### Detail

As reported by the Connext team, the internal stable swap checks if `msg.sender` has sufficient funds on `execute()`. This `msg.sender` is the `relayer` which normally wouldn't have these funds so the swaps would fail. The local funds should come from the Connext diamond itself.

`BridgeFacet.sol`
```solidity
function execute(ExecuteArgs calldata _args) external nonReentrant whenNotPaused returns (bytes32) { 
	... 
	(uint256 amountOut, address asset, address local) = _handleExecuteLiquidity(...); 
	... 
} 

function _handleExecuteLiquidity(...) ... {
	... 
	(uint256 amount, address adopted) = AssetLogic.swapFromLocalAssetIfNeeded(...); 
	...
}
```

`AssetLogic.sol`
```solidity
function swapFromLocalAssetIfNeeded(...) ... { 
	... 
	return _swapAsset(...); 
} 

function _swapAsset(... ) ... { 
	... 
	SwapUtils.Swap storage ipool = s.swapStorages[_key]; 
	if (ipool.exists()) { 
		// Swap via the internal pool. 
		return ... ipool.swapInternal(...) ... 
	} 
}
```

`SwapUtils.sol`
```solidity
function swapInternal(...) ... { 
	IERC20 tokenFrom = self.pooledTokens[tokenIndexFrom]; 
	require(dx <= tokenFrom.balanceOf(msg.sender), "more than you own"); // msg.sender is the relayer 
	... 
}
```
### Recommended Mitigation

Don't use the balance of `msg.sender`.

`SwapUtils.sol`
```solidity
function swapInternal(...) ... { 
-	IERC20 tokenFrom = self.pooledTokens[tokenIndexFrom]; 
-	require(dx <= tokenFrom.balanceOf(msg.sender), "more than you own"); // msg.sender is the relayer 
+   require(dx <= self.balances[tokenIndexFrom], "more than pool balance");
	... 
}
```
### Discussion

### Notes

```
replyer A ---> BridgeFacet.execute() - msg.sender = A ---> BridgeFacet._handleExecuteLiquidity() - msg.sender = A ---> AssetLogic.swapFromLocalAssetIfNeeded() - msg.sender = A ---> 
AssetLogic._swapAsset() - msg.sender = A ---> SwapUtils.swapInternal msg.sender = A
```

Problem: Checks relayer's balance instead of pool's balance
### Tools
### Refine
- [[1-Business_Logic]]
- [[2-Validation]]

---
## [H-07] No way to update a Stable Swap once assigned to a key
----
- **Tags**: #business_logic 
- Number of finders: 5
- Difficulty: Easy
---
### Detail

Once a Stable Swap is assigned to a key (the hash of the canonical id and domain for token), it cannot be updated nor deleted. A Swap can be hacked or an improved version may be released which will warrant updating the Swap for a key.

[SwapAdminFacet.sol#L109-L177](https://github.com/connext/monorepo/blob/32a0370edc917cc45c231565591740ff274b5c05/packages/deployments/contracts/contracts/core/connext/facets/SwapAdminFacet.sol#L109-L177)
```solidity
  function initializeSwap(
    bytes32 _key,
    IERC20[] memory _pooledTokens,
    uint8[] memory decimals,
    string memory lpTokenName,
    string memory lpTokenSymbol,
    uint256 _a,
    uint256 _fee,
    uint256 _adminFee,
    address lpTokenTargetAddress
  ) external onlyOwnerOrAdmin {
    if (s.swapStorages[_key].pooledTokens.length != 0) revert SwapAdminFacet__initializeSwap_alreadyInitialized();


    // Check _pooledTokens and precisions parameter
    if (_pooledTokens.length <= 1 || _pooledTokens.length > 32)
      revert SwapAdminFacet__initializeSwap_invalidPooledTokens();


    uint8 numPooledTokens = uint8(_pooledTokens.length);


    if (numPooledTokens != decimals.length) revert SwapAdminFacet__initializeSwap_decimalsMismatch();


    uint256[] memory precisionMultipliers = new uint256[](decimals.length);


    for (uint8 i; i < numPooledTokens; ) {
      if (i != 0) {
        // Check if index is already used. Check if 0th element is a duplicate.
        if (s.tokenIndexes[_key][address(_pooledTokens[i])] != 0 || _pooledTokens[0] == _pooledTokens[i])
          revert SwapAdminFacet__initializeSwap_duplicateTokens();
      }
      if (address(_pooledTokens[i]) == address(0)) revert SwapAdminFacet__initializeSwap_zeroTokenAddress();


      if (decimals[i] > SwapUtils.POOL_PRECISION_DECIMALS)
        revert SwapAdminFacet__initializeSwap_tokenDecimalsExceedMax();


      precisionMultipliers[i] = 10**uint256(SwapUtils.POOL_PRECISION_DECIMALS - decimals[i]);
      s.tokenIndexes[_key][address(_pooledTokens[i])] = i;


      unchecked {
        ++i;
      }
    }


    // Check _a, _fee, _adminFee, _withdrawFee parameters
    if (_a >= AmplificationUtils.MAX_A) revert SwapAdminFacet__initializeSwap_aExceedMax();
    if (_fee >= SwapUtils.MAX_SWAP_FEE) revert SwapAdminFacet__initializeSwap_feeExceedMax();
    if (_adminFee >= SwapUtils.MAX_ADMIN_FEE) revert SwapAdminFacet__initializeSwap_adminFeeExceedMax();


    // Initialize a LPToken contract
    LPToken lpToken = LPToken(Clones.clone(lpTokenTargetAddress));
    if (!lpToken.initialize(lpTokenName, lpTokenSymbol)) revert SwapAdminFacet__initializeSwap_failedInitLpTokenClone();


    // Initialize swapStorage struct
    SwapUtils.Swap memory entry = SwapUtils.Swap({
      key: _key,
      initialA: _a * AmplificationUtils.A_PRECISION,
      futureA: _a * AmplificationUtils.A_PRECISION,
      swapFee: _fee,
      adminFee: _adminFee,
      lpToken: lpToken,
      pooledTokens: _pooledTokens,
      tokenPrecisionMultipliers: precisionMultipliers,
      balances: new uint256[](_pooledTokens.length),
      adminFees: new uint256[](_pooledTokens.length),
      initialATime: 0,
      futureATime: 0
    });
    s.swapStorages[_key] = entry;
    emit SwapInitialized(_key, entry, msg.sender);
  }
```
### Recommended Mitigation

Add a privileged `removeSwap()` function to remove a Swap already assigned to a key. In case a Swap has to be updated, it can be deleted and then initialized.

### Discussion

### Notes
#### Impressions
*Smart contracts should implement complete lifecycle management for all critical system components*
1. Initialization mechanisms
2. Update mechanisms
3. Removal/deprecation mechanisms
4. Emergency pause/shutdown mechanisms
### Tools
### Refine
- [[1-Business_Logic]]
---
## [H-09] No way of removing Fraudulent Roots
----
- **Tags**:  #business_logic 
- Number of finders: 5
- Difficulty: Easy
---
### Context

[RootManager](https://github.com/connext/monorepo/blob/32a0370edc917cc45c231565591740ff274b5c05/packages/deployments/contracts/contracts/messaging/RootManager.sol#L1)
### Detail

Fraudulent Roots cannot be removed once fraud is detected by the Watcher. This means that Fraud Roots will be propogated to each chain.
### Recommended Mitigation

Create a new method (callable only by Owner) which can be called when the contract is in paused state to remove the offending roots from the queue

### Discussion

### Notes

*See [[2022-12-connext#[H-7] No way to update a Stable Swap once assigned to a key|[H-7] No way to update a Stable Swap once assigned to a key]]*

### Tools
### Refine

-[[1-Business_Logic]]

---
## [H-11] Missing mirrorConnector check on Optimism hub connector
----
- **Tags**:  #business_logic 
- Number of finders: 5
- Difficulty: Medium
---
### Context

```
  function _processMessage(bytes memory _data) internal override {
    // sanity check root length
    require(_data.length == 32, "!length");

    // get root from data
    bytes32 root = bytes32(_data);

    if (!processed[root]) {
      // set root to processed
      processed[root] = true;
      // update the root on the root manager
      IRootManager(ROOT_MANAGER).aggregate(MIRROR_DOMAIN, root);
    } // otherwise root was already sent to root manager
  }

  /**
   * @dev modified from: https://github.com/ethereum-optimism/optimism/blob/9973c1da3211e094a180a8a96ba9f8bb1ab1b389/packages/contracts/contracts/L1/messaging/L1CrossDomainMessenger.sol#L165
   */
  function processMessageFromRoot(
    address _target,
    address _sender,
    bytes memory _message,
    uint256 _messageNonce,
    L2MessageInclusionProof memory _proof
  ) external {
    // verify the sender is the l2 contract
    require(_sender == mirrorConnector, "!mirrorConnector");

    // verify the target is this contract
    require(_target == address(this), "!this");

    // Get the encoded data
    bytes memory xDomainData = _encodeXDomainCalldata(_target, _sender, _message, _messageNonce);

    require(_verifyXDomainMessage(xDomainData, _proof), "!proof");

    // NOTE: optimism seems to pad the calldata sent in to include more than the expected
    // 36 bytes, i.e. in this transaction:
    // https://blockscout.com/optimism/goerli/tx/0x440fda036d28eb547394a8689af90c5342a00a8ca2ab5117f2b85f54d1416ddd/logs
    // the corresponding _message is:
    // 0x4ff746f60000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000002027ae5ba08d7291c96c8cbddcc148bf48a6d68c7974b94356f53754ef6171d757
    //
    // this means the length check and byte parsing used in the `ArbitrumHubConnector` would
    // not work here. Instead, take the back 32 bytes of the string, regardless of the length. The length
    // can be validated in _processMessage

    // NOTE: TypedMemView only loads 32-byte chunks onto stack, which is fine in this case
    bytes29 _view = _message.ref(0);
    bytes32 _data = _view.index(_view.len() - 32, 32);

    _processMessage(abi.encode(_data));
    emit MessageProcessed(abi.encode(_data), msg.sender);
  }
```
### Detail

`processMessageFromRoot()` calls `_processMessage()` to process messages for the "fast" path. But `_processMessage()` can also be called by the AMB in the slow path. 

The second call to `_processMessage()` is not necessary (and could double process the message, which luckily is prevented via the `processed[]` mapping). The second call (from the AMB directly to `_processMessage()`) also doesn't properly verify the origin of the message, which might allow the insertion of fraudulent messages.

```
function processMessageFromRoot(...) ... { 
	... 
	_processMessage(abi.encode(_data)); 
	... 
} 

function _processMessage(bytes memory _data) internal override { 
	// sanity check root length 
	require(_data.length == 32, "!length"); 
	
	// get root from data 
	bytes32 root = bytes32(_data); 
	
	if (!processed[root]) { 
		// set root to processed 
		processed[root] = true; 
		// update the root on the root manager 
		IRootManager(ROOT_MANAGER).aggregate(MIRROR_DOMAIN, root); 
	} // otherwise root was already sent to root manager 
}
```
### Recommended Mitigation

Remove the second path.

```solidity
function _processMessage(bytes memory _data) internal override { 
-	// sanity check root length 
-	require(_data.length == 32, "!length"); 
-	
-	// get root from data 
-	bytes32 root = bytes32(_data); 
-	
-	if (!processed[root]) { 
-		// set root to processed 
-		processed[root] = true; 
-		// update the root on the root manager 
-		IRootManager(ROOT_MANAGER).aggregate(MIRROR_DOMAIN, root); 
-	} // otherwise root was already sent to root manager 
+   // Does nothing, all messages should go through the `processMessageFromRoot` path
+   revert Connector__processMessage_notUsed();
}

function processMessageFromRoot(...) ... { 
	... 
-	bytes32 _data = _view.index(_view.len() - 32, 32);
-    _processMessage(abi.encode(_data));
-    emit MessageProcessed(abi.encode(_data), msg.sender);
+    bytes32 root = _view.index(_view.len() - 32, 32);
+
+    if (!processed[root]) {
+        // set root to processed
+        processed[root] = true;
+       // update the root on the root manager
+       IRootManager(ROOT_MANAGER).aggregate(MIRROR_DOMAIN, root);
+       emit MessageProcessed(abi.encode(root), msg.sender);
+    } // otherwise root was already sent to root manager
}
 
```

### Discussion

### Notes

#### Impressions
always check for alternative entry points to critical functionality
### Tools
### Refine
- [[1-Business_Logic]]
---
# Medium Risk Findings (xx)

---
## [M-06] The set of tokens in an internal swap pool cannot be updated
----
- **Tags**: #business_logic 
- Number of finders: nnn
- Difficulty: Medium
---
### Context
[SwapAdminFacet.sol#L109-L119](https://github.com/connext/monorepo/blob/32a0370edc917cc45c231565591740ff274b5c05/packages/deployments/contracts/contracts/core/connext/facets/SwapAdminFacet.sol#L109-L119)
```solidity
  function initializeSwap(
    bytes32 _key,
    IERC20[] memory _pooledTokens,
    uint8[] memory decimals,
    string memory lpTokenName,
    string memory lpTokenSymbol,
    uint256 _a,
    uint256 _fee,
    uint256 _adminFee,
    address lpTokenTargetAddress
  ) external onlyOwnerOrAdmin {
```
### Detail
Once a swap is initialized by the `owner` or an `admin` (indexed by the `key` parameter) the `_pooledTokens` or the set of tokens used in this stable swap pool cannot be updated. 

Now the `s.swapStorages[_key]` pools are used in other facets for assets that have the hash of their canonical token id and canonical domain equal to `_key`, for example when we need to swap between a local and adopted asset or when a user provides liquidity or interact with other `external` endpoints of `StableSwapFacet`.

If the submitted set of tokens to this pool `_pooledTokens` beside the local and adopted token corresponding to `_key` include some other `bad/malicious` tokens, users' funds can be at risk in the pool in question. If this happens, we need to pause the protocol, push an update, and `initializeSwap` again. 
### Recommendation
Document the procedure on how `_pooledTokens` is selected and submitted to initializeSwap to lower the risk of introducing potentially bad/malicious tokens into the system.
### Discussion

### Notes & Impressions

#### Notes 
See 
- [[2022-12-connext#[H-07] No way to update a Stable Swap once assigned to a key|[H-07] No way to update a Stable Swap once assigned to a key]]
- [[2022-12-connext#[H-09] No way of removing Fraudulent Roots|[H-09] No way of removing Fraudulent Roots]]
### Tools
### Refine
- [[1-Business_Logic]]
---
## [M-10] `TypedMemView.sameType` does not use the correct right shift value to compare two `bytes29`s
----
- **Tags**: #business_logic #bitwise
- Number of finders: 5
- Difficulty: Medium
---
### Context

[TypedMemView.sol#L401-L403](https://github.com/connext/monorepo/blob/32a0370edc917cc45c231565591740ff274b5c05/packages/deployments/contracts/contracts/shared/libraries/TypedMemView.sol#L401-L403)
```solidity
  function sameType(bytes29 left, bytes29 right) internal pure returns (bool) {
    return (left ^ right) >> (2 * TWELVE_BYTES) == 0;
  }
```
### Detail

The function `sameType` should shift `2 x 12 + 3` bytes to access the` type flag (TTTTTTTTTT)` when comparing it to `0`. This is due to the fact that when using `bytes29` type in bitwise operations and also comparisons to `0`, a paramater of type `bytes29` is zero padded from the right so that it fits into a `uint256` under the hood.

```
0x TTTTTTTTTT AAAAAAAAAAAAAAAAAAAAAAAA LLLLLLLLLLLLLLLLLLLLLLLL 00 00 00
```

Currently, `sameType` only shifts the` xored` value `2 x 12` bytes so the comparison compares the `type` flag and the 3 leading bytes of `memory address` in the packing specified below:

```
// First 5 bytes are a type flag. 
// - ff_ffff_fffe is reserved for unknown type. 
// - ff_ffff_ffff is reserved for invalid types/errors. 
// next 12 are memory address 
// next 12 are len 
// bottom 3 bytes are empty
```

The function is not used in the codebase but can pose an important issue if incorporated into the project in the future.

```
uint8 constant TWELVE_BYTES = 96;
...
function sameType(bytes29 left, bytes29 right) internal pure returns (bool) { 
	return (left ^ right) >> (2 * TWELVE_BYTES) == 0; 
}
```
### Recommended Mitigation

Change `sameType()` to take the `zero` padding into account:

```
uint256 private constant TWENTY_SEVEN_BYTES = 8 * 27; 
... 
function sameType(bytes29 left, bytes29 right) internal pure returns (bool) { 
	return (left ^ right) >> TWENTY_SEVEN_BYTES == 0; 
}
```

### Discussion

### Notes & Impressions

#### Notes 
In the `TypedMemView` library, a `bytes29` is a packed value with a specific bit structure:

```
0xTTTTTTTTTT_AAAAAAAAAAAAAAAAAAAAAAAA_LLLLLLLLLLLLLLLLLLLLLLLL_000000
  |--5 bytes--|--------12 bytes--------|--------12 bytes--------|--3--|
    Type flag       Memory address            Length            Empty
```
- **Type flag (5 bytes)**: Identifies what kind of data this is
- **Memory address (12 bytes)**: Points to where the data is in memory
- **Length (12 bytes)**: Indicates how long the data is
- **Empty space (3 bytes)**: Unused padding (Cause Solidity EVM )

### The Problem In Detail

When Solidity performs bitwise operations on a `bytes29` value, it needs to convert it to a `uint256` (a 32-byte value). This means adding 3 bytes of zero padding on the right:

```
Original bytes29 (29 bytes):
0xTTTTTTTTTT_AAAAAAAAAAAAAAAAAAAAAAAA_LLLLLLLLLLLLLLLLLLLLLLLL

As uint256 for operations (32 bytes):
0xTTTTTTTTTT_AAAAAAAAAAAAAAAAAAAAAAAA_LLLLLLLLLLLLLLLLLLLLLLLL_000000
                                                                 ↑
                                                        3 bytes of padding
```

The current `sameType` function:

```
function sameType(bytes29 left, bytes29 right) internal pure returns (bool) {
  return (left ^ right) >> (2 * TWELVE_BYTES) == 0;
}
```

Here, `TWELVE_BYTES = 96` (bits), so the shift is `2 * 96 = 192` bits.

This means we're shifting the XOR result right by 192 bits (24 bytes), leaving the leftmost 8 bytes for comparison (32 - 24 = 8):

```
left ^ right:
0xRRRRRRRRRR_RRRRRRRRRRRRRRRRRRRRRRRR_RRRRRRRRRRRRRRRRRRRRRRRR_RRRRRR
                                       ↑
                      Shift by 192 bits (24 bytes)

After shift:
0x00000000000000000000000000000000000000000000000000_RRRRRRRRRR_RRR000
                                                       ↑         ↑
                                               5-byte type flag  +3 bytes of address
```

So when we compare with 0, we're actually checking if:
1. The entire type flag (5 bytes) AND
2. The first 3 bytes of the memory address ...are the same for both values.
This is wrong! We only want to compare the type flags.

#### A Concrete Example

Let's look at two hypothetical `bytes29` values:

**Value 1:**

- Type flag: `0xAABBCCDDEE`
- Address: `0x112233445566778899AABBCC`
- Length: `0x112233445566778899AABBCC`

In hex: `0xAABBCCDDEE112233445566778899AABBCC112233445566778899AABBCC`

**Value 2:**

- Type flag: `0xAABBCCDDEE` (same type)
- Address: `0x992233445566778899AABBCC` (different in first byte)
- Length: `0x554433221166778899AABBCC` (different length)

In hex: `0xAABBCCDDEE992233445566778899AABBCC554433221166778899AABBCC`
#### With Current Implementation

1. XOR the values:
    ```
    0xAABBCCDDEE112233445566778899AABBCC112233445566778899AABBCC
    0xAABBCCDDEE992233445566778899AABBCC554433221166778899AABBCC
    ^ ---------------------------------------------------------
    0x00000000008800000000000000000000009966000044000000000000
    ```
2. Shift right by 192 bits (24 bytes):
    ```
    0x00000000008800000000000000000000009966000044000000000000 >> 192
    = 0x0000000000880000
    ```
    
3. Compare with 0:
    ```
    0x0000000000880000 == 0 ? 
    ```
    This is false, so `sameType` returns false.
    
Even though both values have the SAME type flag (`0xAABBCCDDEE`), the function incorrectly returns `false` because it's also comparing part of the address.
#### With Corrected Implementation

1. XOR the values (same as before)
    
2. Shift right by 216 bits (27 bytes):
    
    ```
    0x00000000008800000000000000000000009966000044000000000000 >> 216
    = 0x000000000
    ```
    
3. Compare with 0:
    
    ```
    0x000000000 == 0 ? 
    ```
    
    This is true, so `sameType` returns true.
    

With the fix, we're properly identifying that the values have the same type.

#### Why The Fix Works

The problem is caused by not shifting enough. The current code shifts by:

- 2 * 12 bytes = 24 bytes

But we need to shift by:

- 2 * 12 bytes + 3 bytes (the padding) = 27 bytes

Or more directly, we need to shift right by the total number of bytes except for the type flag:

- 32 bytes (full uint256) - 5 bytes (type flag) = 27 bytes

The recommended fix creates a constant:

```solidity
uint256 private constant TWENTY_SEVEN_BYTES = 8 * 27; // 216 bits
```

And then uses it correctly:

```solidity
function sameType(bytes29 left, bytes29 right) internal pure returns (bool) { 
    return (left ^ right) >> TWENTY_SEVEN_BYTES == 0; 
}
```

This ensures we're isolating just the 5-byte type flag in our comparison.

#### Impressions
*When performing bitwise operations on packed data structures, ensure the bit shifting exactly isolates the intended components, accounting for any padding that occurs during type conversions.*

### Tools
### Refine

- [[1-Business_Logic]]
- [[22-Bitwise]]

---
---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}