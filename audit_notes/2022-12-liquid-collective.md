# 2022-12-Liquid Collective
---
- Category: #staking_pool #liquid_staking #services #yield_aggregator #cross-chain 
- Note Create 2025-02-24
- Platform: Spearbit
- Report Url: [2022-12-Liquid Collective](https://github.com/spearbit/portfolio/blob/master/pdfs/LiquidCollective-Spearbit-Security-Review.pdf)
---
# Critical & High Risk Findings (xx)

---
## [C-3] `OperatorsRegistry._getNextValidatorsFromActiveOperators` can DOS Alluvial staking if there's an operator with `funded==stopped` and `funded == min(limit, keys)`
----
- **Tags**:  #validation #business_logic 
- Number of finders: 5
- Difficulty: Medium
---
### Context Code:

[OperatorsRegistry.1.sol#L403-L454](https://github.com/liquid-collective/liquid-collective-protocol/blob/778d71c5c2b0bb7d430b60df72b4d65173ebee6a/contracts/src/OperatorsRegistry.1.sol#L403-L454)
```solidity
    /// @notice Handler called whenever a deposit to the consensus layer is made. Should retrieve _requestedAmount or lower keys
    /// @param _requestedAmount Amount of keys required. Contract is expected to send _requestedAmount or lower.
    function _getNextValidatorsFromActiveOperators(uint256 _requestedAmount)
        internal
        returns (bytes[] memory publicKeys, bytes[] memory signatures)
    {
        Operators.CachedOperator[] memory operators = Operators.getAllFundable();


        if (operators.length == 0) {
            return (new bytes[](0), new bytes[](0));
        }


        uint256 selectedOperatorIndex = 0;
        for (uint256 idx = 1; idx < operators.length;) {
            if (
                operators[idx].funded - operators[idx].stopped
                    < operators[selectedOperatorIndex].funded - operators[selectedOperatorIndex].stopped
            ) {
                selectedOperatorIndex = idx;
            }
            unchecked {
                ++idx;
            }
        }


        uint256 selectedOperatorAvailableKeys = Uint256Lib.min(
            operators[selectedOperatorIndex].keys, operators[selectedOperatorIndex].limit
        ) - operators[selectedOperatorIndex].funded;


        if (selectedOperatorAvailableKeys == 0) {
            return (new bytes[](0), new bytes[](0));
        }


        Operators.Operator storage operator = Operators.get(operators[selectedOperatorIndex].name);
        if (selectedOperatorAvailableKeys >= _requestedAmount) {
            (publicKeys, signatures) = ValidatorKeys.getKeys(
                operators[selectedOperatorIndex].index, operators[selectedOperatorIndex].funded, _requestedAmount
            );
            operator.funded += _requestedAmount;
        } else {
            (publicKeys, signatures) = ValidatorKeys.getKeys(
                operators[selectedOperatorIndex].index,
                operators[selectedOperatorIndex].funded,
                selectedOperatorAvailableKeys
            );
            operator.funded += selectedOperatorAvailableKeys;
            (bytes[] memory additionalPublicKeys, bytes[] memory additionalSignatures) =
                _getNextValidatorsFromActiveOperators(_requestedAmount - selectedOperatorAvailableKeys);
            publicKeys = _concatenateByteArrays(publicKeys, additionalPublicKeys);
            signatures = _concatenateByteArrays(signatures, additionalSignatures);
        }
    }
```
### Description

This issue is also related to `OperatorsRegistry._getNextValidatorsFromActiveOperators` should not consider `stopped` when picking a validator.

Consider a scenario where we have
```
Op at index 0 
name op1 
active true 
limit 10 
funded 10 
stopped 10 
keys 10 

Op at index 1 
name op2 
active true 
limit 10 
funded 0 
stopped 0 
keys 10
```

In this case, 
- Op1 got all 10 keys funded and exited. Because it has `keys=10` and `limit=10` it means that it has no more keys to get funded again. 
- Op2 instead has still 10 approved keys to be funded. 

Because of how the selection of the picked validator works
```solidity
uint256 selectedOperatorIndex = 0; 
for (uint256 idx = 1; idx < operators.length;) { 
	if ( 
		operators[idx].funded - operators[idx].stopped < operators[selectedOperatorIndex].funded - operators[selectedOperatorIndex].stopped 
	) { 
		selectedOperatorIndex = idx; 
	} 
	unchecked { 
		++idx; 
	}
```

When the function finds an operator with `funded == stopped` it will pick that operator because `0 < operators[selectedOperatorIndex].funded - operators[selectedOperatorIndex].stopped`. 

After the loop ends, `selectedOperatorIndex` will be the index of an operator that has no more validators to be funded (for this scenario). Because of this, the following code
```
uint256 selectedOperatorAvailableKeys = Uint256Lib.min( 
			operators[selectedOperatorIndex].keys, 
			operators[selectedOperatorIndex].limit 
		) - operators[selectedOperatorIndex].funded;
```

when executed on Op1 it will set `selectedOperatorAvailableKeys = 0` and as a result, the function will return `return (new bytes[](0), new bytes[](0));`.

In this scenario when `stopped==funded` and there are no keys available to be funded `(funded == min(limit, keys))` the function will **always** return an empty result, breaking the `pickNextValidators` mechanism that won't be able to stake user's deposited ETH anymore even if there are operators with fundable validators. 
Check the Appendix for a test case to reproduce this issue. 

### Recommendation: 
Alluvial should 
- reimplement the logic of `Operators._hasFundableKeys` that should select only active operators with fundable keys without using the `stopped` attribute. 
- reimplement the logic inside the `OperatorsRegistry._getNextValidatorsFromActiveOperators` loop to correctly pick the active operator with the higher number of fundable keys without using the `stopped` attribute. 
### Notes

#### Notes 
Imagine we have only two operators in the system:

**Operator A (Fully Used Up)**
- Keys provided: 10
- Limit set: 10
- Currently funded: 10
- Stopped/exited: 10

**Operator B (Fresh and Ready)**
- Keys provided: 10
- Limit set: 10
- Currently funded: 0
- Stopped/exited: 0

Now, let's walk through what happens when someone deposits ETH and the function runs:

1. The function starts by defaulting to Operator A as the first selection
2. It compares Operator B to Operator A:
   - Operator A has: funded - stopped = 10 - 10 = 0 active validators
   - Operator B has: funded - stopped = 0 - 0 = 0 active validators
3. Since both have the same number (0), it keeps Operator A as its selection (doesn't change selections when equal)
4. Next, it calculates how many available validator slots Operator A has:
   ```
   availableKeys = min(keys, limit) - funded
   availableKeys = min(10, 10) - 10 = 0
   ```
5. Since Operator A has 0 available keys, the function returns empty arrays
6. The function ends here without even considering Operator B, which actually has 10 available keys!

#### Impressions

The core issue is related to how subtraction is used in comparison logic.

*Mathematical equivalence doesn't mean functional equivalence.*
 
### Tools
### Refine

- [[1-Business_Logic]]
- [[2-Validation]]
---
## [H-2] Order of calls to `removeValidators` can affect the resulting validator keys set
----
- **Tags**:  #business_logic #array_index #front-running #Denial_of_Service 
- Number of finders: 5
- Difficulty: Medium
---
### Context
[OperatorsRegistry.1.sol#L310](https://github.com/liquid-collective/liquid-collective-protocol/blob/778d71c5c2b0bb7d430b60df72b4d65173ebee6a/contracts/src/OperatorsRegistry.1.sol#L310)
```solidity
    function removeValidators(uint256 _index, uint256[] calldata _indexes) external operatorOrAdmin(_index) {
        Operators.Operator storage operator = Operators.getByIndex(_index);


        if (_indexes.length == 0) {
            revert InvalidKeyCount();
        }


        for (uint256 idx = 0; idx < _indexes.length;) {
            uint256 keyIndex = _indexes[idx];


            if (keyIndex < operator.funded) {
                revert InvalidFundedKeyDeletionAttempt();
            }


            if (keyIndex >= operator.keys) {
                revert InvalidIndexOutOfBounds();
            }


            if (idx > 0 && _indexes[idx] >= _indexes[idx - 1]) {
                revert InvalidUnsortedIndexes();
            }


            uint256 lastKeyIndex = operator.keys - 1;
            (bytes memory removedPublicKey,) = ValidatorKeys.get(_index, keyIndex);
            (bytes memory lastPublicKey, bytes memory lastSignature) = ValidatorKeys.get(_index, lastKeyIndex);
            ValidatorKeys.set(_index, keyIndex, lastPublicKey, lastSignature);
            ValidatorKeys.set(_index, lastKeyIndex, new bytes(0), new bytes(0));
            operator.keys -= 1;
            emit RemovedValidatorKey(_index, removedPublicKey);
            unchecked {
                ++idx;
            }
        }


        if (_indexes[_indexes.length - 1] < operator.limit) {
            operator.limit = _indexes[_indexes.length - 1];
        }
    }
```
### Description

If two entities A and B (which can be either the admin or the operator O with the index I) send a call to `removeValidators` with 2 different set of parameters:
- $T_1:\left(I, R_1\right)$
- $T_2:\left(I, R_2\right)$
Then depending on the order of transactions, the resulting set of validators for this operator might be different. And since either party might not know a priori if any other transaction is going to be included on the blockchain after they submit their transaction, they don't have a 100 percent guarantee that their intended set of validator keys are going to be removed.

This also opens an opportunity for either party to DoS the other party's transaction by front-running it with a call to remove enough validator keys to trigger the `InvalidIndexOutOfBounds` error:

[OperatorsRegistry.1.sol#L324-L326](https://github.com/liquid-collective/liquid-collective-protocol/blob/778d71c5c2b0bb7d430b60df72b4d65173ebee6a/contracts/src/OperatorsRegistry.1.sol#L324-L326)
```solidity
            if (keyIndex >= operator.keys) {
                revert InvalidIndexOutOfBounds();
            }
```

### Recommendation: 

We can send a snapshot block parameter to `removeValidators` and compare it to a stored field for the operator and make sure there have not been any changes to the validator key set since that snapshot block. Alluvial has introduced such a mechanism for `setOperatorLimits`. A similar technique can be used here. 

### Discussion

Alluvial: Don't think this is really an issue. 

On a regular basis, the admin would not remove the keys but would request the Node Operator to remove the keys (because a key is unhealthy for example). In case a Node Operator refuses to remove the key (which is unexpected because this is would be against terms and conditions) then the admin could deactivate the operator and then remove the key without being exposed to the front run attack. 

This is not as sensitive as the front run we had on setOperatorLimit because in this case, we are not making any keys eligible for funding. So the consequences are not this bad. Worst case the admin deactivates the node operator and there is no issue anymore. 

Spearbit: We think the issue still needs to be documented both for the admin and also for the operators. Because in the scenario above both A and B can be the operator O. And O might send two transactions T1, T2 thinking T1 would be applied to the state before T2 (this might be unintentional, or intentional maybe because of something like out-of-gas issues). But it is possible that the order would be reversed and the end result would not be what the operator had expected. And if the operator would not check this, the issue can go unnoticed.
### Notes

#### Notes 

The problem arises because of transaction ordering on the blockchain. Imagine two transactions that want to remove different validator keys:

- Transaction 1 wants to remove keys [5, 4, 3]
- Transaction 2 wants to remove keys [8, 7, 6]

When these transactions are submitted, their final execution order isn't guaranteed. This creates two potential issues:

1. Unexpected Results: If someone submits two transactions thinking they'll execute in a specific order, they might end up with a different set of validators than intended. This happens because removing validators shifts the remaining keys around (the function swaps the removed key with the last key to maintain array continuity).
2. Transaction Failures: More seriously, someone could intentionally or unintentionally cause others' transactions to fail through front-running. Here's how:
    - Alice submits a transaction to remove validator key at index 8
    - Bob sees this transaction in the mempool
    - Bob quickly submits and gets processed a transaction that removes enough validators so that index 8 no longer exists
    - Alice's transaction will fail with `InvalidIndexOutOfBounds`
#### Impressions
1. Functions that modify shared state (like arrays/sets) where transaction ordering matters:
	- Multiple parties can call the same function
	- State changes affect subsequent operations
	- No mechanism to handle concurrent modifications

### Tools
- [[State_Shared]]
### Refine

- [[1-Business_Logic]]


---
# Medium Risk Findings (xx)

---
## [M-2]  `_getNextValidatorsFromActiveOperators` can be tweaked to find an operator with a better validator pool
----
- **Tags**: #business_logic 
- Number of finders: 5
- Difficulty: Medium
---
### Context
[OperatorsRegistry.1.sol#L417-L420](https://github.com/liquid-collective/liquid-collective-protocol/blob/778d71c5c2b0bb7d430b60df72b4d65173ebee6a/contracts/src/OperatorsRegistry.1.sol#L417-L420)
```
            if (
                operators[idx].funded - operators[idx].stopped
                    < operators[selectedOperatorIndex].funded - operators[selectedOperatorIndex].stopped
            ) {
```
### Description
Assume for an operator:
```
(A, B) = (funded - stopped, limit - funded)
```

The current algorithm finds the first index in the cached operators array with the minimum value for A and tries to gather as many `publicKeys` and `signatures` from this operator's validators up to a max of `_requestedAmount`. But there is also the B cap for this amount. And if B is zero, the function returns early with empty arrays. Even though there could be other approved and non-funded validators from other operators. 

Related: `OperatorsRegistry._getNextValidatorsFromActiveOperators` should not consider `stopped` when picking a validator, `OperatorsRegistry._getNextValidatorsFromActiveOperators` can DOS Alluvial staking if there's an operator with `funded==stopped` and `funded == min(limit, keys)` , `_hasFundableKeys` marks operators that have no more fundable validators as fundable. 

### Recommendation: 
A better search algorithm would be to try to find an operator by minimizing A but also maximizing `B`. But the only linear cost function that would avoid this shortfall above is `-B`. If the minimum of `-B` all operators is `0`, then we can conclude that for all operators `B == 0` and thus `limit == funded` for all operators. So no more approved fundable validators left to select. Note, that we can also look at non-linear cost functions or try to change the picking algorithm in a different direction. 

### Discussion
**Alluvial**: 
It's ok to pick the operator with the least running validators as the best one even if he doesn't have a lot of fundable keys. The check for fundable should be edited to not take stopped into account, that way we can be sure that the cached operator list contains operators with at least 1 fundable key and focus entirely on finding the operator with the lowest active validator count. The end goal of the system is to even the validator count of all operators. Of course limits will be set to similar values but new operators with low validator numbers should be prioritised to catch up with the rest of the operators. 

**Spearbit**: We can also tweak the current algorithm to not just pick the 1st found operator with the lowest nonstopped funded number of validators, but pick one amongst those that also have the highest approved non-funded validators. Basically with my notations from the previous comment, among the operators with the lowest A, pick the one with the highest B. 

We can tweak the search algorithm to `favor/pick` an operator with the highest number of allowed non-funded validators amongst the operators with the lowest number of non-stopped funded validators (As a side effect, this change also has negative net gas on all tests, gas is more saved).

```solidity
uint256 selectedFunded = operators[selectedOperatorIndex].funded; 
uint256 currentFunded = operators[idx].funded; 

uint256 selectedNonStoppedFundedValidators = ( 
	selectedFunded - operators[selectedOperatorIndex].stopped 
); 
uint256 currerntNonStoppedFundedValidators = ( 
	currentFunded - operators[idx].stopped 
); 

bool equalNonStoppedFundedValidators = ( 
	currerntNonStoppedFundedValidators == selectedNonStoppedFundedValidators 
); 

bool hasLessNonStoppedFundedValidators = ( 
	currerntNonStoppedFundedValidators < selectedNonStoppedFundedValidators 
); 

bool hasMoreAllowedNonFundedValidators = ( 
	operators[idx].limit - currentFunded > operators[selectedOperatorIndex].limit - selectedFunded 
); 

if ( 
	hasLessNonStoppedFundedValidators || 
	( 
		equalNonStoppedFundedValidators && hasMoreAllowedNonFundedValidators 
	) 
) { 
	selectedOperatorIndex = idx; 
}
```

**Spearbit**: The picking algorithm has been changed in PR SPEARBIT/3 slightly by adding a `MAX_VALIDATOR_- ATTRIBUTION_PER_ROUND` per round and keeping track of the `picked` number of validators for an operator. Thus the recommendation in this issue is not fully implemented, but the early return issue has been fixed. 

So the new operator picking algorithm is changed to (below the subscripts $f$ refers to `funded`, $p$ `picked`, $s$ `stopped`, $l$ `limit`):
$$
o^*=\underset{o \in \text { Operators }}{\operatorname{argmin}}\left\{o_f+o_p-o_s \mid o_a \wedge\left(o_l>o_f+o_p\right)\right\}
$$
And once the operator $o$ is selected, we pick the number of validation keys based on:
$$
o^*=\underset{o \in \text { Operators }}{\operatorname{argmin}}\left\{o_f+o_p-o_s \mid o_a \wedge\left(o_l>o_f+o_p\right)\right\}
$$
That means for each round we pick maximum `MAX_VALIDATOR_ATTRIBUTION_PER_ROUND = 5` validator keys. There could be also scenarios where each operator $o_l-(o_f+o_p) = 1$, which means at each round we pick exactly 1 key. Now, if `count` is a really big number, we might run into out-of-gas issues. 

One external call that triggers` _pickNextValidatorsFromActiveOperators` is `ConsensusLayerDepositManagerV1.depositToConsensusLayer` which currently does not have any access control modifier. So anyone can call into it. But from the test files, it seems like it might be behind a firewall that only an executor might have permission to call into. Is that true that `depositToConsensusLayer` will always be behind a firewall? In that case, we could move the picking/distribution algorithm off-chain and modify the signature of `depositToConsensusLayer` to look like:
```
function depositToConsensusLayer( 
	uint256[] calldata operatorIndexes, 
	uint256[] calldata validatorCounts 
) external
```

So we provide `depositToConsensusLayer` with an array of operators that we want to fund and also per operator the number of new validator keys that we would like to fund. Note that this would also help with the out-of-gas issue mentioned before. Why is the picking/distribution algorithm currently on-chain? Is it because it is kind of transparent for the operators how their validators get picked? 

**Alluvial**: we would like to keep things that should be transparent for end users inside the contract. Knowing that the validators are properly split between all operators is important as operator diversification is one of the advertised benefits of liquid staking.
### Notes & Impressions

The same as [[2022-12-liquid-collective#[C-3] `OperatorsRegistry._getNextValidatorsFromActiveOperators` can DOS Alluvial staking if there's an operator with `funded==stopped` and `funded == min(limit, keys)`|[C-3] `OperatorsRegistry._getNextValidatorsFromActiveOperators` can DOS Alluvial staking if there's an operator with `funded==stopped` and `funded == min(limit, keys)`]]

### Tools
### Refine

- [[1-Business_Logic]]

---
## [M-8] `OperatorsRegistry._getNextValidatorsFromActiveOperators`should not consider `stopped` when picking a validator 
----
- **Tags**: #business_logic 
- Number of finders: 5
- Difficulty: Medium
---
### Description
Note that
- `limited` → number of validators (already pushed by op) that have been approved by Alluvial and can be selected to be funded. 
- `funded` → number of validators funded. 
- `stopped` → number of validators exited (so that were funded at some point but for any reason they have exited the staking). 
The implementation of the function should favor operators that have the highest number of available validators to be funded. Nevertheless functions favor validators that have stopped value near the funded value. 
Consider the following example:
```
Op at index 0 
name op1 
active true 
limit 10 
funded 5 
stopped 5 
keys 10 

Op at index 1 
name op2 
active true 
limit 10 
funded 0 
stopped 0 
keys 10
```
1) op1 and op2 have 10 validators whitelisted. 
2) op1 at time1 get 5 validators funded. 
3) op1 at time2 get those 5 validators exited, this mean that `op.stopped == 5`. 
In this scenario, those 5 validators would not be used because they are "blacklisted". 
At this point
- op1 have 5 validators that can be funded.
- op2 have 10 validators that can be funded. 
`pickNextValidators` logic should favor operators that have the higher number of available keys (not funded but approved) to be funded. 

If we run `operatorsRegistry.pickNextValidators(5);` the result is this
```
Op at index 0 
name op1 
active true 
limit 10 
funded 10 
stopped 5 
keys 10 

Op at index 1 
name op2 
active true 
limit 10 
funded 0 
stopped 0 
keys 10
```

Op1 gets all the remaining 5 validators funded, the function (from the specification of the logic) should instead have picked Op2. 
Check the Appendix for a test case to reproduce this issue. 

### Recommendation: 
**Alluvial should**:
- reimplement the logic of `Operators. _hasFundableKeys` that should select only active operators with fundable keys without using the `stopped` attribute. 
- reimplement the logic inside the `OperatorsRegistry._getNextValidatorsFromActiveOperators` loop to correctly pick the active operator with the higher number of fundable keys without using the `stopped` attribute. 
### Discussion
Alluvial: Recommendation implemented in SPEARBIT/3. While stopped is not used anymore to gather the list of active and fundable operators, it's still used in the sorting algorithm. As a result, it could happen that operators with `stopped > 0` get picked before operators that have fundable keys but `stopped === 0`. 
Spearbit: Acknowledged.

### Notes & Impressions

The same as [[2022-12-liquid-collective#[C-3] `OperatorsRegistry._getNextValidatorsFromActiveOperators` can DOS Alluvial staking if there's an operator with `funded==stopped` and `funded == min(limit, keys)`]]
### Tools
### Refine
---
## [M-11] `OracleV1.getMemberReportStatus` returns true for non existing oracles
----
- **Tags**: #business_logic 
- Number of finders: 5
- Difficulty: Medium
---
### Context
[Oracle.1.sol#L115-L118](https://github.com/liquid-collective/liquid-collective-protocol/blob/778d71c5c2b0bb7d430b60df72b4d65173ebee6a/contracts/src/Oracle.1.sol#L115-L118)
```
    function getMemberReportStatus(address _oracleMember) external view returns (bool) {
        int256 memberIndex = OracleMembers.indexOf(_oracleMember);
        return ReportsPositions.get(uint256(memberIndex));
    }
```
### Description
`memberIndex` will be equal to `-1` for non-existing oracles, which will cause the mask to be equal to `0`, which will cause the function to return `true` for non-existing oracles. 
[OracleMembers.sol#L35C1-L54C6](https://github.com/liquid-collective/liquid-collective-protocol/blob/778d71c5c2b0bb7d430b60df72b4d65173ebee6a/contracts/src/state/oracle/OracleMembers.sol#L35C1-L54C6)
```
    function indexOf(address memberAddress) internal view returns (int256) {
        bytes32 slot = ORACLE_MEMBERS_SLOT;


        Slot storage r;


        assembly {
            r.slot := slot
        }


        for (uint256 idx = 0; idx < r.value.length;) {
            if (r.value[idx] == memberAddress) {
                return int256(idx);
            }
            unchecked {
                ++idx;
            }
        }


        return int256(-1);
    }
```
### Recommendation: 
Consider changing the function to return false for `memberIndex = -1` but bear in mind that if this function is used directly inside some part of the logic it could allow a not existing member to vote. In this case, the best solution is to always check if the member does not exist by checking if `memberIndex >= 0`. 
The function could otherwise revert if the member does not exist, and return `true/false` if it does exist and has voted/not voted. If this solution is chosen, remember that if integrated directly into the code could create a DOS scenario if not handled correctly. 
For all these reasons, consider properly documenting the behavior of the function and the possible side effects in the natspec comment.
### Notes & Impressions

#### Notes 
The problem arises when the oracle member doesn’t exist in the `OracleMembers` list. In such cases, `indexOf` will return `-1`, as the index for non-existing members is negative.
- `ReportsPositions.get(uint256(memberIndex))` will be called with `memberIndex = -1`.
- The problem is that `uint256(-1)` gets converted to the maximum `uint256` value, which is `2^256 - 1`. This could cause the code to fetch an unintended value or return an incorrect result.
- Specifically, this results in `ReportsPositions.get(0)`, which will evaluate to `true`, because the default value in most cases for boolean storage is `false`, and `false` converted into a mask will likely result in `true`.

### Tools
### Refine

- [[1-Business_Logic]]

---
## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}