## Examine all the paths that can modify or read these critical state variables. Create a flow diagram showing:

1. How values get updated
2. When they can be read
3. What checks are performed before access
4. What other state variables influence these operations


### Example
- [[2023-06-angle#[H-03] Poor detection of disputed trees allows claiming tokens from a disputed tree]]


## Access controls based on temporary or easily acquirable tokens don't provide effective protection against malicious behavior when there's no permanent cost or risk to the attacker.

In robust security designs, any action with potential for system disruption should require one or more of:

1. **Locked value at risk**: Require users to have something meaningful at stake that they could lose if they act maliciously.
2. **Permanent privileges**: Restrict sensitive operations to entities with long-term alignment with the protocol (like governance participants or verified stakeholders).
3. **Time-based constraints**: Include mechanisms that prevent rapid manipulation of the system (like lockup periods or rate limits).
4. **Incentive alignment**: Ensure that the economic incentives of all participants discourage harmful actions.

### How to Find Similar Issues in Future Audits

When conducting future audits, look for:

1. **Weak authorization checks**: Functions that rely solely on token balances, especially those that can be temporarily acquired.
2. **Lack of time constraints**: Operations that can be performed repeatedly without cooling-off periods.
3. **Misaligned incentives**: Situations where users can benefit from or remain unharmed by actions that harm the protocol.
4. **Griefing vectors**: Functions that allow users to prevent others from using the protocol normally without significant cost to themselves.
5. **Circular dependencies**: Cases where acquiring a privilege and relinquishing it can be done in quick succession with minimal cost.

### Example
- [[2022-11-stakehouse#[M-30] Giant pools are prone to user griefing, preventing their holdings from being staked]]