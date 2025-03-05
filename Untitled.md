## [H-01] griefing / blocking / delaying users to withdraw
----
- **Tags**:  [[report_tags]]
- Number of finders: 5
- Difficulty: Medium
---
### Detail

To withdraw, a user needs to convert his collateral for the base token. This is done in the **withdraw** function in Collateral.

The `WithdrawHook` has some security mechanics that can be activated like a global max withdraw in a specific timeframe, also for users to have a withdraw limit for them in a specific timeframe. It also collects the fees.

The check for the user withdraw is wrongly implemented and can lead to an unepexted delay for a user with a `position > userWithdrawLimitPerPeriod`. To withdraw all his funds he needs to be the first in every first new epoch `(lastUserPeriodReset + userPeriodLength)` to get his amount out. If he is not the first transaction in the new epoch, he needs to wait for a complete new epoch and depending on the timeframe from `lastUserPeriodReset + userPeriodLength` this can get a long delay to get his funds out.

The documentation says, that after every epoch all the user withdraws will be reset and they can withdraw the next set.

```
File: apps/smart-contracts/core/contracts/interfaces/IWithdrawHook.sol
63:   /**
64:    * @notice Sets the length in seconds for which user withdraw limits will
65:    * be evaluated against. Every time `userPeriodLength` seconds passes, the
66:    * amount withdrawn for all users will be reset to 0. This amount is only
```

But the implementation only resets the amount for the first user that interacts with the contract in the new epoch and leaves all other users with their old limit. This can lead to a delay for every user that is on his limit from a previous epoch until they manage to be the first to interact with the contract in the new epoch.

### Recommended Mitigation Steps

The check how the user periods are handled need to be changed. One possible way is to change the `lastUserPeriodReset` to a mapping like `mapping(address => uint256) private lastUserPeriodReset` to track the time for every user separately.

With a mapping you can change the condition to:

```
File: apps/smart-contracts/core/contracts/WithdrawHook.sol
18:   mapping(address => uint256) lastUserPeriodReset;

File: apps/smart-contracts/core/contracts/WithdrawHook.sol
66:     if (lastUserPeriodReset[_sender] + userPeriodLength < block.timestamp) {
67:       lastUserPeriodReset[_sender] = block.timestamp;
68:       userToAmountWithdrawnThisPeriod[_sender] = _amountBeforeFee;
69:     } else {
70:       require(userToAmountWithdrawnThisPeriod[_sender] + _amountBeforeFee <= userWithdrawLimitPerPeriod, "user withdraw limit exceeded");
71:       userToAmountWithdrawnThisPeriod[_sender] += _amountBeforeFee;
72:     }
```
