An invariant is a condition that should always be true throughout the lifecycle of a contract - it's like a fundamental law that the contract must never break.

First, let's define what makes a good invariant:

1. It should be a clear, testable condition
2. It should hold true across all possible state transitions
3. It should capture an essential security or business logic requirement

When writing invariants, consider these categories:

1. Value Conservation: Total inputs must equal total outputs (like total deposits vs borrows)
2. State Consistency: Related state variables must maintain logical relationships
3. Access Control: Certain operations should only be possible under specific conditions
4. Time Consistency: Time-dependent state transitions must maintain system integrity
5. Mathematical Bounds: Values must stay within acceptable ranges

## Example:


1. Define the expected invariants of the system. For a dispute system, some invariants might be:

```solidity
contract DisputeSystem {
    struct Tree {
        bytes32 merkleRoot;
        uint256 totalAmount;
        mapping(address => uint256) claimed;
    }
    
    Tree public currentTree;
    Tree public lastTree;
    address public disputer;
    uint256 public endOfDisputePeriod;
    uint256 public totalFunds;

    // Core Invariants we should verify:
    function checkInvariants() internal view {
        // Invariant 1: Total claimed amounts cannot exceed total funds
        assert(currentTree.totalAmount <= totalFunds);
        assert(lastTree.totalAmount <= totalFunds);
        
        // Invariant 2: Disputed trees cannot be used for claims
        if (disputer != address(0)) {
            assert(getMerkleRoot() != currentTree.merkleRoot);
        }
        
        // Invariant 3: Claims from a tree cannot exceed its declared total
        uint256 totalClaimed;
        // Note: This is pseudo-code as we can't iterate over mappings
        for (address user in currentTree.claimed) {
            totalClaimed += currentTree.claimed[user];
        }
        assert(totalClaimed <= currentTree.totalAmount);
        
        // Invariant 4: Time-based state consistency
        if (block.timestamp < endOfDisputePeriod) {
            assert(getMerkleRoot() == lastTree.merkleRoot);
        }
    }
}
```

