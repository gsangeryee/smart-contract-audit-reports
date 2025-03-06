# Financial Bypass
## The General Principle

When a financial protocol has functions that can be called directly (no access control) that handle value but don't properly update internal accounting systems, critical financial invariants can break.

## Key Characteristics to Look For:

1. **Public/External Functions Without Access Control**: Especially those that handle rewards, withdrawals, or value transfers
2. **Disconnected Accounting Flows**: When claiming/transferring value is separate from updating internal records
3. **Composable Systems**: Where user actions can occur through multiple entry points (direct contract calls vs. using a management interface)
4. **Indirect Value Tracking**: Systems that don't directly track token balances but rely on separate accounting mechanisms
    

## Questions to Ask During Audits:

1. "Can a third party trigger financial operations on behalf of another user?"
2. "If they do, will all accounting systems properly update?"
3. "Are there separate paths for the same financial operation with different side effects?"
4. "What assumptions does the system make about which contract interfaces users will use?"
    
## Similar Vulnerability Patterns:

- Reward systems where claiming and accounting are separate
	- [[2022-12-sentiment#[M-01] `getRewards()` can be triggered by external parties which will result in the rewards not be tracking properly by the system]]
	- [[2022-11-redactedcartel#[H-06] fee loss in `AutoPxGmx` and `AutoPxGlp` and reward loss in `AutoPxGlp` by calling `PirexRewards.claim(pxGmx/pxGpl, AutoPx*)` directly which transfers rewards to `AutoPx`* pool without compound logic get executed and fee calculation logic and `pxGmx` wouldn't be executed for those rewards]]
- Withdrawal functions that can bypass fee collection
- Rebasing tokens where balance snapshots can be manipulated
- Staking systems where third parties can force unstaking without proper accounting

This class of issues arises when developers assume users will follow a specific path through the system, but smart contracts allow multiple execution paths to the same end state with different accounting effects.