*Summary from typical issues.*
# Typical Common Issues

- Check all code related to funds
- Check the updates of states  
	- Correctness of the update.
	- Whether all updates have been made.
	- [[2023-02-astaria#[H-03] `VaultImplementation.buyoutLien` does not update the new public vault's parameters and does not transfer assets between the vault and the borrower|[H-03] `VaultImplementation.buyoutLien` does not update the new public vault's parameters and does not transfer assets between the vault and the borrower]]
- Check multiplications calculations are stored in limited-size integers
- Precision Loss and  Insufficient Precision
	- Always be aware of the potential loss of precision caused by division operations.
	- Pay special attention to all calculation logics involving division during auditing.
	- Hidden "division before a multiplication"
		- Track the **complete** calculation process of variables
- Compare similar functions
	1. **Cross-contract Comparisons**: Compare related contracts for inconsistencies in key functionalities.
	2. **Key Functions**: Focus on critical operations such as `withdraw`, `deposit`, or similar sensitive actions.
	3. **Validation Checks**: Look for missing or inconsistent validations, especially regarding access control or permissions.
- Data Validation 
	- Verifying input parameter constraints
	- Checking for proper data range and type validations
- edge cases
	- full-byte parameters
	- `new ExpirationPeriod window < current time < new ExpirationPeriod window`  - [[2024-10-kleidi#[M-03] `UpdateExpirationPeriod()` cannot be executed when the `newExpirationPeriod` is less than `currentExpirationPeriod`| `UpdateExpirationPeriod()` cannot be executed when the `newExpirationPeriod` is less than `currentExpirationPeriod`]]
- Check basic functions
	- `receive` and `withraw` - [[2023-07-baton_launchpad#[H-01] Protocol fees from NFT mints can't be claimed in `BatonLaunchpad`|[H-01] Protocol fees from NFT mints can't be claimed in `BatonLaunchpad`]]
- Verify that reward accounting remains accurate if reward tokens are added/removed from underlying protocols.
	- [[2023-04-blueberry#[M-12] `rewardTokens` removed from `WAuraPool/WConvexPools` will be lost forever|[M-12] `rewardTokens` removed from `WAuraPool/WConvexPools` will be lost forever]]
- Cached Value
	- Identify it
	- Check it
	- [[2023-03-Morpho#[M-14] Compound liquidity computation uses outdated cached borrowIndex]]
- When auditing transactions within a `for-loop`
	- [[2023-02-clober#[M-01] Group claim clashing condition|[M-01] Group claim clashing condition]]
- Check whether time-based epochs increase as expected
	- Epoch/period increments
	- Required sequential processing
	- Blocking conditions
	- [[2023-02-astaria#[H-11] `processEpoch()` needs to be called regularly[H-11] `processEpoch()` needs to be called regularly]]
- Check array parameter types (memory vs storage)
	- [[2023-02-astaria#[H-10] Refactor `_paymentAH()`]]
- Check  `msg.sender`, `account`, `owner`, `receiver`
	- `owner ≠ msg.sender`
		- [[2023-02-astaria#[M-10] `redeemFutureEpoch` transfers the shares from the `msg.sender` to the vault instead of from the `owner`||[M-10] `redeemFutureEpoch` transfers the shares from the `msg.sender` to the vault instead of from the `owner`]]
	- flash loan `receiver` -> `msg.sender`
		- [[2023-06-lybra#[H-01] There is a vulnerability in the `executeFlashloan` function of the `PeUSDMainnet` contract. Hackers can use this vulnerability to burn other people's eUSD token balance without permission|[H-01] There is a vulnerability in the `executeFlashloan` function of the `PeUSDMainnet` contract. Hackers can use this vulnerability to burn other people's eUSD token balance without permission]]
	- `account` ->`msg.sender`
		- [[2022-11-backed#[M-05] `PaprController.buyAndReduceDebt msg.sender` can lose paper by paying the debt twice|[M-05] `PaprController.buyAndReduceDebt msg.sender` can lose paper by paying the debt twice]]
	- Balance account -> msg.sender
		- [[2022-12-connext#[H-01] `swapInternal()` shouldn't use `msg.sender`|[H-01] `swapInternal()` shouldn't use `msg.sender`]]
- Check whether crucial parameters have limits.
	- Reward rates/speeds
		- [[2023-01-popcorn#[H-09] Attacker can steal 99% of total balance from any reward token in any Staking contract|[H-09] Attacker can steal 99% of total balance from any reward token in any Staking contract]]
	- Interest rates
	- Exchange rates
	- Fee percentages
	- Time periods
	- Withdrawal limits
- Check financial calculation 
	- we should repeatedly verify whether the financial calculations(such as interest and fees) are correctly implemented in the code during future audit tasks.
		- [[2023-02-astaria#[H-20] `commitToLiens` transfers extra assets to the borrower when protocol fee is present|[H-20] `commitToLiens` transfers extra assets to the borrower when protocol fee is present]]
	- Error Type: Part for Whole
		- [[2023-01-ajna#[M-04] Incorrect MOMP calculation in neutral price calculation|[M-04] Incorrect MOMP calculation in neutral price calculation]]
	- #Double-check_the_complex_calculation #loan_with_interest
		- [[2022-11-isomorph#[H-02] The calculation of `totalUSDborrowed` in `openLoan()` is not correct|[H-02] The calculation of `totalUSDborrowed` in `openLoan()` is not correct]]
- Danger of `delete` on Structs
	- In Solidity, when you delete a struct from storage, all its fields are reset to their default values. So loan.lender becomes address(0) because that's the default for address types.
	- [[2023-01-cooler#[H-03] Fully repaying a loan will result in debt payment being lost|[H-03] Fully repaying a loan will result in debt payment being lost]]
- Funds First, Delete Last
	- **Always finalize financial transactions** _before_ modifying or deleting state variables they depend on.
	- [[2023-01-cooler#[H-03] Fully repaying a loan will result in debt payment being lost|[H-03] Fully repaying a loan will result in debt payment being lost]]
- *Double-check the complex calculation*
	- [[2023-01-UXD#[M-06] Inaccurate Perp debt calculation|[M-06] Inaccurate Perp debt calculation]]
- Check Array Index
	- [[2022-12-liquid-collective#[H-2] Order of calls to `removeValidators` can affect the resulting validator keys set]]
	- [[2023-02-astaria#[H-10] Refactor `_paymentAH()`]]
	- [[2023-02-seaport#[M-04] Advance orders of CONTRACT order types can generate orders with less consideration items that would break the aggregation routine]]
	- [[2023-05-liquid_collective#[H-01] `_pickNextValidatorsToExitFromActiveOperators` uses the wrong index to query stopped validator]]
- How subtraction is used in comparison logic.
	*Mathematical equivalence doesn't mean functional equivalence.*
	- [[2022-12-liquid-collective#[C-3] `OperatorsRegistry._getNextValidatorsFromActiveOperators` can DOS Alluvial staking if there's an operator with `funded==stopped` and `funded == min(limit, keys)`]]
- Ensure all potential contributions to a final outcome are fully accounted for before making irreversible decisions.
	- [[2022-11-backed#[H-01] Borrowers may earn auction proceeds without filling the debt shortfall]]
- When a system has multiple functions that operate on the same resource, but implements authorization/validation checks inconsistently across those functions, security gaps emerge.
	- Checks when adding but missing checks when updating (increasing)
	- `Adding logic = Increasing logic`
	- [[2022-11-backed#[M-02] Disabled NFT collateral should not be used to mint debt]]
- Check transfer process
	- #transfer_vs_transferFrom 
	- [[2022-11-backed#[M-06] `PaprController` pays swap fee in `buyAndReduceDebt`, not user|[M-06] `PaprController` pays swap fee in `buyAndReduceDebt`, not user]]
- Smart contracts should implement complete lifecycle management for all critical system components
	1. Initialization mechanisms
	2. Update mechanisms
	3. Removal/deprecation mechanisms
	4. Emergency pause/shutdown mechanisms
	5. [[2022-12-connext#[H-7] No way to update a Stable Swap once assigned to a key|[H-7] No way to update a Stable Swap once assigned to a key]]
	6. [[2022-12-connext#[H-09] No way of removing Fraudulent Roots|[H-09] No way of removing Fraudulent Roots]]
- The balances maintained by ERC20 contract are considered trustworthy. 代币合约中的余额更可信。
	- [[2022-12-maple#[M-03] Unaccounted collateral is mishandled in `triggerDefault`|[M-03] Unaccounted collateral is mishandled in `triggerDefault`]]
# Typical Logical Issues

- Process Control Points vs. System Control Points
	- Interval calculation boundary alignment
	- Compare `@natspec` and code comment with actual implementation code
- Consistency
	- Look for multiple functions with similar names or purposes
    - Identify operations that handle the same business logic
    - Search for duplicated code with slight variations
    - Check for similar state mutations across different functions
    - Review functions that interact with the same state variables
- Multi-Step Bypass vie OR logic
	- Find all `OR` (`||`) condition in access controls
	- Can satisfying one condition affect other conditions?
	- Map out the relationship between each condition: `Condition A -> Changes State -> Enables Condition B?`
	- Try two-step attack

## Uniswap V3

- Different pool have different `sqrtPriceLimitX96` (**maximum/minimum price** a swap will accept)
	- [[2023-01-UXD#[M-02] `PerpDepository._rebalanceNegativePnlWithSwap()` shouldn't use a `sqrtPriceLimitX96` twice.]]