ref: [[2023-06-Angle#[H-03] Poor detection of disputed trees allows claiming tokens from a disputed tree]]

2. Lending protocol example:
```solidity
contract LendingPool {
    struct UserAccount {
        uint256 deposited;
        uint256 borrowed;
        uint256 collateral;
    }
    
    mapping(address => UserAccount) public accounts;
    uint256 public totalDeposits;
    uint256 public totalBorrows;
    uint256 public reserveFactor;
    
    function checkLendingInvariants() internal view {
        // Invariant 1: Protocol solvency
        assert(totalDeposits >= totalBorrows);
        
        // Invariant 2: Individual account health
        for (address user in accounts) {
            UserAccount memory account = accounts[user];
            
            // Collateral ratio must always be maintained
            if (account.borrowed > 0) {
                uint256 collateralValue = getCollateralValue(account.collateral);
                uint256 borrowValue = getBorrowValue(account.borrowed);
                assert(collateralValue >= borrowValue * 150 / 100); // 150% collateral ratio
            }
            
            // User cannot borrow more than they're allowed
            assert(account.borrowed <= getMaxBorrow(account.collateral));
        }
        
        // Invariant 3: Reserve consistency
        uint256 totalReserves = getReserveBalance();
        assert(totalReserves >= (totalBorrows * reserveFactor) / 10000);
        
        // Invariant 4: Mathematical consistency
        uint256 sumDeposits;
        uint256 sumBorrows;
        for (address user in accounts) {
            sumDeposits += accounts[user].deposited;
            sumBorrows += accounts[user].borrowed;
        }
        assert(sumDeposits == totalDeposits);
        assert(sumBorrows == totalBorrows);
    }
}
```


## How to systematically derive invariants from contract requirements. 

This is a crucial skill for smart contract security, as it helps us translate business rules and security requirements into testable conditions.

Let's break this down into a systematic process using a real-world example. Imagine we're analyzing a staking contract where users can stake tokens to earn rewards. We'll walk through each step of deriving invariants from its requirements.

Step 1: Gather All Requirements Sources
First, we need to collect requirements from multiple sources:

```solidity
contract StakingRewards {
    // Token to be staked
    IERC20 public stakingToken;
    // Token to be earned as rewards
    IERC20 public rewardsToken;
    
    // Tracking staked amounts and rewards
    mapping(address => uint256) public stakedBalance;
    mapping(address => uint256) public rewards;
    uint256 public totalStaked;
    uint256 public rewardRate;
    uint256 public lastUpdateTime;
}
```

Let's say our sources include:
- Smart contract documentation
- Business requirements document
- Security considerations
- Protocol whitepaper
- Team discussions and meeting notes

Step 2: Categorize Requirements
We can organize requirements into different categories. For our staking contract:

Economic Requirements:
```text
"Users earn rewards proportional to their stake and time staked"
"Total rewards distributed cannot exceed the contract's reward token balance"
"Users cannot withdraw more than they deposited"
```

Security Requirements:
```text
"Only staked tokens can be withdrawn"
"Rewards calculation must be resistant to manipulation"
"Contract must remain solvent at all times"
```

Administrative Requirements:
```text
"Only admin can update reward rates"
"Emergency withdrawal mechanism must always work"
```

Step 3: Transform Requirements into Mathematical Statements
Let's convert these natural language requirements into mathematical expressions:

```solidity
contract StakingInvariants {
    // Economic invariant: User rewards are proportional to stake
    function checkRewardProportionality(address user) internal view {
        uint256 userStake = stakedBalance[user];
        uint256 userRewards = rewards[user];
        uint256 timePassed = block.timestamp - lastUpdateTime;
        
        // User's reward should equal: stake * rewardRate * time
        assert(userRewards == (userStake * rewardRate * timePassed) / 1e18);
    }
    
    // Solvency invariant: Contract must have enough rewards
    function checkSolvency() internal view {
        uint256 totalPossibleRewards = totalStaked * rewardRate * 
            (block.timestamp - lastUpdateTime);
        assert(rewardsToken.balanceOf(address(this)) >= totalPossibleRewards);
    }
}
```

Step 4: Identify State Variables and Their Relationships
For each requirement, identify which state variables are involved:

```solidity
contract StateRelationships {
    // Relationship: Total staked must equal sum of individual stakes
    function checkStakeConsistency() internal view {
        uint256 sumOfStakes;
        // Note: This is pseudo-code as we can't iterate over mappings
        for (address user in stakedBalance) {
            sumOfStakes += stakedBalance[user];
        }
        assert(sumOfStakes == totalStaked);
    }
    
    // Relationship: User balances cannot exceed their deposits
    function checkBalanceConstraints(address user) internal view {
        assert(stakedBalance[user] <= stakingToken.balanceOf(address(this)));
    }
}
```

Step 5: Define Temporal Invariants
Consider how values should behave over time:

```solidity
contract TemporalInvariants {
    uint256 public lastRewardUpdate;
    
    function checkTimeBasedInvariants() internal view {
        // Rewards should never decrease over time
        uint256 currentRewards = calculateRewards(msg.sender);
        // Store this value and check in next update that new value is higher
        assert(currentRewards >= lastStoredRewards[msg.sender]);
        
        // Time should always move forward
        assert(block.timestamp >= lastRewardUpdate);
        
        // Reward rate changes should be properly time-weighted
        assert(getTimeWeightedRewardRate() == expectedRate);
    }
}
```

Step 6: Create Composite Invariants
Combine related invariants to create more complex checks:

```solidity
contract CompositeInvariants {
    function checkSystemHealth() internal view {
        // Combine solvency, stake consistency, and rewards accuracy
        bool isSolvent = rewardsToken.balanceOf(address(this)) >= 
            calculateTotalOutstandingRewards();
        bool stakesMatch = validateStakeConsistency();
        bool rewardsAccurate = validateRewardsCalculation();
        
        assert(isSolvent && stakesMatch && rewardsAccurate);
    }
}
```

Step 7: Test Edge Cases
Derive invariants specifically for boundary conditions:

```solidity
contract EdgeCaseInvariants {
    function checkEdgeCases() internal view {
        // Check zero stake edge case
        assert(calculateRewards(address(0)) == 0);
        
        // Check maximum stake edge case
        assert(calculateRewards(maxStaker) < rewardsToken.balanceOf(address(this)));
        
        // Check reward calculation with minimum time passage
        assert(calculateRewards(msg.sender) >= lastRewardAmount);
    }
}
```

