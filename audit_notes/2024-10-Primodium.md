# 2024-10-Primodium
---
- Category: chose from [[protocol_categories]]
- Note Create 2025-02-24
- Platform: Pashov Audit Group
- Report Url: [2024-10-Primodium](https://github.com/pashov/audits/blob/master/team/md/Primodium-security-review_2024-10-02.md)
---
# High Risk Findings (xx)

---

## [C-02] The portion of the pot corresponding to locked points is not distributed to the players
----
- **Tags**:  #business_logic #consistency 
- Number of finders: 1
- Difficulty: Easy
---
### Description

The `withdrawEarnings` function in the `RewardsSystem` contract calculates the amount of pot to distribute to the player based on the number of points they have in the winning empire. These are some of the steps in the function:

1. Get the total points issued to the winning empire (line 131).
2. Get the player's points in the winning empire (line 136), excluding the locked points (line 137).
3. Calculate the player's share of the pot based on their points (line 142).

```
File: RewardsSystem.sol

125:   function withdrawEarnings() public _onlyGameOver {
126:     EEmpire winningEmpire = WinningEmpire.get();
127:     require(winningEmpire != EEmpire.NULL, "[RewardsSystem] No empire has won the game");
128:
129:     bytes32 playerId = addressToId(_msgSender());
130:
131:     uint256 empirePoints = Empire.getPointsIssued(winningEmpire);
132:     if (empirePoints == 0) {
133:       return;
134:     }
135:
136:     uint256 playerEmpirePoints = PointsMap.getValue(winningEmpire, playerId) -
137:       PointsMap.getLockedPoints(winningEmpire, playerId);
138:
139:     if (playerEmpirePoints == 0) return;
140:
141:     uint256 pot = (Balances.get(EMPIRES_NAMESPACE_ID));
142:     uint256 playerPot = (pot * playerEmpirePoints) / empirePoints;
143:
144:     PlayersMap.setGain(playerId, PlayersMap.get(playerId).gain + playerPot);
145:     PointsMap.remove(winningEmpire, playerId);
146:
147:     IWorld(_world()).transferBalanceToAddress(EMPIRES_NAMESPACE_ID, _msgSender(), playerPot);
148:   }
```

The issue is that `empirePoints` includes both locked and unlocked points, while `playerEmpirePoints` only includes unlocked points. This means that a portion of the pot corresponding to locked points is not distributed to the players and is locked in the contract.

Let's consider the following scenario:

- The total points issued to the winning empire is 15 and the total pot is 15 ether.
- Player A has 10 points in the winning empire, 5 of which are locked.
- Player B has 5 points in the winning empire, all unlocked.
- Player A withdraws 5 ether from the pot: `15 ether * (10 points - 5 points) / 15 points`.
- Player B withdraws 5 ether from the pot: `15 ether * 5 points / 15 points`.
- The remaining 5 ether in the pot is locked in the contract.

### Recommendations

Option 1: Unlock all points for the winning empire when the game ends. This way, the portion of the pot corresponding to locked points is distributed to the players that locked them based on their number of locked points.

Option 2: Subtract the total points locked in the winning empire from `empirePoints`. This way, the portion of the pot corresponding to locked points is distributed evenly among all players based on their number of unlocked points.

### Discussion

### Notes

#### Notes 

Option 1 : 
Player A : `15 ether * 10 points/ 15 points = 10 ether` 
Player B : `15 ether * 5 points / 15 points = 5 ether`

Option 2 : 
Player A : `15 ether * (10 points - 5 points)/ 10 points = 7.5 ether`
Player B : `15 ether * 5 points / 10 points = 7.5 ether`
#### Impressions

*The core issue stems from a mathematical and logical inconsistency in how the contract handles two related components in a fractional calculation. (especially calculating portions ore shares using fractions)*

### Tools
### Refine
- [[1-Business_Logic]]
- [[logical_issues#[03] Consistency Issues]]
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