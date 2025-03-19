# 2022-10-holograph
---
- Category: #Dexes #Bridge #services #Launchpad #NFT_Marketplace 
- Note Create 2025-03-17
- Platform: code4rena
- Report Url: [2022-10-holograph](https://code4rena.com/reports/2022-10-holograph)
---
# Critical & High Risk Findings (xx)

---
## [H-02] If user sets a low `gasPrice` the operator would have to choose between being locked out of the pod or executing the job anyway
----
- **Tags**:  #business_logic #gas_price
- Number of finders: 4
- Difficulty: Medium
---
During the beaming process the user compensates the operator for the gas he has to pay by sending some source-chain-native-tokens via `hToken`.
The amount he has to pay is determined according to the `gasPrice` set by the user, which is supposed to be the maximum gas price to be used on dest chain (therefore predicting the max gas fee the operator would pay and paying him the same value in src chain native tokens).
However, in case the user sets a low price (as low as 1 wei) the operator can't skip the job because he's locked out of the pod till he executes the job. 
The operator would have to choose between loosing money by paying a higher gas fee than he's compensated for or being locked out of the pod - not able to execute additional jobs or get back his bonded amount.
### Impact

Operator would be losing money by having to pay gas fee that's higher than the compensation (gas fee can be a few dozens of USD for heavy `txs`). 
This could also be used by attackers to make operators pay for the attackers' expensive gas tasks:

- They can deploy their own contract as the 'source contract'
- Use the `bridgeIn` event and the `data` that's being sent to it to instruct the source contract what operations need to be executed
- They can use it for execute operations where the `tx.origin` doesn't matter (e.g. USDc gasless send)
### Proof of Concept

- An operator can't execute any further jobs or leave the pod till the job is executed. From the docs:

> When an operator is selected for a job, they are temporarily removed from the pod, until they complete the job. If an operator successfully finalizes a job, they earn a reward and are placed back into their selected pod.

- Operator can't skip a job. Can't prove a negative but that's pretty clear from reading the code.
- There's indeed a third option - that some other operator/user would execute the job instead of the selected operator, but a) the operator would get slashed for that. b) If the compensation is lower than the gas fee then other users have no incentive to execute it as well.
### Recommended Mitigation

Allow operator to opt out of executing the job if the `gasPrice` is higher than the current gas price.
### Discussion

**alexanderattar (Holograph) commented:**

> Is a known issue, and we will be fixing it.

**alexanderattar (Holograph) resolved**

> [Feature/HOLO-604: implementing critical issue fixes](https://github.com/holographxyz/holograph-protocol/pull/84)
### Notes

#### System Setup:

1. Bob is an operator who has deposited 10 ETH ($20,000) as a bond into a pod
2. Bob earns money by executing cross-chain transactions for users
3. When Bob is assigned a job, he's temporarily removed from the pod until he completes it
4. Bob cannot take new jobs or withdraw his 10 ETH bond until he completes his assigned job

#### Normal Operation:

1. Alice wants to transfer tokens from Ethereum to Arbitrum
2. Alice sets a gasPrice parameter of 50 gwei, which is the current market rate on Arbitrum
3. Alice sends compensation to Bob in ETH on Ethereum based on this 50 gwei rate
4. Bob receives the job, executes the transfer on Arbitrum paying ~50 gwei, and returns to the pod
5. Bob earned a fair profit because the compensation matched his costs

#### Exploit Scenario:

1. Mallory wants to transfer tokens from Ethereum to Arbitrum during network congestion
2. Mallory deliberately sets gasPrice at 1 gwei (far below market rate of 200 gwei during congestion)
3. Mallory sends compensation to Bob based on this 1 gwei rate (approximately $0.20 worth of ETH)
4. Bob receives the job but realizes the actual gas cost on Arbitrum is currently 200 gwei ($40)

#### Bob's Dilemma:

- **Option 1:** Execute Mallory's transaction at a personal loss of $39.80
- **Option 2:** Refuse to execute, becoming locked out of the pod system indefinitely, unable to:
    - Execute other profitable jobs
    - Withdraw his 10 ETH ($20,000) bond
#### Impressions

Set `minGasPrice`

### Tools
### Refine
- [[1-Business_Logic]]
- [[29-GasPrice]]

---
## [H-04] An attacker can manipulate each pod and gain an advantage over the remainder Operators
----
- **Tags**:  #business_logic #share_randomness
- Number of finders: 3
- Difficulty: Medium
---
In `crossChainMessage`

```solidity
  function crossChainMessage(bytes calldata bridgeInRequestPayload) external payable {
    require(msg.sender == address(_messagingModule()), "HOLOGRAPH: messaging only call");
    /**
     * @dev would be a good idea to check payload gas price here and if it is significantly lower than current amount
     *      to set zero address as operator to not lock-up an operator unnecessarily
     */
    unchecked {
      bytes32 jobHash = keccak256(bridgeInRequestPayload);
      /**
       * @dev load and increment operator temp storage in one call
       */
      ++_operatorTempStorageCounter;
      /**
       * @dev use job hash, job nonce, block number, and block timestamp for generating a random number
       */
      uint256 random = uint256(keccak256(abi.encodePacked(jobHash, _jobNonce(), block.number, block.timestamp)));
      /**
       * @dev divide by total number of pods, use modulus/remainder
       */
      uint256 pod = random % _operatorPods.length;
      /**
       * @dev identify the total number of available operators in pod
       */
      uint256 podSize = _operatorPods[pod].length;
      /**
       * @dev select a primary operator
       */
      uint256 operatorIndex = random % podSize;
      /**
       * @dev If operator index is 0, then it's open season! Anyone can execute this job. First come first serve
       *      pop operator to ensure that they cannot be selected for any other job until this one completes
       *      decrease pod size to accomodate popped operator
       */
      _operatorTempStorage[_operatorTempStorageCounter] = _operatorPods[pod][operatorIndex];
      _popOperator(pod, operatorIndex);
      if (podSize > 1) {
        podSize--;
      }
      _operatorJobs[jobHash] = uint256(
        ((pod + 1) << 248) |
          (uint256(_operatorTempStorageCounter) << 216) |
          (block.number << 176) |
          (_randomBlockHash(random, podSize, 1) << 160) |
          (_randomBlockHash(random, podSize, 2) << 144) |
          (_randomBlockHash(random, podSize, 3) << 128) |
          (_randomBlockHash(random, podSize, 4) << 112) |
          (_randomBlockHash(random, podSize, 5) << 96) |
          (block.timestamp << 16) |
          0
      ); // 80 next available bit position && so far 176 bits used with only 128 left
      /**
       * @dev emit event to signal to operators that a job has become available
       */
      emit AvailableOperatorJob(jobHash, bridgeInRequestPayload);
    }
  }
```

each Operator is selected by:

- Generating a random number ``
```solidity
	uint256 random = uint256(keccak256(abi.encodePacked(jobHash, _jobNonce(), block.number, block.timestamp)));
```    
- A pod is selected by dividing the random with the total number of pods, and using the remainder
```solidity
	uint256 operatorIndex = random % podSize;
```
- An Operator of the selected pod is chosen using the **same** random and dividing by the total number of operators.
```solidity
	uint256 pod = random % _operatorPods.length;
```

This creates an unintended bias since the first criterion (the `random`) is used for both selecting the pod and selecting the Operator, as explained in a previous issue (`M001-Biased distribution`). In this case, an attacker knowing this flaw can continuously monitor the contracts state and see the current number of pods and Operators. 

- An Operator can easily join and leave a pod, albeit when leaving a small fee is paid
- An Operator can only join one pod, but an attacker can control multiple Operators
- The attacker can then enter and leave a pod to increase (unfairly) his odds of being selected for a job

Honest Operators may feel compelled to leave the protocol if there are no financial incentives (and lose funds in the process), which can also increase the odds of leaving the end-users at the hands of a malicious Operator.
### Proof of Concept

Consider the following simulation for 10 pods with a varying number of operators follows (X → "does not apply"):

| Pod n | Pon len | Op0 | Op1 | Op2 | Op3 | Op4 | Op5 | Op6 | Op7 | Op8 | Op9 | Total Pod |
| ----- | ------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --------- |
| P0    | 10      | 615 | 0   | 0   | 0   | 0   | 0   | 0   | 0   | 0   | 0   | 615       |
| P1    | 3       | 203 | 205 | 207 | X   | X   | X   | X   | X   | X   | X   | 615       |
| P2    | 6       | 208 | 0   | 233 | 0   | 207 | 0   | X   | X   | X   | X   | 648       |
| P3    | 9       | 61  | 62  | 69  | 70  | 65  | 69  | 61  | 60  | 54  | X   | 571       |
| P4    | 4       | 300 | 0   | 292 | 0   | X   | X   | X   | X   | X   | X   | 592       |
| P5    | 10      | 0   | 0   | 0   | 0   | 0   | 586 | 0   | 0   | 0   | 0   | 586       |
| P6    | 2       | 602 | 0   | X   | X   | X   | X   | X   | X   | X   | X   | 602       |
| P7    | 7       | 93  | 93  | 100 | 99  | 76  | 74  | 78  | X   | X   | X   | 613       |
| P8    | 2       | 586 | 0   | X   | X   | X   | X   | X   | X   | X   | X   | 586       |
| P9    | 6       | 0   | 190 | 0   | 189 | 0   | 192 | X   | X   | X   | X   | 571       |
|       |         |     |     |     |     |     |     |     |     |     |     |           |

At this stage, an attacker Mallory joins the protocol and scans the protocol (or interacts with - e.g. `getTotalPods`, `getPodOperatorsLength`). As an example, after considering the potential benefits, she chooses pod `P9` and sets up some bots `[B1, B2, B3]`. The number of Operators will determine the odds, so:

| Pod P9 | Alt len | Op0 | Op1 | Op2 | Op3 | Op4 | Op5 | Op6 | Op7 | Op8 | Op9 | Total Pod |
| ------ | ------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --------- |
| P9A    | 4       | 0   | 276 | 0   | 295 | X   | X   | X   | X   | X   | X   | 571       |
| P9B    | 5       | 0   | 0   | 0   | 0   | 571 | X   | X   | X   | X   | X   | 571       |
| P9     | 6       | 0   | 190 | 0   | 189 | 0   | 192 | X   | X   | X   | X   | 571       |
| P9C    | 7       | 66  | 77  | 81  | 83  | 87  | 90  | 87  | X   | X   | X   | 571       |
| P9D    | 8       | 0   | 127 | 0   | 147 | 0   | 149 | 0   | 148 | X   | X   | 571       |

And then:

1. She waits for the next job to fall in `P9` and keeps an eye on the number of pods, since it could change the odds.
2. After an Operator is selected (he pops from the array. `_popOperator(pod, operatorIndex);` ), the number of available Operators change to 5, and the odds change to `P9B`.
3. She deploys `B1` and it goes to position `Op5`, odds back to `P9`. If the meantime the previously chosen Operator comes back to the `pod`, see the alternative timeline.
4. She now has 1/3 of the probability to be chosen for the next job:  
    4.1 If she is not chosen, she will assume the position of the chosen Operator, and deploys `B2` to maintain the odds of `P9` and controls 2/3 of the pod.  
```
        if (lastIndex != operatorIndex) {
          /**
           * @dev if operator is not last index, move last index to operator's current index
           */
          _operatorPods[pod][operatorIndex] = _operatorPods[pod][lastIndex];
          _operatorPodIndex[_operatorPods[pod][operatorIndex]] = operatorIndex;
        }
```
	4.2 If she is chosen, she chooses between employing another bot or waiting to execute the job to back to the pod (keeping the original odds).
5. She can then iterate multiple times to swap to the remainder of possible indexes via step 4.1.

Alternative timeline (from previous 3.):

1. The chosen Operator finishes the job and goes back to the pod. Now there's 7 members with uniform odds (`P9C`).
2. Mallory deploys `B2` and the length grows to 8, the odds turn to `P9D` and she now controls two of the four possible indexes from which she can be chosen.

There are a lot of ramifications and possible outcomes that Mallory can manipulate to increase the odds of being selected in her favor.
### Recommended Mitigation

Has stated in `M001-Biased distribution`, use two random numbers for pod and Operator selection. Ideally, an independent source for randomness should be used, but following the assumption that the one used in [L499](https://github.com/code-423n4/2022-10-holograph/blob/main/contracts/HolographOperator.sol#L499) is safe enough, using the most significant bits (e.g. `random >> 128`) should guarantee an unbiased distribution. Also, reading the EIP-4399 could be valuable.

```
L499  uint256 random = uint256(keccak256(abi.encodePacked(jobHash, _jobNonce(), block.number, block.timestamp)));
```

Additionally, since randomness in blockchain is always tricky to achieve without an oracle provider, consider adding additional controls (e.g. waiting times before joining each pod) to increase the difficulty of manipulating the protocol.

And finally, in this particular case, removing the swapping mechanism (moving the last index to the chosen operator's current index) for another mechanism (shifting could also create **conflicts with backup operators**? ) could also increase the difficulty of manipulating a particular pod.

(shifting could also create conflicts [with backup operators?](https://github.com/code-423n4/2022-10-holograph/blob/main/contracts/HolographOperator.sol#L358-L370))
```
        if (timeDifference < 6) {
          uint256 podIndex = uint256(job.fallbackOperators[timeDifference - 1]);
          /**
           * @dev do a quick sanity check to make sure operator did not leave from index or is a zero address
           */
          if (podIndex > 0 && podIndex < _operatorPods[pod].length) {
            address fallbackOperator = _operatorPods[pod][podIndex];
            /**
             * @dev ensure that sender is currently valid backup operator
             */
            require(fallbackOperator == msg.sender, "HOLOGRAPH: invalid fallback");
          }
        }
```
### Discussion

### Notes

#### Exploitation Example

Let me walk through a simplified example:

Imagine we have 10 pods, and a random number of 123456789.

1. Pod selection: 123456789 % 10 = 9 (so we select Pod 9)
2. Now, the operator selection depends on how many operators are in Pod 9
    - If Pod 9 has 6 operators: 123456789 % 6 = 3 (select operator at index 3)
    - If Pod 9 has 3 operators: 123456789 % 3 = 0 (select operator at index 0)

An attacker named Mallory realizes this relationship and does the following:

1. She observes the current state of the protocol (number of pods and operators in each pod)
2. She joins Pod 9 with multiple operator accounts under her control
3. She strategically positions these accounts to maximize her chances of selection
4. When a job comes in and an operator is selected, the remaining operators shift positions
5. Mallory repositions her remaining operators to maintain maximum advantage

Because of the mathematical relationship, Mallory can predict which positions are more likely to be selected and place her operators there. As the finding shows, she can methodically increase her control over a pod from 1/3 to 2/3 and potentially higher.
#### Impressions

**Shared Randomness Sources**: When a single random number is used for multiple selections, check for mathematical relationships between the selections.

### Tools
### Refine

- [[1-Business_Logic]]

---
## [H-07] Failed job can't be recovered. NFT may be lost.
----
- **Tags**:  #business_logic 
- Number of finders: 5
- Difficulty: Medium
---
### Detail

`executeJob` in `HolographOperator.sol`
```
function executeJob(bytes calldata bridgeInRequestPayload) external payable {
...
	delete _operatorJobs[hash];
...

    try
      HolographOperatorInterface(address(this)).nonRevertingBridgeCall{value: msg.value}(
        msg.sender,
        bridgeInRequestPayload
      )
    {
      /// @dev do nothing
    } catch {
      _failedJobs[hash] = true;
      emit FailedOperatorJob(hash);
    }
}
```

First, it will `delete _operatorJobs[hash];` to have it not replayable.

Next, assume `nonRevertingBridgeCall` failed. NFT won't be minted and the catch block is entered.

`_failedJobs[hash]` is set to true and event is emitted

Notice that `_operatorJobs[hash]` has been deleted, so this job is not replayable. This mean NFT is lost forever since we can't retry executeJob.
### Recommended Mitigation

Move `delete _operatorJobs[hash];` to the end of function executeJob covered in `if (!_failedJobs[hash])`

```solidity
...
if (!_failedJobs[hash]) delete _operatorJobs[hash];
...
```

But this implementation is not safe. The selected operator may get slashed. Additionally, you may need to check `_failedJobs` flag to allow retry for only the selected operator.
### Discussion
gzeon (judge) commented

> While the use of non-blocking call is good to unstuck operator, consider making the failed job still executable by anyone (so the user can e.g. use a higher gas limit) to avoid lost fund. Kinda like how Arbitrum retryable ticket works. Can be high risk due to asset lost.

Trust (warden) commented

> I think it's a design choice to make it not replayable. Sponsor discussed having a refund mechanism at the source chain, if we were to leave it replayable the refunding could lead to double mint attack.

alexanderattar (Holograph) commented

> This is a valid point and the desired code is planned but wasn't implemented in time for the audit. We will add logic to handle this case.

gzeon (judge) increased severity to High and commented

> Since asset can be lost, I think it is fair to judge this as High risk.

alexanderattar (Holograph) resolved and commented

> We have a fix for this: 
```
   /**
   * @notice Recover failed job
   * @dev If a job fails, it can be manually recovered
   * @param bridgeInRequestPayload the entire cross chain message payload
   */
  function recoverJob(bytes calldata bridgeInRequestPayload) external payable {
    bytes32 hash = keccak256(bridgeInRequestPayload);
    require(_failedJobs[hash], "HOLOGRAPH: invalid recovery job");
    (bool success, ) = _bridge().call{value: msg.value}(bridgeInRequestPayload);
    require(success, "HOLOGRAPH: recovery failed");
    delete (_failedJobs[hash]);
  }
```

### Notes

#### Notes 
##### Example Scenario

Alice wants to transfer her valuable NFT (worth 10 ETH) from Chain A to Chain B:

1. Alice initiates a bridge operation on Chain A
2. A job is created on Chain B with hash `0x123...` and stored in `_operatorJobs[0x123...]`
3. An operator on Chain B calls `executeJob` with Alice's bridge payload

Let's say the `nonRevertingBridgeCall` fails because:

- The gas limit was too low
- There was a temporary network issue
- A condition in the minting logic wasn't met

What happens now?

1. The job is marked as failed in `_failedJobs[0x123...]`
2. A `FailedOperatorJob` event is emitted
3. But critically, the job data has already been deleted from `_operatorJobs[0x123...]`
#### Impressions
- caution: delete Mapping 
- Only delete or modify resources after confirmed success, and always provide recovery mechanisms for failed operations.

### Tools
### Refine

- [[1-Business_Logic]]

---
# Medium Risk Findings (xx)

---
## [M-03] Beaming job might freeze on dest chain under some conditions, leading to owner losing (temporarily) access to token
----
- **Tags**: #business_logic #gas_price #gas_spike
- Number of finders: 1
- Difficulty: Hard
---
```solidity
        require(gasPrice >= tx.gasprice, "HOLOGRAPH: gas spike detected");
```

If the following conditions have been met:

- The selected operator doesn't complete the job, either intentionally (they're sacrificing their bonded amount to harm the token owner) or innocently (hardware failure that caused a loss of access to the wallet)
- Gas price has spiked, and isn't going down than the `gasPrice` set by the user in the bridge out request

Then the bridging request wouldn't complete and the token owner would lose access to the token till the gas price goes back down again.
### Proof of Concept

The fact that no one but the selected operator can execute the job in case of a gas spike has been proven by the test 'Should fail if there has been a gas spike' provided by the sponsor.

'Should fail if there has been a gas spike'
```typescript
    it('Should fail if there has been a gas spike', async () => {
      let payloadHash: string = availableJobs[0] as string;
      let payload: string = availableJobs[1] as string;
      let operatorJob = await l1.operator.getJobDetails(payloadHash);
      let jobOperator = pickOperator(l1, operatorJob[2], true);
      process.stdout.write(' '.repeat(8) + 'sleeping for ' + BLOCKTIME + ' seconds...' + '\n');
      await sleep(1000 * BLOCKTIME); // gotta wait 60 seconds for operator opportunity to close
      await expect(
        l1.operator.connect(jobOperator).executeJob(payload, { gasPrice: GASPRICE.mul(BigNumber.from('2')) })
      ).to.be.revertedWith('HOLOGRAPH: gas spike detected');
    });
```

An example of a price spike can be in the recent month in the Ethereum Mainnet where the min gas price was 3 at Oct 8, but jumped to 14 the day after and didn't go down since then (the min on Oct 9 was lower than the avg of Oct8, but users might witness a momentarily low gas price and try to hope on it). See the gas price chat on Etherscan for more details.
### Recommended Mitigation

In case of a gas price spike, instead of refusing to let other operators to execute the job, let them execute the job without slashing the selected operator. This way, after a while also the owner can execute the job and pay the gas price.

### Discuss

**Trust (warden) commented:**

> If there is a gas spike, it is too expensive to execute the transaction, so we should not force executor to do it. I think it is intended behavior that `TX` just doesn't execute until gas falls back down.<br> The docs state there is a refund mechanism that is activated in this case, back to origin chain.

**0xA5DF (warden) commented:**

> > The docs state there is a refund mechanism that is activated in this case, back to origin chain.
> 
> Can you please point where in the docs does it state that?<br> Also, regardless of the docs, that kind of mechanism is certainly not implemented.

**Trust (warden) commented:**

> Operator Job Selection:<br> "Operator jobs are given specific gas limits. This is meant to prevent gas spike abuse (e.g., as a form of DoS attack), bad code, or smart contract reverts from penalizing good-faith operators. If an operator is late to finalize a job and another operator steps in to take its place, if the gas price is above the set limit, the selected operator will not get slashed. A job is considered successful if it does not revert, or if it reverts but gas limits were followed correctly. Failed jobs can be re-done (for an additional fee), can be returned to origin chain (for an additional fee), or left untouched entirely. This shifts the financial responsibility towards users, rather than operators."

**0xA5DF (warden) commented:**

> Thanks, wasn't aware of that at time of submission.<br> But the docs specifically talk about 'failed jobs', in this case the job wouldn't even be marked as failed since nobody would be able to execute the `executeJob()` function (the `require(gasPrice >= tx.gasprice` would revert the entire function rather than move to the catch block)

**Trust (warden) commented:**

> I think the assumption is that `tx.gasprice` will eventually come back to a non-reverting amount. Agree that it seems like a good idea to add a force-fail after `EXPIRY_NUM` blocks passed, without executing the `TX`.

**alexanderattar (Holograph) commented):**

> Agree that it seems like a good idea to add a force-fail after `EXPIRY_NUM` blocks passed, without executing the `TX`.

### Discussion

### Notes & Impressions

#### Notes 
Imagine Alice wants to transfer her NFT from Ethereum to Polygon. She sets a gas price of 20 gwei when initiating the transfer, based on current network conditions.

1. The system selects Bob as the operator to complete this transfer
2. Shortly after, an anticipated NFT drop causes gas prices to spike to 50 gwei
3. Bob experiences a hardware failure and can't execute the job
4. Gas prices remain elevated for several days
5. During this time, Alice's NFT is stuck in the bridge - not accessible on either chain

Even if other operators are willing to execute the job despite higher gas costs, they can't because the contract will revert their transaction with the "gas spike detected" error

#### Impressions

#gas_spike 

### Tools
### Refine

- [[1-Business_Logic]]

---
## [M-07] Attacker can force chaotic operator behavior
----
- **Tags**: #business_logic #chaotic 
- Number of finders: 2
- Difficulty: Hard
---
### Detail

Operators are organized into different pod tiers. Every time a new request arrives, it is scheduled to a random available pod. It is important to note that pods may be empty, in which case the pod array actually has a single zero element to help with all sorts of bugs. When a pod of a non existing tier is created, any intermediate tiers between the current highest tier to the new tier are filled with zero elements. This happens at `bondUtilityToken()`:

```solidity
if (_operatorPods.length < pod) {
  /**
   * @dev activate pod(s) up until the selected pod
   */
  for (uint256 i = _operatorPods.length; i <= pod; i++) {
    /**
     * @dev add zero address into pod to mitigate empty pod issues
     */
    _operatorPods.push([address(0)]);
  }
}
```

The issue is that any user can spam the contract with a large amount of empty operator pods. The attack would look like this:

1. `bondUtilityToken`(attacker, large_amount, high_pod_number)
2. `unbondUtilityToken`(attacker, attacker)

The above could be wrapped in a flashloan to get virtually any pod tier filled.

The consequence is that when the scheduler chooses pods uniformly, they will very likely choose an empty pod, with the zero address. Therefore, the chosen operator will be 0, which is referred to in the code as "open season". In this occurrence, any operator can perform the `executeJob()` call. This is of course really bad, because all but one operator continually waste gas for executions that will be reverted after the lucky first transaction goes through. This would be a practical example of a griefing attack on Holograph.
### Impact

Any user can force chaotic "open season" operator behavior
### Recommended Mitigation

It is important to pay special attention to the scheduling algorithm, to make sure different pods are given execution time according to the desired heuristics.

### Discussion

### Notes & Impressions

The pod selection mechanism doesn't account for the possibility of many empty pods.
### Tools
### Refine

- [[1-Business_Logic]]

---
## [M-12] Bond tokens (HLG) can get permanently stuck in operator
----
- **Tags**: #business_logic #paradox
- Number of finders: 8
- Difficulty: Medium
---
Bond tokens (HLG) equal to the slash amount will get permanently stuck in the HolographOperator each time a job gets executed by someone who is not an (fallback-)operator.
### Proof of Concept

The `HolographOperator.executeJob` function can be executed by anyone after a certain passage of time:

```solidity
...
if (job.operator != address(0)) {
    ...
    if (job.operator != msg.sender) {
        //perform time and gas price check
        if (timeDifference < 6) {
            // check msg.sender == correct fallback operator
        }
        // slash primary operator
        uint256 amount = _getBaseBondAmount(pod);
        _bondedAmounts[job.operator] -= amount;
        _bondedAmounts[msg.sender] += amount;

        //determine if primary operator retains his job
        if (_bondedAmounts[job.operator] >= amount) {
            ...
        } else {
            ...
        }
    }
}
// execute the job
```

In case `if (timeDifference < 6) {` gets skipped, the slashed amount will be assigned to the `msg.sender` regardless if that sender is currently an operator or not. The problem lies within the fact that if `msg.sender` is not already an operator at the time of executing the job, he cannot become one after, to retrieve the reward he got for slashing the primary operator. This is because the function `HolographOperator.bondUtilityToken` requires `_bondedAmounts` to be 0 prior to bonding and hence becoming an operator:

```solidity
require(_bondedOperators[operator] == 0 && _bondedAmounts[operator] == 0, "HOLOGRAPH: operator is bonded");
```

### Recommended Mitigation

Assuming that it is intentional that non-operators can execute jobs (which could make sense, so that a user could finish a bridging process on his own, if none of the operators are doing it): remove the requirement that `_bondedAmounts` need to be 0 prior to bonding and becoming an operator so that non-operators can get access to the slashing reward by unbonding after.

Alternatively (possibly preferable), just add a method to withdraw any `_bondedAmounts` of non-operators.

```solidity
	require(_bondedOperators[operator] == 0 && _bondedAmounts[operator] == 0, "HOLOGRAPH: operator is bonded");
+   if (_isContract(operator)) {
+     require(Ownable(operator).owner() != address(0), "HOLOGRAPH: contract not ownable");
+   }
```
### Discussion

### Notes & Impressions
## The Catch-22 Situation

This creates a paradoxical situation:

- To withdraw bonded tokens, you must be an operator
- To become an operator, you must have zero bonded tokens
- But if you receive tokens from slashing, you now have bonded tokens
- Which means you can't become an operator
- Which means you can't withdraw the tokens
#### Example Scenario
- Alice is an operator with 1000 HLG bonded
- Alice is assigned a job but fails to execute it
- After the time limit, Bob (who is not an operator) notices and executes the job
- The protocol slashes Alice, taking 100 HLG from her bonded amount
- The 100 HLG is credited to Bob's `_bondedAmounts[bob]`
- Bob now has 100 HLG in the system but can't become an operator because his balance isn't zero
- Bob also can't withdraw the tokens because he isn't an operator
- The 100 HLG is now permanently stuck in the contract

#### Impressions

Access control Paradox
when a system has conflicting or circular dependencies between resource access and state requirements.
### Tools
### Refine

- [[1-Business_Logic]]

---
## [M-13] Implementation code does not align with the business requirement: Users are not charged with withdrawn fee when user unbound token in `HolographOperator.sol`
----
- **Tags**: #business_logic 
- Number of finders: 1
- Difficulty: Hard
---
When user call `unbondUtilityToken` to `unstake` the token, the function reads the available bonded amount, and transfers back to the operator.

```solidity
/**
 * @dev get current bonded amount by operator
 */
uint256 amount = _bondedAmounts[operator];
/**
 * @dev unset operator bond amount before making a transfer
 */
_bondedAmounts[operator] = 0;
/**
 * @dev remove all operator references
 */
_popOperator(_bondedOperators[operator] - 1, _operatorPodIndex[operator]);
/**
 * @dev transfer tokens to recipient
 */
require(_utilityToken().transfer(recipient, amount), "HOLOGRAPH: token transfer failed");
```

the logic is clean, but does not conform to the business requirement in the documentation, the doc said

> To move to a different pod, an Operator must withdraw and re-bond HLG. Operators who withdraw HLG will be charged a 0.1% fee, the proceeds of which will be burned or returned to the Treasury.

The charge 0.1% fee is not implemented in the code.

there are two incentive for bounded operator to stay,

the first is the reward incentive, the second is to avoid penalty with `unbonding`.

Without `charge` the `unstaking` fee, the second incentive is weak and the operator can unbound or bond whenever they want.

### Recommended Mitigation

We recommend charge the 0.1% `unstaking` fee to make the code align with the business requirement in the doc.

```solidity
/**
 * @dev get current bonded amount by operator
 */
uint256 amount = _bondedAmounts[operator];
uint256 fee = chargedFee(amount); // here
amount -= fee;  
/**
 * @dev unset operator bond amount before making a transfer
 */
_bondedAmounts[operator] = 0;
/**
 * @dev remove all operator references
 */
_popOperator(_bondedOperators[operator] - 1, _operatorPodIndex[operator]);
/**
 * @dev transfer tokens to recipient
 */
require(_utilityToken().transfer(recipient, amount), "HOLOGRAPH: token transfer failed");
```
### Discussion
alexanderattar (Holograph) commented

> This is true. The functionality is purposefully disabled for easier bonding/unbonding testing by team at the moment, but will be addressed in the upcoming release.

alexanderattar (Holograph) commented

> On initial mainnet beta launch, Holograph will be operating as the sole operator on the network so this is not an immediate concern, but before the launch of the public operator network, the fee will be added via upgrade.
### Notes & Impressions

#PCPvsSCP 

### Tools
### Refine

- [[1-Business_Logic]]
---
## [M-17] Wrong slashing calculation rewards for operator that did not do his job
----
- **Tags**: #business_logic 
- Number of finders: 4
- Difficulty: Medium
---
Wrong slashing calculation may create unfair punishment for operators that accidentally forgot to execute their job.
### Proof of Concept

Docs: If an operator acts maliciously, a percentage of their bonded HLG will get slashed. Misbehavior includes 
1. downtime, 
2. double-signing transactions, and 
3. abusing transaction speeds. 
50% of the slashed HLG will be rewarded to the next operator to execute the transaction, and the remaining 50% will be burned or returned to the Treasury.

The docs also include a guide for the number of slashes and the percentage of bond slashed. However, in the contract, there is no slashing of percentage fees. Rather, the whole `_getBaseBondAmount()` fee is slashed from the job.operator instead.

```solidity
	uint256 amount = _getBaseBondAmount(pod);
	/**
	 * @dev select operator that failed to do the job, is slashed the pod base fee
	 */
	_bondedAmounts[job.operator] -= amount;
	/**
	 * @dev the slashed amount is sent to current operator
	 */
	_bondedAmounts[msg.sender] += amount;
```

Documentation states that only a portion should be slashed and the number of slashes should be noted down.
### Recommended Mitigation

Implement the correct percentage of slashing and include a mapping to note down the number of slashes that an operator has.
### Discussion

### Notes & Impressions

#### Notes 
According to the documentation, the slashing amount should:

- Be a percentage of the operator's bonded tokens
- Vary based on the number of previous infractions
- Have 50% of the slashed amount rewarded to the next operator
- Have the remaining 50% either burned or returned to the Treasury

However, the actual implementation in the code doesn't follow these rules. Instead, it:

- Slashes the full base bond amount (`_getBaseBondAmount(pod)`)
- Transfers the entire slashed amount to the new operator
- Doesn't track the number of infractions
- Doesn't implement the percentage-based slashing system

#### Impressions
#PCPvsSCP 

### Tools
### Refine

- [[1-Business_Logic]]

---
## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}