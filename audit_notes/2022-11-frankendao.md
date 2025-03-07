# 2022-11-FrankenDAO
---
- Category: #liquid_staking #Dexes #yield #Launchpad #payments
- Note Create 2025-03-07
- Platform: sherlock
- Report Url: [2022-11-FrankenDAO](https://audits.sherlock.xyz/contests/18/report)
---
# Critical & High Risk Findings (xx)

---

{{Copy from High Risk Finding Template.md}}

---

# Medium Risk Findings (xx)

---
## [M-06] Staking `changeStakeTime` and `changeStakeAmount` are problematic given current staking design
----
- **Tags**: #business_logic 
- Number of finders: 1
- Difficulty: Hard
---
### Summary

Staking `changeStakeTime` and `changeStakeAmount` allow the locking bonus to be modified. Any change to this value will cause voting imbalance in the system. If changes result in a higher total bonus then existing stakers will be given a permanent advantage over new stakers. If the bonus is increased then existing stakers will be at a disadvantage because they will be locked and unable to realize the new staking bonus.
### Detail

```solidity
function _stakeToken(uint _tokenId, uint _unlockTime) internal returns (uint) {
	if (_unlockTime > 0) {
	    unlockTime[_tokenId] = _unlockTime;
	    uint fullStakedTimeBonus = ((_unlockTime - block.timestamp) * stakingSettings.maxStakeBonusAmount) / stakingSettings.maxStakeBonusTime;
		stakedTimeBonus[_tokenId] = _tokenId < 10000 ? fullStakedTimeBonus : fullStakedTimeBonus / 2;
  }
```

When a token is staked their `stakeTimeBonus` is stored. This means that any changes to `stakingSettings.maxStakeBonusAmount` or `stakingSettings.maxStakeBonusTime` won't affect tokens that are already stored. Storing the value is essential to prevent changes to the values causing major damage to the voting, but it leads to other more subtle issue when it is changed that will put either existing or new stakers at a disadvantage.

Example: 
- User A stake when `maxStakeBonusAmount = 10` and stake long enough to get the entire bonus. Now `maxStakeBonusAmount` is changed to 20. 
- User A is unable to unstake their token right away because it is locked. They are now at a disadvantage because other users can now stake and get a bonus of 20 while they are stuck with only a bonus of 10. Now `maxStakeBonusAmount` is changed to 5. 
- User A now has an advantage because other users can now only stake for a bonus of 5. If User A never unstakes then they will forever have that advantage over new users.
### Impact

Voting power becomes skewed for users when Staking `changeStakeTime` and `changeStakeAmount` are used.
### Recommended Mitigation

I recommend implementing a poke function that can be called by any user on any user. This function should loop through all tokens (or the tokens specified) and recalculate their voting power based on current multipliers, allowing all users to be normalized to prevent any abuse.
### Discussion

**zobront**:

This is the intended behavior. Staking windows will be relatively short (~1 month) and bonuses will change only by governance vote. We accept that there may be short periods where a user is locked in a suboptimal spot, but they can unstake and restake when the period is over.

**0x00052**:

Escalate for 1 USDC

I think this should be considered valid. It won't just be for a small amount of time if the staking amount is lowered. In this case, all users who staked beforehand will have a permanent advantage over other users. Due to the permanent imbalance lowering it would cause in the voting power of users, I think that medium is appropriate.

**sherlock-admin**:

> Escalate for 1 USDC
> 
> I think this should be considered valid. It won't just be for a small amount of time if the staking amount is lowered. In this case, all users who staked beforehand will have a permanent advantage over other users. Due to the permanent imbalance lowering it would cause in the voting power of users, I think that medium is appropriate.

You've created a valid escalation for 1 USDC!

To remove the escalation from consideration: Delete your comment. To change the amount you've staked on this escalation: Edit your comment **(do not create a new comment)**.

You may delete or edit your escalation comment anytime before the 48-hour escalation window closes. After that, the escalation becomes final.

**zobront**:

I can see the argument here. We don't want to change it and believe it's fine as is, but it may be a valid Medium.

**Evert0x**:

Escalation accepted

**sherlock-admin**:

> Escalation accepted

This issue's escalations have been accepted!

Contestants' payouts and scores will be updated according to the changes made on this issue.

### Notes & Impressions

#### Notes 
The smart contract allows users to stake their tokens for a period of time. As a reward for locking up their tokens longer, users receive a bonus to their voting power. This bonus is calculated based on two key parameters:

- `maxStakeBonusAmount`: How much extra voting power you can get
- `maxStakeBonusTime`: How long you need to stake to get the maximum bonus

The Problem
1. If the maximum bonus is **increased** after users have staked:
    - Existing stakers are at a disadvantage because they're locked into their lower bonus
    - New stakers get higher voting power for the same lock period
    - Existing stakers must wait until their lock period ends to unstake and restake to get the new higher bonus
2. If the maximum bonus is **decreased** after users have staked:
    - Existing stakers have a permanent advantage over new stakers
    - They keep their higher bonus value forever as long as they remain staked
    - This creates a long-term imbalance in voting power within the system
#### Impressions

*When a protocol stores calculated values based on global parameters instead of calculating them on-demand, parameter changes can create permanent inequities between users.*

### Tools
### Refine

- [[1-Business_Logic]]

---
## [M-07] `castVote` can be called by anyone even those without votes
----
- **Tags**: #business_logic #vote
- Number of finders: 3
- Difficulty: Medium
---
### Summary

Governance `castVote` can be called by anyone, even users that don't have any votes. Since the voting refund is per address, an adversary could use a large number of addresses to vote with zero votes to drain the vault.
### Detail

```solidity
function _castVote(address _voter, uint256 _proposalId, uint8 _support) internal returns (uint) {
    // Only Active proposals can be voted on
    if (state(_proposalId) != ProposalState.Active) revert InvalidStatus();
    
    // Only valid values for _support are 0 (against), 1 (for), and 2 (abstain)
    if (_support > 2) revert InvalidInput();

    Proposal storage proposal = proposals[_proposalId];

    // If the voter has already voted, revert        
    Receipt storage receipt = proposal.receipts[_voter];
    if (receipt.hasVoted) revert AlreadyVoted();

    // Calculate the number of votes a user is able to cast
    // This takes into account delegation and community voting power
    uint24 votes = (staking.getVotes(_voter)).toUint24();

    // Update the proposal's total voting records based on the votes
    if (_support == 0) {
        proposal.againstVotes = proposal.againstVotes + votes;
    } else if (_support == 1) {
        proposal.forVotes = proposal.forVotes + votes;
    } else if (_support == 2) {
        proposal.abstainVotes = proposal.abstainVotes + votes;
    }

    // Update the user's receipt for this proposal
    receipt.hasVoted = true;
    receipt.support = _support;
    receipt.votes = votes;

    // Make these updates after the vote so it doesn't impact voting power for this vote.
    ++totalCommunityScoreData.votes;

    // We can update the total community voting power with no check because if you can vote, 
    // it means you have votes so you haven't delegated.
    ++userCommunityScoreData[_voter].votes;

    return votes;
}
```

Nowhere in the flow of voting does the function revert if the user calling it doesn't actually have any votes. staking `getVotes` won't revert under any circumstances. Governance `_castVote` only reverts if 
1. the proposal isn't active
2. support > 2 or 
3. if the user has already voted. The result is that any user can vote even if they don't have any votes, allowing users to maliciously burn vault funds by voting and claiming the vote refund.
### Impact

Vault can be drained maliciously by users with no votes
### Recommended Mitigation

Governance `_castVote` should revert if `msg.sender` doesn't have any votes:

```solidity
    // Calculate the number of votes a user is able to cast
    // This takes into account delegation and community voting power
    uint24 votes = (staking.getVotes(_voter)).toUint24();

+   if (votes == 0) revert NoVotes();

    // Update the proposal's total voting records based on the votes
    if (_support == 0) {
        proposal.againstVotes = proposal.againstVotes + votes;
    } else if (_support == 1) {
        proposal.forVotes = proposal.forVotes + votes;
    } else if (_support == 2) {
        proposal.abstainVotes = proposal.abstainVotes + votes;
    }
```

### Discussion

### Notes & Impressions

#### Notes 

The smart contract allows users with zero voting power to cast votes and receive refunds, enabling an attacker to create multiple addresses and drain the vault through mass zero-vote submissions.

### Tools
### Refine

- [[1-Business_Logic]]
- [[24-Vote]]

---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}