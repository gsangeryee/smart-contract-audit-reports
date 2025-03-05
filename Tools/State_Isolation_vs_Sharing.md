
One way to think about this is to ask for each variable: "Is this tracking something about a specific user, or about the system as a whole?"

- **System-wide variables** should be shared (total deposits, global pauses)
- **User-specific variables** should be isolated (withdrawal limits, balances)

In the contract we analyzed, they incorrectly treated individual user reset periods as a system-wide variable, creating unfair competition between users.

## Cases

- [[2022-12-prePO#[H-01] griefing / blocking / delaying users to withdraw]]