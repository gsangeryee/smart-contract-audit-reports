# 2022-11-Redacted Cartel
---
- Category: #Dexes #CDP #yield #cross-chain #staking_pool 
- Note Create 2025-03-06
- Platform: code4rena
- Report Url: [2022-11-redactedcartel](https://code4rena.com/reports/2022-11-redactedcartel)
---
# Critical & High Risk Findings (xx)

---
## [H-06] fee loss in `AutoPxGmx` and `AutoPxGlp` and reward loss in `AutoPxGlp` by calling `PirexRewards.claim(pxGmx/pxGpl, AutoPx*)` directly which transfers rewards to `AutoPx`* pool without compound logic get executed and fee calculation logic and `pxGmx` wouldn't be executed for those rewards
----
- **Tags**: #business_logic #pre/post_balance #financial_bypass 
- Number of finders: 2
- Difficulty: Medium
---
### Impact

Function `compound()` in `AutoPxGmx` and `AutoPxGlp` contracts is for compounding `pxGLP` (and additionally `pxGMX`) rewards. it works by calling `PirexGmx.claim(px*, this)` to collect the rewards of the vault and then swap the received amount (to calculate the reward, contract save the balance of a contract in that reward token before and after the call to the `claim()` and by subtracting them finds the received reward amount) and deposit them in `PirexGmx` again for compounding and in doing so it calculates fee based on what it received and in `AutoPxGlp` case it calculates `pxGMX` rewards too based on the extra amount contract receives during the execution of `claim()`. But attacker can call `PirexGmx.claim(px*, PirexGlp)` directly and make `PirexGmx` contract to transfer (`gmxBaseReward` and `pxGmx`) rewards to `AutoPxGlp` and in this case the logics of fee calculation and reward calculation in `compound()` function won't get executed and contract won't get it's fee from rewards and users won't get their `pxGmx` reward. So this bug would cause fee loss in `AutoPxGmx` and `AutoPxGlp` for contract and `pxGmx`'s reward loss for users in `AutoPxGlp`.
### Proof of Concept

The bug in `AutoPxGmx` is similar to `AutoPxGlp`, so we only give Proof of Concept for `AutoPxGlp`.

This is `compound()` function code in `AutoPxGlp` contract:

```solidity
    function compound(
        uint256 minUsdg,
        uint256 minGlp,
        bool optOutIncentive
    )
        public
        returns (
            uint256 gmxBaseRewardAmountIn,
            uint256 pxGmxAmountOut,
            uint256 pxGlpAmountOut,
            uint256 totalPxGlpFee,
            uint256 totalPxGmxFee,
            uint256 pxGlpIncentive,
            uint256 pxGmxIncentive
        )
    {
        if (minUsdg == 0) revert InvalidParam();
        if (minGlp == 0) revert InvalidParam();

        uint256 preClaimTotalAssets = asset.balanceOf(address(this));
        uint256 preClaimPxGmxAmount = pxGmx.balanceOf(address(this));

        PirexRewards(rewardsModule).claim(asset, address(this));
        PirexRewards(rewardsModule).claim(pxGmx, address(this));

        // Track the amount of rewards received
        gmxBaseRewardAmountIn = gmxBaseReward.balanceOf(address(this));

        if (gmxBaseRewardAmountIn != 0) {
            // Deposit received rewards for pxGLP
            (, pxGlpAmountOut, ) = PirexGmx(platform).depositGlp(
                address(gmxBaseReward),
                gmxBaseRewardAmountIn,
                minUsdg,
                minGlp,
                address(this)
            );
        }

        // Distribute fees if the amount of vault assets increased
        uint256 newAssets = totalAssets() - preClaimTotalAssets;
        if (newAssets != 0) {
            totalPxGlpFee = (newAssets * platformFee) / FEE_DENOMINATOR;
            pxGlpIncentive = optOutIncentive
                ? 0
                : (totalPxGlpFee * compoundIncentive) / FEE_DENOMINATOR;

            if (pxGlpIncentive != 0)
                asset.safeTransfer(msg.sender, pxGlpIncentive);

            asset.safeTransfer(owner, totalPxGlpFee - pxGlpIncentive);
        }

        // Track the amount of pxGMX received
        pxGmxAmountOut = pxGmx.balanceOf(address(this)) - preClaimPxGmxAmount;

        if (pxGmxAmountOut != 0) {
            // Calculate and distribute pxGMX fees if the amount of pxGMX increased
            totalPxGmxFee = (pxGmxAmountOut * platformFee) / FEE_DENOMINATOR;
            pxGmxIncentive = optOutIncentive
                ? 0
                : (totalPxGmxFee * compoundIncentive) / FEE_DENOMINATOR;

            if (pxGmxIncentive != 0)
                pxGmx.safeTransfer(msg.sender, pxGmxIncentive);

            pxGmx.safeTransfer(owner, totalPxGmxFee - pxGmxIncentive);

            // Update the pxGmx reward accrual
            _harvest(pxGmxAmountOut - totalPxGmxFee);
        } else {
            // Required to keep the globalState up-to-date
            _globalAccrue();
        }

        emit Compounded(
            msg.sender,
            minGlp,
            gmxBaseRewardAmountIn,
            pxGmxAmountOut,
            pxGlpAmountOut,
            totalPxGlpFee,
            totalPxGmxFee,
            pxGlpIncentive,
            pxGmxIncentive
        );
    }
```

As you can see contract collects rewards by calling `PirexRewards.claim()` and in the line `uint256 newAssets = totalAssets() - preClaimTotalAssets;` contract calculates the received amount of rewards (by subtracting the balance after and before reward claim) and then calculates fee based on this amount `totalPxGlpFee = (newAssets * platformFee) / FEE_DENOMINATOR;` and then sends the fee in the line `asset.safeTransfer(owner, totalPxGlpFee - pxGlpIncentive)` for `owner`.

The logic for `pxGmx` rewards are the same. As you can see the calculation of the fee is based on the rewards received, and there is no other logic in the contract to calculate and transfer the fee of protocol. So if `AutoPxGpl` receives rewards without `compound()` getting called then for those rewards fee won't be calculated and transferred and protocol would lose it's fee.

In the line `_harvest(pxGmxAmountOut - totalPxGmxFee)` contract calls `_harvest()` function to update the `pxGmx` reward accrual and there is no call to `_harvest()` in any other place and this is the only place where `pxGmx` reward accrual gets updated. The contract uses `pxGmxAmountOut` which is the amount of `gmx` contract received during the call (code calculates it by subtracting the balance after and before reward claim: `pxGmxAmountOut = pxGmx.balanceOf(address(this)) - preClaimPxGmxAmount;`) so contract only handles accrual rewards in this function call and if some `pxGmx` rewards claimed for contract without `compund()` logic execution then those rewards won't be used in `_harvest()` and `_globalAccrue()` calculation and users won't receive those rewards.

As mentioned attacker can call `PirexRewards.claim(pxGmx, AutoPxGpl)` directly and make `PirexRewads` contract to transfer `AutoPxGpl` rewards. This is `claim()` code in `PirexRewards`:

```solidity
    function claim(ERC20 producerToken, address user) external {
        if (address(producerToken) == address(0)) revert ZeroAddress();
        if (user == address(0)) revert ZeroAddress();

        harvest();
        userAccrue(producerToken, user);

        ProducerToken storage p = producerTokens[producerToken];
        uint256 globalRewards = p.globalState.rewards;
        uint256 userRewards = p.userStates[user].rewards;

        // Claim should be skipped and not reverted on zero global/user reward
        if (globalRewards != 0 && userRewards != 0) {
            ERC20[] memory rewardTokens = p.rewardTokens;
            uint256 rLen = rewardTokens.length;

            // Update global and user reward states to reflect the claim
            p.globalState.rewards = globalRewards - userRewards;
            p.userStates[user].rewards = 0;

            emit Claim(producerToken, user);

            // Transfer the proportionate reward token amounts to the recipient
            for (uint256 i; i < rLen; ++i) {
                ERC20 rewardToken = rewardTokens[i];
                address rewardRecipient = p.rewardRecipients[user][rewardToken];
                address recipient = rewardRecipient != address(0)
                    ? rewardRecipient
                    : user;
                uint256 rewardState = p.rewardStates[rewardToken];
                uint256 amount = (rewardState * userRewards) / globalRewards;

                if (amount != 0) {
                    // Update reward state (i.e. amount) to reflect reward tokens transferred out
                    p.rewardStates[rewardToken] = rewardState - amount;

                    producer.claimUserReward(
                        address(rewardToken),
                        amount,
                        recipient
                    );
                }
            }
        }
    }
```

As you can see it can be called by anyone for any user. So to perform this attack, attacker would perform these steps:

1. Suppose `AutoPxGpl` has pending rewards, for example 100 `pxGmx` and 100 `weth`.
2. Attacker would call `PirexRewards.claim(pxGmx, AutoPxGpl)` and `PirexRewards.claim(pxGpl, AutoPxGpl)` and `PirexRewards` contract would calculate and claim and transfer `pxGmx` rewards and `weth` rewards of `AutoPxGpl` address.
3. Then `AutoPxGpl` has no pending rewards but the balance of `pxGmx` and `weth` of contract has been increased.
4. If anyone calls `AutoPxGpl.compound()` because there is no pending rewards contract would receive no rewards and because contract only calculates fee and rewards based on received rewards during the call to `compound()` so contract wouldn't calculate any fee or reward accrual for those 1000 `pxGmx` and `weth` rewards.
5. `owner` of `AutoPxGpl` would lose his fee for those rewards and users of `AutoPxGpl` would lose their claims for those 1000 `pxGmx` rewards (because the calculation for them didn't happen).

This bug is because of the fact that the only logic handling rewards is in `compound()` function which is only handling receiving rewards by calling `claim()` during the call to `compound()` but it's possible to call `claim()` directly (`PirexRewards` contract allows this) and `AutoPxGpl` won't get notified about this new rewards and the related logics won't get executed.

### Recommended Mitigation

Contract should keep track of it's previous balance when `compound()` get executed and update this balance in deposits and withdraws and claims so it can detect rewards that directly transferred to contract without call to `compound()`.

### Discussion

### Notes

##### The Core Issue

The vulnerability allows an attacker to bypass the normal reward claiming process, causing:

1. Loss of protocol fees that should go to the contract owner
2. Loss of `pxGmx` rewards that should go to users of the `AutoPxGlp` contract

##### How the System Should Work

The contracts are designed with a `compound()` function that:

1. Claims rewards from the `PirexRewards` contract
2. Calculates the difference in token balances before and after claiming
3. Takes protocol fees based on these rewards
4. In `AutoPxGlp`, processes `pxGmx` rewards for users
5. Updates internal accounting of rewards

##### The Vulnerability

The problem arises because:

1. The `PirexRewards.claim()` function can be called by anyone for any user
2. An attacker can directly call `PirexRewards.claim(pxGmx/pxGlp, AutoPx*)`
3. This transfers rewards directly to the `AutoPx*` contracts
4. When this happens, the `compound()` function never executes
5. Without `compound()` executing, fee calculations and reward distributions don't happen

##### Attack Scenario

Here's how an attack would work:

1. The `AutoPxGlp` contract has pending rewards (e.g., 100 `pxGmx` and 100 `weth`)
2. An attacker calls `PirexRewards.claim(pxGmx, AutoPxGlp)` and `PirexRewards.claim(pxGlp, AutoPxGlp)`
3. The `PirexRewards` contract transfers these rewards to `AutoPxGlp`
4. The `AutoPxGlp` contract now has no pending rewards but increased token balances
5. When someone later calls `AutoPxGlp.compound()`, it won't detect any new rewards
6. No fees are calculated or sent to the owner
7. No `pxGmx` rewards are distributed to users

##### Root Cause

The vulnerability exists because:

1. The contract only calculates rewards and fees based on balance changes during the `compound()` call
2. There's no protection against direct claiming of rewards
3. The contract has no way to track rewards that were claimed outside the normal process

### Tools
- [[Financial_Bypass]]
### Refine

- [[1-Business_Logic]]
- [[28-Pre_Post_Balance]]

---

---

# Medium Risk Findings (xx)

---
## [M-12] Reward tokens mismanagement can cause users losing rewards
----
- **Tags**: #business_logic 
- Number of finders: 9
- Difficulty: Easy
---
### Impact

A user (which can also be one of the `autocompounding` contracts, `AutoPxGlp` or `AutoPxGmx`) can lose a reward as a result of reward tokens mismanagement by the owner.
### Proof of Concept

The protocol defines a short list of reward tokens that are hard coded in the `claimRewards` function of the `PirexGmx` contract
[PirexGmx.sol#L756-L759](https://github.com/code-423n4/2022-11-redactedcartel/blob/03b71a8d395c02324cb9fdaf92401357da5b19d1/src/PirexGmx.sol#L756-L759)
```solidity
rewardTokens[0] = gmxBaseReward;
rewardTokens[1] = gmxBaseReward;
rewardTokens[2] = ERC20(pxGmx); // esGMX rewards distributed as pxGMX
rewardTokens[3] = ERC20(pxGmx);
```

The fact that these addresses are hard coded means that no other reward tokens will be supported by the protocol. However, the `PirexRewards` contract maintains a different list of reward tokens, one per producer token
[PirexRewards.sol#L19-L31](https://github.com/code-423n4/2022-11-redactedcartel/blob/03b71a8d395c02324cb9fdaf92401357da5b19d1/src/PirexRewards.sol#L19-L31)
```solidity
struct ProducerToken {
    ERC20[] rewardTokens;
    GlobalState globalState;
    mapping(address => UserState) userStates;
    mapping(ERC20 => uint256) rewardStates;
    mapping(address => mapping(ERC20 => address)) rewardRecipients;
}

// Producer tokens mapped to their data
mapping(ERC20 => ProducerToken) public producerTokens;
```

These reward tokens can be added (`addRewardToken`) or removed (`removeRewardToken`) by the owner, which creates the possibility of mismanagement:

1. The owner can mistakenly remove one of the reward tokens hard coded in the `PirexGmx` contract;
2. The owner can add reward tokens that are not supported by the `PirexGmx` contract.

[addRewardToken](https://github.com/code-423n4/2022-11-redactedcartel/blob/03b71a8d395c02324cb9fdaf92401357da5b19d1/src/PirexRewards.sol#L151-L172)
```solidity
    function addRewardToken(ERC20 producerToken, ERC20 rewardToken)
        external
        onlyOwner
    {
        if (address(producerToken) == address(0)) revert ZeroAddress();
        if (address(rewardToken) == address(0)) revert ZeroAddress();


        // Check if the token has been added previously for the specified producer
        ProducerToken storage p = producerTokens[producerToken];
        ERC20[] memory rewardTokens = p.rewardTokens;
        uint256 len = rewardTokens.length;


        for (uint256 i; i < len; ++i) {
            if (address(rewardTokens[i]) == address(rewardToken)) {
                revert TokenAlreadyAdded();
            }
        }


        p.rewardTokens.push(rewardToken);


        emit AddRewardToken(producerToken, rewardToken);
    }
```

[removeRewardToken](https://github.com/code-423n4/2022-11-redactedcartel/blob/03b71a8d395c02324cb9fdaf92401357da5b19d1/src/PirexRewards.sol#L179-L197)
```solidity
    function removeRewardToken(ERC20 producerToken, uint256 removalIndex)
        external
        onlyOwner
    {
        if (address(producerToken) == address(0)) revert ZeroAddress();


        ERC20[] storage rewardTokens = producerTokens[producerToken]
            .rewardTokens;
        uint256 lastIndex = rewardTokens.length - 1;


        if (removalIndex != lastIndex) {
            // Set the element at removalIndex to the last element
            rewardTokens[removalIndex] = rewardTokens[lastIndex];
        }


        rewardTokens.pop();


        emit RemoveRewardToken(producerToken, removalIndex);
    }
```

Such mismanagement can cause users to lose rewards for two reasons:

1. Reward state of a user is updated _before_ their rewards are claimed;
2. It's the reward token addresses set by the owner of the `PirexRewards` contract that are used to transfer rewards.

In the `claim` function:

1. `harvest` is called to pull rewards from GMX ([PirexRewards.sol#L377](https://github.com/code-423n4/2022-11-redactedcartel/blob/03b71a8d395c02324cb9fdaf92401357da5b19d1/src/PirexRewards.sol#L377)):
  ```
	harvest()
  ```
2. `claimReward` is called on `PirexGmx` to pull rewards from GMX and get the hard coded lists of producer tokens, reward tokens, and amounts.
```solidity
(_producerTokens, rewardTokens, rewardAmounts) = producer
.claimRewards();
```
3. Rewards are recorded for each of the hard coded reward token
```
if (r != 0) {
    producerState.rewardStates[rewardTokens[i]] += r;
}
```
4. Later in the `claim` function, owner-set reward tokens are read
```solidity
ERC20[] memory rewardTokens = p.rewardTokens;
uint256 rLen = rewardTokens.length;
```
5. User reward state is set to 0, which means they've claimed their entire share of rewards, however this is done before a reward is actually claimed:
```solidity
p.userStates[user].rewards = 0;
```
6. The owner-set reward tokens are iterated and the previously recorded rewards are distributed
```solidity
for (uint256 i; i < rLen; ++i) {
    ERC20 rewardToken = rewardTokens[i];
    address rewardRecipient = p.rewardRecipients[user][rewardToken];
    address recipient = rewardRecipient != address(0)
        ? rewardRecipient
        : user;
    uint256 rewardState = p.rewardStates[rewardToken];
    uint256 amount = (rewardState * userRewards) / globalRewards;

    if (amount != 0) {
        // Update reward state (i.e. amount) to reflect reward tokens transferred out
        p.rewardStates[rewardToken] = rewardState - amount;

        producer.claimUserReward(
            address(rewardToken),
            amount,
            recipient
        );
    }
}
```

In the above loop, there can be multiple reasons for rewards to not be sent:

1. One of the hard coded reward tokens is missing in the owner-set reward tokens list;
2. The owner-set reward token list contains a token that's not supported by `PirexGmx` (i.e. it's not in the hard coded reward tokens list);
3. The `rewardTokens` array of a producer token turns out to be empty due to mismanagement by the owner.

In all of the above situations, rewards won't be sent, however user's reward state will still be set to 0.

Also, notice that calling `claim` won't revert if reward tokens are misconfigured, and the `Claim` event will be emitted successfully, which makes reward tokens mismanagement hard to detect.

The amount of lost rewards can be different depending on how much GMX a user has staked and how often they claim rewards. Of course, if a mistake isn't detected quickly, multiple users can suffer from this issue. The autocompounding contracts (`AutoPxGlp` and `AutoPxGmx`) are also users of the protocol, and since they're intended to hold big amounts of real users' deposits (they'll probably be the biggest stakers), lost rewards can be big.

### Recommended Mitigation Steps

Consider having one source of reward tokens. Since they're already hard coded in the `PirexGmx` contract, consider exposing them so that `PirexRewards` could read them in the `claim` function. This change will also mean that the `addRewardToken` and `removeRewardToken` functions won't be needed, which makes contract management simpler.

Also, in the `claim` function, consider updating global and user reward states only after ensuring that at least one reward token was distributed.
### Discussion

drahrealm (Redacted Cartel) disagreed with severity and commented:

> To make sure this won't be an issue, we will add the `whenNotPaused` modifier to `claimUserReward` method in `PirexGmx`. Also, as `migrateRewards` is going to be updated to also set the `pirexRewards` address to 0, it will defer any call to claim the rewards

### Notes & Impressions

#### Notes 
- Hard-coded list in one contract (`PirexGmx`)
- Dynamic, owner-controlled list in another contract (`PirexRewards`)
- **State Update Before Action Completion**: User's reward state is reset to 0 _before_ rewards are actually transferred
### Tools
### Refine
- [[1-Business_Logic]]

---

---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}