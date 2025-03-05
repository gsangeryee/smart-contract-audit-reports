
# 2023-07-nounsdao
---
- Category: #Dexes #yield #cross-chain #rwa #NFT_Marketplace
- Note Create 2024-12-18
- Platform: code4rena
- Report Url: [2023-07-nounsdao](https://code4rena.com/reports/2023-07-nounsdao)
---
# High Risk Findings (xx)

---

{{Copy from High Risk Finding Template.md}}

---

# Medium Risk Findings (xx)

---
## [M-02] If DAO updates `forkEscrow` before `forkThreshold` is reached, the user's escrowed Nounns will be lost

----
- **Tags**: #funds-locked #business_logic 
- Number of finders: 1
- Difficulty: Hard
---
During the escrow period, users can escrow to or withdraw from `forkEscrow` their Nouns.

During the escrow period, proposals can be executed.

```solidity
    function withdrawFromForkEscrow(NounsDAOStorageV3.StorageV3 storage ds, uint256[] calldata tokenIds) external {
        if (isForkPeriodActive(ds)) revert ForkPeriodActive();

        INounsDAOForkEscrow forkEscrow = ds.forkEscrow;
        forkEscrow.returnTokensToOwner(msg.sender, tokenIds);

        emit WithdrawFromForkEscrow(forkEscrow.forkId(), msg.sender, tokenIds);
    }
```

Since` withdrawFromForkEscrow` will only call the `returnTokensToOwner` function of `ds.forkEscrow`, and `returnTokensToOwner` is only allowed to be called by DAO.

If, during the escrow period, `ds.forkEscrow` is changed by the proposal's call to `_setForkEscrow`, then the user's escrowed Nouns will not be withdrawn by `withdrawFromForkEscrow`.

```
    function returnTokensToOwner(address owner, uint256[] calldata tokenIds) external onlyDAO {
        for (uint256 i = 0; i < tokenIds.length; i++) {
            if (currentOwnerOf(tokenIds[i]) != owner) revert NotOwner();

            nounsToken.transferFrom(address(this), owner, tokenIds[i]);
            escrowedTokensByForkId[forkId][tokenIds[i]] = address(0);
        }

        numTokensInEscrow -= tokenIds.length;
    }
```

Consider that some Nouners is voting on a proposal that would change `ds.forkEscrow`.<br>  
There are some escrowed Nouns in `forkEscrow` (some Nouners may choose to always escrow their Nouns to avoid missing fork).<br>  
The proposal is executed, `ds.forkEscrow` is updated, and the escrowed Nouns cannot be withdrawn.

### Proof of Concept

[NounsDAOV3Fork.sol#L95-L102](https://github.com/nounsDAO/nouns-monorepo/blob/718211e063d511eeda1084710f6a682955e80dcb/packages/nouns-contracts/contracts/governance/fork/NounsDAOV3Fork.sol#L95-L102)
```solidity
    function withdrawFromForkEscrow(NounsDAOStorageV3.StorageV3 storage ds, uint256[] calldata tokenIds) external {
        if (isForkPeriodActive(ds)) revert ForkPeriodActive();


        INounsDAOForkEscrow forkEscrow = ds.forkEscrow;
        forkEscrow.returnTokensToOwner(msg.sender, tokenIds);


        emit WithdrawFromForkEscrow(forkEscrow.forkId(), msg.sender, tokenIds);
    }
```

[NounsDAOForkEscrow.sol#L116-L125](https://github.com/nounsDAO/nouns-monorepo/blob/718211e063d511eeda1084710f6a682955e80dcb/packages/nouns-contracts/contracts/governance/fork/NounsDAOForkEscrow.sol#L116-L125)
```solidity
    function returnTokensToOwner(address owner, uint256[] calldata tokenIds) external onlyDAO {
        for (uint256 i = 0; i < tokenIds.length; i++) {
            if (currentOwnerOf(tokenIds[i]) != owner) revert NotOwner();


            nounsToken.transferFrom(address(this), owner, tokenIds[i]);
            escrowedTokensByForkId[forkId][tokenIds[i]] = address(0);
        }


        numTokensInEscrow -= tokenIds.length;
    }
```

[NounsDAOV3Admin.sol#L527-L531](https://github.com/nounsDAO/nouns-monorepo/blob/718211e063d511eeda1084710f6a682955e80dcb/packages/nouns-contracts/contracts/governance/NounsDAOV3Admin.sol#L527-L531)
```solidity
    function _setForkEscrow(NounsDAOStorageV3.StorageV3 storage ds, address newForkEscrow) external onlyAdmin(ds) {
        emit ForkEscrowSet(address(ds.forkEscrow), newForkEscrow);

        ds.forkEscrow = INounsDAOForkEscrow(newForkEscrow);
    }
```
### Recommended Mitigation Steps

Consider allowing the user to call `forkEscrow.returnTokensToOwner` directly to withdraw escrowed Nouns, and need to move `isForkPeriodActive` from `withdrawFromForkEscrow` to `returnTokensToOwner`.
### Notes & Impressions

#### Notes 

##### The Critical Sequence of Events

1. **Initial State**
   - Users have tokens escrowed in the ORIGINAL fork escrow contract
   - The `returnTokensToOwner()` function in this contract is marked with `onlyDAO`

2. **After Address Update**
   ```solidity
   function _setForkEscrow(NounsDAOStorageV3.StorageV3 storage ds, address newForkEscrow) external onlyAdmin(ds) {
       ds.forkEscrow = INounsDAOForkEscrow(newForkEscrow);
   }
   ```
   - `ds.forkEscrow` now points to a NEW contract address
   - The NEW contract is EMPTY (no tokens)
   - The ORIGINAL contract still holds users' tokens

3. **Withdrawal Attempt**
   ```solidity
   function withdrawFromForkEscrow(NounsDAOStorageV3.StorageV3 storage ds, uint256[] calldata tokenIds) external {
       INounsDAOForkEscrow forkEscrow = ds.forkEscrow;  // NEW address
       forkEscrow.returnTokensToOwner(msg.sender, tokenIds);
   }
   ```
   - Users call `withdrawFromForkEscrow()`
   - This attempts to call `returnTokensToOwner()` on the NEW contract
   - But the tokens are still in the ORIGINAL contract

##### The Core Problem

The critical issue is NOT about DAO permissions, but about token location:
- The NEW contract doesn't have the tokens
- Users can't directly interact with the ORIGINAL contract to retrieve tokens
- The `onlyDAO` modifier prevents users from calling `returnTokensToOwner()`

##### A Real-World Analogy

Imagine:
- You have money in Bank A's safe deposit box
- The bank decides to change its branch location
- The new branch (Bank B) doesn't know about your old safe deposit box
- Only the bank manager can transfer items between branches
- You, as the account holder, can't directly retrieve your items

##### Why Can't Users Call `onlyDAO`?

The `onlyDAO` modifier explicitly restricts the function to be called only by the DAO:
```solidity
modifier onlyDAO() {
    if (msg.sender != dao) revert Unauthorized();
    _;
}
```

This means ONLY the DAO contract address can call `returnTokensToOwner()`, preventing users from directly retrieving their tokens from the original contract.

#### Impressions
- It's so difficult.
- Rare scenario
- Anticipate edge cases in permission and ownership transfers

### Refine
- [[1-Business_Logic]]

---
## [M-03] `NounsDAOV3Proposals.cancel()` should allow to cancel the proposal of the Expired state

----
- **Tags**: #business_logic #edge-case 
- Number of finders: 1
- Difficulty: Medium
---
### Detail

`cancel()` does not allow to cancel proposals in the final states `Canceled/Defeated/Expired/Executed/Vetoed`.

```solidity
    function cancel(NounsDAOStorageV3.StorageV3 storage ds, uint256 proposalId) external {
        NounsDAOStorageV3.ProposalState proposalState = stateInternal(ds, proposalId);
        if (
            proposalState == NounsDAOStorageV3.ProposalState.Canceled ||
            proposalState == NounsDAOStorageV3.ProposalState.Defeated ||
            proposalState == NounsDAOStorageV3.ProposalState.Expired ||
            proposalState == NounsDAOStorageV3.ProposalState.Executed ||
            proposalState == NounsDAOStorageV3.ProposalState.Vetoed
        ) {
            revert CantCancelProposalAtFinalState();
        }
```

The `Canceled/Executed/Vetoed` states are final because they cannot be changed once they are set.

The `Defeated` state is also a final state because no new votes will be cast (`stateInternal()` may return Defeated only if the `objectionPeriodEndBlock` is passed).

But the Expired state depends on the `GRACE_PERIOD` of the `timelock`, and `GRACE_PERIOD` may be changed due to upgrades. Once the `GRACE_PERIOD` of the `timelock` is changed, the state of the proposal may also be changed, so Expired is not the final state.

```solidity
        } else if (block.timestamp >= proposal.eta + getProposalTimelock(ds, proposal).GRACE_PERIOD()) {
            return NounsDAOStorageV3.ProposalState.Expired;
        } else {
            return NounsDAOStorageV3.ProposalState.Queued;
```

Consider the following scenario:

- Alice submits proposal A to stake 20,000 ETH to a DEFI protocol, and it is successfully passed, but it cannot be executed because there is now only 15,000 ETH in the `timelock` (consumed by other proposals), and then proposal A expires.
    
- The DEFI protocol has been hacked or rug-pulled.
    
- Now proposal B is about to be executed to upgrade the `timelock` and extend `GRACE_PERIOD` (e.g., `GRACE_PERIOD` is extended by 7 days from V1 to V2).
    
- Alice wants to cancel Proposal A, but it cannot be canceled because it is in Expired state.
    
- Proposal B is executed, causing Proposal A to change from Expired to Queued.
    
- The malicious user sends 5000 ETH to the `timelock` and immediately executes Proposal A to send 20000 ETH to the hacked protocol.
- 
### Proof of Concept

```solidity
    function cancel(NounsDAOStorageV3.StorageV3 storage ds, uint256 proposalId) external {
        NounsDAOStorageV3.ProposalState proposalState = stateInternal(ds, proposalId);
        if (
            proposalState == NounsDAOStorageV3.ProposalState.Canceled ||
            proposalState == NounsDAOStorageV3.ProposalState.Defeated ||
            proposalState == NounsDAOStorageV3.ProposalState.Expired ||
            proposalState == NounsDAOStorageV3.ProposalState.Executed ||
            proposalState == NounsDAOStorageV3.ProposalState.Vetoed
        ) {
            revert CantCancelProposalAtFinalState();
        }
```
### Recommended Mitigation

Consider adding a proposal expiration time field in the Proposal structure.

```solidity
    function queue(NounsDAOStorageV3.StorageV3 storage ds, uint256 proposalId) external {
        require(
            stateInternal(ds, proposalId) == NounsDAOStorageV3.ProposalState.Succeeded,
            'NounsDAO::queue: proposal can only be queued if it is succeeded'
        );
        NounsDAOStorageV3.Proposal storage proposal = ds._proposals[proposalId];
        INounsDAOExecutor timelock = getProposalTimelock(ds, proposal);
        uint256 eta = block.timestamp + timelock.delay();
        for (uint256 i = 0; i < proposal.targets.length; i++) {
            queueOrRevertInternal(
                timelock,
                proposal.targets[i],
                proposal.values[i],
                proposal.signatures[i],
                proposal.calldatas[i],
                eta
            );
        }
        proposal.eta = eta;
+       proposal.exp = eta + timelock.GRACE_PERIOD();
...
-       } else if (block.timestamp >= proposal.eta + getProposalTimelock(ds, proposal).GRACE_PERIOD()) {
+       } else if (block.timestamp >= proposal.exp) {
            return NounsDAOStorageV3.ProposalState.Expired;
```

###  Discussion
**[eladmallel (Nouns DAO) acknowledged and commented](https://github.com/code-423n4/2023-07-nounsdao-findings/issues/55#issuecomment-1644570812):**

> Agree, it's possible due to a change in executor's grace period to move from Expired back to Queued.<br>  
> However, since a grace period change is a rare event, we think this is very low priority and we won't fix.

**[gzeon (judge) decreased severity to Low/Non-Critical](https://github.com/code-423n4/2023-07-nounsdao-findings/issues/55#issuecomment-1650646474)**

**[eladmallel (Nouns DAO) commented](https://github.com/code-423n4/2023-07-nounsdao-findings/issues/55#issuecomment-1650607865):**

> We think it would be great to include this issue in the report (at medium severity).

**[gzeon (judge) commented](https://github.com/code-423n4/2023-07-nounsdao-findings/issues/55#issuecomment-1650646474):**

> @eladmallel - Changing the `GRACE_PERIOD` is an admin change, which besides misconfiguration is out-of-scope, it is as you described is a rare event. Having a malicious proposal which is passed that got expired is also a rare event. Having a changed `GRACE_PERIOD` that just long enough to make such a malicious proposal become queued is a very rare event, assuming governance is not completely compromised already.
> 
> That said, I am ok with this being Medium risk since this is clearly in scope + can be Medium risk with some assumption (tho extreme imo but is subjective), and I would recommend for a fix accordingly. Please let me know if that's what you want, thanks!

**[eladmallel (Nouns DAO) commented](https://github.com/code-423n4/2023-07-nounsdao-findings/issues/55#issuecomment-1650792548):**

> Thank you @gzeon.<br>  
> We all agree the odds of the risk materializing is low, we just felt like this was a nice find, and honestly mostly motivated by wanting the warden who found this to have a win :)
> 
> It's not a deal breaker for us if it's in the report or not, just wanted to express our preference.
> 
> Thank you for sharing more of your thinking, it's helpful!

**[cccz (warden) commented](https://github.com/code-423n4/2023-07-nounsdao-findings/issues/55#issuecomment-1650936160):**

> Low Likelihood + High Severity is generally considered Medium, which is an edge case that fits the medium risk.<br>  
> Another thing I would say is that the proposal doesn't need to be malicious, as I said in the attack scenario where the proposal is normal but expires due to inability to execute for other reasons ( contract balance insufficient, etc.).
> 
> > _Changing the `GRACE_PERIOD` is an admin change, which besides misconfiguration is out-of-scope, it is as you described is a rare event. Having a malicious proposal which is passed that got expired is also a rare event. Having a changed `GRACE_PERIOD` that just long enough to make such a malicious proposal become queued is a very rare event, assuming governance is not completely compromised already._

**[gzeon (judge) increased severity to Medium and commented](https://github.com/code-423n4/2023-07-nounsdao-findings/issues/55#issuecomment-1651037458):**

> @cccz - True, but this is also marginally out-of-scope since an admin action is required, and one may argue it is a misconfiguration if you increase `GRACE_PERIOD` so much that it revive some old passed buggy proposal.
> 
> But given this is marginal and on sponsor's recommendation, I will upgrade this to Medium.

### Notes & Impressions

#### Notes 
- The code prevents cancellation of proposals in "final" states, including Expired
- A proposal's Expired state is determined by: execution time + timelock's GRACE_PERIOD
- Since GRACE_PERIOD can be modified through governance, an Expired proposal can revert to Queued state
- This creates a vulnerability where dangerous expired proposals could become executable again without the ability to cancel them
#### Impressions
This issue seems a bit difficult to find.

To find similar business logic issues, focus on these key areas:

1. State transitions - Map out all possible state changes and identify what triggers them. Look for states assumed to be "final" but that could change.
2. Governance parameters - Any parameter that can be modified through governance can impact system behavior. Review how parameter changes affect other parts of the system.
3. Time-based conditions - Examine logic depending on time periods, deadlines or delays. These often create edge cases.
4. One-way assumptions - Question any assumption that a state or condition is permanent/irreversible.
5. Interaction patterns - Consider how different system functions might interact in unexpected ways over time.

## Tools:
- [[State_Transition_Maps]]
### Refine
- [[1-Business_Logic]]

---
---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}