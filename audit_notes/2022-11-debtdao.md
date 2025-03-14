# 2022-11-debtdao
---
- Category: #Dexes #services #liquidity_manager #payments #rwa_lending 
- Note Create 2025-03-13
- Platform: Code4rena
- Report Url: [2022-11-debtdao](https://code4rena.com/reports/2022-11-debtdao)
---
# Critical & High Risk Findings (xx)

---
## [H-01] Call to `declareInsolvent()` would revert when contract status reaches liquidation point after repayment of credit position 1
----
- **Tags**:  #business_logic #liquidation 
- Number of finders: 6
- Difficulty: Medium
---
### Lines of code

[declareInsolvent()](https://github.com/debtdao/Line-of-Credit/blob/e8aa08b44f6132a5ed901f8daa231700c5afeb3a/contracts/modules/credit/LineOfCredit.sol#L143-L155)
```solidity
    function declareInsolvent() external whileBorrowing returns(bool) {
        if(arbiter != msg.sender) { revert CallerAccessDenied(); }
        if(LineLib.STATUS.LIQUIDATABLE != _updateStatus(_healthcheck())) {
            revert NotLiquidatable();
        }
        if(_canDeclareInsolvent()) {
            _updateStatus(LineLib.STATUS.INSOLVENT);
            return true;
        } else {
          return false;
        }
    }
```

[whileBorrowing](https://github.com/debtdao/Line-of-Credit/blob/e8aa08b44f6132a5ed901f8daa231700c5afeb3a/contracts/modules/credit/LineOfCredit.sol#L83-L86)
```solidity
    modifier whileBorrowing() {
        if(count == 0 || credits[ids[0]].principal == 0) { revert NotBorrowing(); }
        _;
    }
```
### Impact

The modifier `whileBorrowing()` is used along in the call to `LineOfCredit.declareInsolvent()`. However this check reverts when `count == 0` or `credits[ids[0]].principal == 0` . Within the contract, any lender can add credit which adds an entry in credits array, `credits[ids]`.

Assume, when borrower chooses lender positions including `credits[ids[0]]` to draw on, and repays back the loan fully for `credits[ids[1]]`, then the call to `declareInsolvent()` by the arbiter would revert since it does not pass the `whileBorrowing()` modifier check due to the ids array index shift in the call to `stepQ()`, which would shift `ids[1]` to `ids[0]`, thereby making the condition for `credits[ids[0]].principal == 0` be true causing the revert.
### Proof of Concept

1. LineOfCredit contract is set up and 5 lenders have deposited into the contract.
2. Alice, the borrower borrows credit from these 5 credit positions including by calling `LineOfCredit.borrow()` for the position ids.
3. Later Alice pays back the loan for credit position id 1 just before the contract gets liquidated
4. At the point where `ids.stepQ()` is called in` _repay()`, position 1 is moved to `ids[0]`
5. When contract status is `LIQUIDATABLE`, no loan drawn on credit `position 0` and arbiter calls `declareInsolvent()` , the call would revert since `credits[ids[0]].principal == 0`
### Recommended Mitigation

The modifier `whileBorrowing()` would need to be reviewed and amended.
### Discussion

### Notes

????
Hi, I am studying the audit reports. After a detailed analysis, I have a question about this finding. The `stepQ()` function ensures that ids[0] always points to an active credit position if any exist, satisfying the whileBorrowing() modifier’s conditions.

```solidity
        // we never check the first id, because we already know it's null
        for (uint i = 1; i < len; ) {
            if (ids[i] != bytes32(0)) {.  //@aduit-info.  ids[i] not null
                (ids[0], ids[i]) = (ids[i], ids[0]); // swap the ids in storage
                emit SortedIntoQ(ids[0], 0, i, ids[i]);
                return true; // if we make the swap, return early
            }
            unchecked {
                ++i;
            }
        }
```

So,

> 4. At the point where ids.stepQ() is called in _repay(), position 1 is moved to ids[0]

if `ids[0]` and `ids[1]` are both ZERO, position1 is not moved to ids[0].

As a result, the `declareInsolvent()` function should not revert when active borrowings are present.

Please let me know if you’d like to discuss this further. Thanks

### Tools
### Refine

{{ Refine to typical issues}}

---
## [H-02] Non-existing revenue contract can be passed to `claimRevenue` to send all tokens to treasury
----
- **Tags**: #business_logic #validation 
- Number of finders: 4
- Difficulty: Medium
---
### Detail

Neither `SpigotLib.claimRevenue` nor `SpigotLib._claimRevenue` check that the provided `revenueContract` was registered before. If this is not the case, `SpigotLib._claimRevenue` assumes that this is a revenue contract with push payments (because `self.settings[revenueContract].claimFunction` is 0) and just returns the difference since the last call to `claimRevenue`:

```solidity
       if(self.settings[revenueContract].claimFunction == bytes4(0)) {
            // push payments

            // claimed = total balance - already accounted for balance
            claimed = existingBalance - self.escrowed[token]; //@audit Rebasing tokens
            // underflow revert ensures we have more tokens than we started with and actually claimed revenue
        }
```

`SpigotLib.claimRevenue` will then read `self.settings[revenueContract].ownerSplit`, which is 0 for non-registered revenue contracts:

```solidity
uint256 escrowedAmount = claimed * self.settings[revenueContract].ownerSplit / 100;
```

Therefore, the whole `claimed` amount is sent to the treasury.

This becomes very problematic for revenue tokens that use push payments. An attacker (in practice the borrower) can just regularly call `claimRevenue` with this token and a non-existing revenue contract. All of the tokens that were sent to the spigot since the last call will be sent to the treasury and none to the escrow, i.e. a borrower can ensure that no revenue will be available for the lender, no matter what the configured split is.
### Proof of Concept

As mentioned above, the attack pattern works for arbitrary tokens where one (or more) revenue contracts use push payments, i.e. where the balance of the Spigot increases from time to time. Then, the attacker just calls `claimRevenue` with a non-existing address. This is illustrated in the following diff:

```
--- a/contracts/tests/Spigot.t.sol
+++ b/contracts/tests/Spigot.t.sol
@@ -174,7 +174,7 @@ contract SpigotTest is Test {
         assertEq(token.balanceOf(address(spigot)), totalRevenue);
         
         bytes memory claimData;
-        spigot.claimRevenue(revenueContract, address(token), claimData);
+        spigot.claimRevenue(address(0), address(token), claimData);
```

Thanks to this small modification, all of the tokens are sent to the treasury and none are sent to the escrow.
### Recommended Mitigation

Check that a revenue contract was registered before, revert if it does not.
### Discussion

### Notes

Always validate that entities referenced in system operations actually exist within the system before performing operations based on their properties.

In essence, **never trust that an address or identifier passed to a function corresponds to a previously registered or valid entity without explicit verification**.

### Tools
### Refine

- [[1-Business_Logic]]
- [[2-Validation]]

---
## [H-03] `addCredit` / `increaseCredit` cannot be called by lender first when token is ETH
----
- **Tags**: #business_logic #mutual_consent
- Number of finders: 6
- Difficulty: Medium
---
### Impact

The functions `addCredit` and `increaseCredit` both have a `mutualConsent` or `mutualConsentById` modifier. Furthermore, these functions are `payable` and the lender needs to send the corresponding ETH with each call. However, if we look at the mutual consent modifier works, we can have a problem:

```solidity
modifier mutualConsent(address _signerOne, address _signerTwo) {
      if(_mutualConsent(_signerOne, _signerTwo))  {
        // Run whatever code needed 2/2 consent
        _;
      }
}

function _mutualConsent(address _signerOne, address _signerTwo) internal returns(bool) {
        if(msg.sender != _signerOne && msg.sender != _signerTwo) { revert Unauthorized(); }
        address nonCaller = _getNonCaller(_signerOne, _signerTwo);
        // The consent hash is defined by the hash of the transaction call data and sender of msg,
        // which uniquely identifies the function, arguments, and sender.
        bytes32 expectedHash = keccak256(abi.encodePacked(msg.data, nonCaller));
        if (!mutualConsents[expectedHash]) {
            bytes32 newHash = keccak256(abi.encodePacked(msg.data, msg.sender));
            mutualConsents[newHash] = true;
            emit MutualConsentRegistered(newHash);
            return false;
        }
        delete mutualConsents[expectedHash];
        return true;
}
```

The problem is: On the first call, when the other party has not given consent to the call yet, the modifier does not revert. It sets the consent of the calling party instead.

This is very problematic in combination with sending ETH for two reasons:

1. When the lender performs the calls first and sends ETH along with the call, the call will not revert. It will instead set the consent for him, but the sent ETH is lost.
    
2. Even when the lender thinks about this and does not provide any ETH on the first call, the borrower has to perform the second call. Of course, he will not provide the ETH with this call, but this will cause the transaction to revert. There is now no way for the borrower to also grant consent, but still let the lender perform the call.
### Proof of Concept

Lender Alice calls `LineOfCredit.addCredit` first to add a credit with 1 ETH. She sends 1 ETH with the call. However, because borrower Bob has not performed this call yet, the function body is not executed, but the 1 ETH is still sent. Afterwards, Bob wants to give his consent, so he performs the same call. However, this call reverts, because Bob does not send any ETH with it.
### Recommended Mitigation

Consider implementing an external function to grant consent to avoid this scenario. Also consider reverting when ETH is sent along, but the other party has not given their consent yet.
### Discussion

### Notes

#### The Mutual Consent System Explained

The smart contract uses a mutual consent system that requires two specific addresses (typically the lender and borrower) to approve certain operations before they can be executed. This process works in two steps:

##### Step 1: First Party Registers Consent

When the first party (let's call them Alice) calls a function with the `mutualConsent` modifier:

```solidity
function addCredit(address token, uint256 amount) external payable mutualConsent(lender, borrower) {
    // Function body that adds credit
}
```

The `mutualConsent` modifier executes the following logic:

1. It first checks if the caller is one of the authorized parties:
    ```solidity
    if(msg.sender != signerOne && msg.sender != signerTwo) { revert Unauthorized(); }
    ```
2. It identifies the other party who needs to consent:
    ```solidity
    address nonCaller = getNonCaller(signerOne, signerTwo);
    ```
    
3. It calculates a hash that represents "the other party consenting to this exact function call":
    ```solidity
    bytes32 expectedHash = keccak256(abi.encodePacked(msg.data, nonCaller));
    ```
    
4. It checks if this hash exists in the `mutualConsents` mapping. Since this is the first call, it doesn't exist yet:
    ```solidity
    if (!mutualConsents[expectedHash]) {
        // Create a new hash that represents "I (the caller) consent to this exact function call"
        bytes32 newHash = keccak256(abi.encodePacked(msg.data, msg.sender));
        mutualConsents[newHash] = true;
        emit MutualConsentRegistered(newHash);
        return false;  // Important: returns false, which prevents function body execution
    }
    ```
    
5. The function body is not executed (because of the `return false`), but the transaction completes successfully. Alice's consent is now registered in the `mutualConsents` mapping.
##### Step 2: Second Party Completes the Consent Process

When the second party (let's call them Bob) calls the exact same function with identical arguments:

1. The modifier again checks if the caller is authorized (Bob is).
2. It calculates the hash that represents "Alice consenting to this function call":
    ```solidity
    bytes32 expectedHash = keccak256(abi.encodePacked(msg.data, Alice's address));
    ```
    
3. It checks if this hash exists in the `mutualConsents` mapping. Since Alice already registered her consent, this is true:
    ```solidity
    if (!mutualConsents[expectedHash]) {
        // This branch is not executed since the hash exists
    }
    ```
    
4. The modifier deletes the consent hash (consumption) and returns true:
    ```solidity
    delete mutualConsents[expectedHash];
    return true;  // Important: returns true, which allows function body execution
    ```
    
5. The function body is now executed because the modifier returned `true`.
##### Example: The ETH Transfer Problem

Now let's see why this is problematic with ETH transfers:

##### Scenario: Adding ETH Credit

Let's say Alice (the lender) wants to add 1 ETH credit to the line of credit. The function signature is:

```solidity
function addCredit(address token, uint256 amount) external payable mutualConsent(lender, borrower) {
    // Credit addition logic
    // Uses msg.value for the ETH amount
}
```

##### Step 1: Alice Calls First

Alice calls `addCredit(ETH_ADDRESS, 1 ether)` and sends 1 ETH with the transaction:

1. The `mutualConsent` modifier executes and registers Alice's consent.
2. The modifier returns `false`, preventing the function body from executing.
3. **BUT the 1 ETH is still sent to the contract**, as the transaction completed successfully.
4. This ETH is now locked in the contract, but not properly accounted for.

##### Step 2: Bob Attempts to Complete the Consent

Bob now needs to call the same function to complete the consent process:

1. Bob calls `addCredit(ETH_ADDRESS, 1 ether)` but doesn't send any ETH (why would he? It's Alice's ETH).
2. The `mutualConsent` modifier executes and finds Alice's consent hash.
3. The modifier returns `true`, allowing the function body to execute.
4. The function body attempts to use `msg.value` for the ETH amount, but since Bob didn't send any ETH, this value is 0.
5. The transaction either reverts due to insufficient funds or incorrectly processes the credit with 0 ETH.

##### The Deadlock

This creates a deadlock:

- If Alice sends ETH first, it gets locked in the contract without being properly accounted for.
- If Bob attempts to complete the consent, he either needs to send ETH himself (which he shouldn't have to) or the transaction reverts.

This design flaw means that for ETH transfers, the mutual consent system simply doesn't work as intended. It's especially problematic because:

1. The first party loses their ETH even though the actual function body never executes.
2. The second party cannot complete the consent process without also sending ETH (which makes no sense in this context).

The issue highlights how important it is to properly separate the consent logic from the asset transfer logic, especially when dealing with native assets like ETH that are transferred as part of the transaction itself.

#### Impression
#### State Management Should Account for Asset Transfer Patterns

This vulnerability illustrates an important security principle: **When designing multi-step transaction processes involving asset transfers, ensure that assets are only transferred during the execution phase, not during intermediate approval steps.**

More specifically: **Mutual consent mechanisms must be carefully designed to separate approval logic from asset transfer logic, especially when dealing with native assets like ETH.**
### Tools
- [[Mutual_Consent]]
### Refine

- [[1-Business_Logic]]

---
## [H-04] Borrower can close a credit without repaying debt
----
- **Tags**: #business_logic #validation 
- Number of finders: 7
- Difficulty: Medium
---
### Detail

A borrower can close a credit without repaying the debt to the lender. The lender will be left with a bad debt and the borrower will keep the borrowed amount and the collateral.
### Proof of Concept

The `close` function of `LineOfCredit` doesn't check whether a credit exists or not. As a result, the `count` variable is decreased in the internal `_close` function when the `close` function is called with an non-existent credit ID: [LineOfCredit.sol#L388](https://github.com/debtdao/Line-of-Credit/blob/e8aa08b44f6132a5ed901f8daa231700c5afeb3a/contracts/modules/credit/LineOfCredit.sol#L388):

```solidity
function close(bytes32 id) external payable override returns (bool) {
    Credit memory credit = credits[id];
    address b = borrower; // gas savings
    if(msg.sender != credit.lender && msg.sender != b) {
      revert CallerAccessDenied();
    }

    // ensure all money owed is accounted for. Accrue facility fee since prinicpal was paid off
    credit = _accrue(credit, id);
    uint256 facilityFee = credit.interestAccrued;
    if(facilityFee > 0) {
      // only allow repaying interest since they are skipping repayment queue.
      // If principal still owed, _close() MUST fail
      LineLib.receiveTokenOrETH(credit.token, b, facilityFee);
      credit = _repay(credit, id, facilityFee);
    }
    _close(credit, id); // deleted; no need to save to storage
    return true;
}
```

[LineOfCredit.sol#L483](https://github.com/debtdao/Line-of-Credit/blob/e8aa08b44f6132a5ed901f8daa231700c5afeb3a/contracts/modules/credit/LineOfCredit.sol#L483):

```solidity
function _close(Credit memory credit, bytes32 id) internal virtual returns (bool) {
    if(credit.principal > 0) { revert CloseFailedWithPrincipal(); }
    // return the Lender's funds that are being repaid
    if (credit.deposit + credit.interestRepaid > 0) {
        LineLib.sendOutTokenOrETH(
            credit.token,
            credit.lender,
            credit.deposit + credit.interestRepaid
        );
    }
    delete credits[id]; // gas refunds
    // remove from active list
    ids.removePosition(id);
    unchecked { --count; }
    // If all credit lines are closed the the overall Line of Credit facility is declared 'repaid'.
    if (count == 0) { _updateStatus(LineLib.STATUS.REPAID); }
    emit CloseCreditPosition(id);
    return true;
}
```

Proof of Concept:

```solidity
// contracts/tests/LineOfCredit.t.sol
function testCloseWithoutRepaying_AUDIT() public {
    assertEq(supportedToken1.balanceOf(address(line)), 0, "Line balance should be 0");
    assertEq(supportedToken1.balanceOf(lender), mintAmount, "Lender should have initial mint balance");
      
    _addCredit(address(supportedToken1), 1 ether);
    bytes32 id = line.ids(0);
    assert(id != bytes32(0));
    assertEq(supportedToken1.balanceOf(lender), mintAmount - 1 ether, "Lender should have initial balance less lent amount");
    
    hoax(borrower);
    line.borrow(id, 1 ether);
    assertEq(supportedToken1.balanceOf(borrower), mintAmount + 1 ether, "Borrower should have initial balance + loan");
    
    // The credit hasn't been repaid.
    // hoax(borrower);
    // line.depositAndRepay(1 ether);
    
    hoax(borrower);
    // Closing with a non-existent credit ID.
    line.close(bytes32(uint256(31337)));
    // The debt hasn't been repaid but the status is REPAID.
    assertEq(uint(line.status()), uint(LineLib.STATUS.REPAID));
    // Lender's balance is still reduced by the borrow amount.
    assertEq(supportedToken1.balanceOf(lender), mintAmount - 1 ether);
    // Borrower's balance still includes the borrowed amount.
    assertEq(supportedToken1.balanceOf(borrower), mintAmount + 1 ether);
}
```
### Recommended Mitigation

In the `close` function of `LineOfCredit`, consider ensuring that a credit with the user-supplied ID exists, before closing it.
### Discussion

### Notes

#### The Normal Flow

In a properly functioning system, the credit lifecycle should work like this:

1. A lender adds credit (deposits funds)
2. A borrower borrows against this credit
3. The borrower repays the principal and interest
4. Either party can close the credit position once fully repaid
#### Impressions
***Input validation must be performed on all external inputs, especially those that control system state transitions.***
### Tools
### Refine
- [[1-Business_Logic]]
- [[2-Validation]]

---
## [H-05] Borrower can craft a borrow that cannot be liquidated, even by arbiter.
----
- **Tags**: #business_logic 
- Number of finders: 2
- Difficulty: Hard
---
### Detail

`LineOfCredit` manages an array of open credit line identifiers called `ids`. Many interactions with the Line operate on `ids[0]`, which is presumed to be the oldest borrow which has non zero principal. For example, borrowers must first deposit and repay to `ids[0]` before other credit lines. 

The list is managed by several functions:

1. `CreditListLib.removePosition` - deletes parameter id in the ids array
2. `CreditListLib.stepQ` - rotates all ids members one to the left, with the leftmost becoming the last element
3. `_sortIntoQ` - most complex function, finds the smallest index which can swap identifiers with the parameter id, which satisfies the conditions:
    1. target index is not empty
    2. there is no principal owed for the target index's credit

`_sortIntQ()`
```solidity
    function _sortIntoQ(bytes32 p) internal returns (bool) {
        uint256 lastSpot = ids.length - 1;
        uint256 nextQSpot = lastSpot;
        bytes32 id;
        for (uint256 i; i <= lastSpot; ++i) {
            id = ids[i];
            if (p != id) {
                if (
                  id == bytes32(0) ||       // deleted element. In the middle of the q because it was closed.
                  nextQSpot != lastSpot ||  // position already found. skip to find `p` asap
                  credits[id].principal > 0 //`id` should be placed before `p` 
                ) continue;
                nextQSpot = i;              // index of first undrawn line found
            } else {
                if(nextQSpot == lastSpot) return true; // nothing to update
                // swap positions
                ids[i] = ids[nextQSpot];    // id put into old `p` position
                ids[nextQSpot] = p;         // p put at target index
                return true; 
            }
          
        }
    }
```
The idea I had is that if we could corrupt the ids array so that `ids[0]` would be zero, but after it there would be some other active borrows, it would be a very severe situation. The `whileBorrowing()` modifier assumes if the first element has no principal, borrower is not borrowing.

```solidity
modifier whileBorrowing() {
    if(count == 0 || credits[ids[0]].principal == 0) { revert NotBorrowing(); }
    _;
}
```

It turns out there is a simple sequence of calls which allows borrowing while `ids[0]` is deleted, and does not re-arrange the new borrow into `ids[0]`!

1. `id1 = addCredit()` - add a new credit line, a new `id` is pushed to the end of `ids` array.
2. `id2 = addCredit()` - called again, `ids.length = 2`
3. `close(id1)` - calls `removePosition()` on` id1`, now ids array is `[0x000000000000000000000000, id2 ]`
4. borrow(id2) - will borrow from id2 and call `_sortIntoQ`. The sorting loop will not find another index other than `id2's` existing index (`id == bytes32(0)` is true).

From this sequence, we achieve a borrow while `ids[0]` is `0`! Therefore, `credits[ids[0]].principal = credits[0].principal = 0`, and `whileBorrowing()` reverts.

The impact is massive - the following functions are disabled:
- `SecureLine::liquidate()`
- `LineOfCredit::depositAndClose()`
- `LineOfCredit::depositAndRepay()`
- `LineOfCredit::claimAndRepay()`
- `LineOfCredit::claimAndTrade()`
### Impact

Borrower can craft a borrow that cannot be liquidated, even by arbiter. Alternatively, functionality may be completely impaired through no fault of users.
### Proof of Concept

Copy the following code into `LineOfCredit.t.sol`

```solidity
function _addCreditLender2(address token, uint256 amount) public {
    // Prepare lender 2 operations, does same as mintAndApprove()
    address lender2 = address(21);
    deal(lender2, mintAmount);
    supportedToken1.mint(lender2, mintAmount);
    supportedToken2.mint(lender2, mintAmount);
    unsupportedToken.mint(lender2, mintAmount);
    vm.startPrank(lender2);
    supportedToken1.approve(address(line), MAX_INT);
    supportedToken2.approve(address(line), MAX_INT);
    unsupportedToken.approve(address(line), MAX_INT);
    vm.stopPrank();
    // addCredit logic
    vm.prank(borrower);
    line.addCredit(dRate, fRate, amount, token, lender2);
    vm.stopPrank();
    vm.prank(lender2);
    line.addCredit(dRate, fRate, amount, token, lender2);
    vm.stopPrank();
}
function test_attackUnliquidatable() public {
    bytes32 id_1;
    bytes32 id_2;
    _addCredit(address(supportedToken1), 1 ether);
    _addCreditLender2(address(supportedToken1), 1 ether);
    id_1 =  line.ids(0);
    id_2 =  line.ids(1);
    hoax(borrower);
    line.close(id_1);
    hoax(borrower);
    line.borrow(id_2, 1 ether);
    id_1 =  line.ids(0);
    id_2 = line.ids(1);
    console.log("id1 : ", uint256(id_1));
    console.log("id2 : ", uint256(id_2));
    vm.warp(ttl+1);
    assert(line.healthcheck() == LineLib.STATUS.LIQUIDATABLE);
    vm.expectRevert(ILineOfCredit.NotBorrowing.selector);
    bool isSolvent = line.declareInsolvent();
}
```
### Recommended Mitigation

When sorting new borrows into the `ids` queue, do not skip any elements.
### Discussion

### Notes

Index-Dependent Validation Vulnerability

### Tools
### Refine

- [[1-Business_Logic]]

---
# Medium Risk Findings (xx)

---
## [M-02] Mutual consent cannot be revoked and stays valid forever
----
- **Tags**: #business_logic #mutual_consent 
- Number of finders: 7
- Difficulty: Easy
---
### Links:

[`MutualConsent` contract](https://github.com/debtdao/Line-of-Credit/blob/e8aa08b44f6132a5ed901f8daa231700c5afeb3a/contracts/utils/MutualConsent.sol#L11-L68)
```solidity
abstract contract MutualConsent {
    /* ============ State Variables ============ */
    // Mapping of upgradable units and if consent has been initialized by other party
    mapping(bytes32 => bool) public mutualConsents;
    error Unauthorized();

    /* ============ Events ============ */
    event MutualConsentRegistered(
        bytes32 _consentHash
    );

    /* ============ Modifiers ============ */
    /**
    * @notice - allows a function to be called if only two specific stakeholders signoff on the tx data
    *         - signers can be anyone. only two signers per contract or dynamic signers per tx.
    */
    modifier mutualConsent(address _signerOne, address _signerTwo) {
      if(_mutualConsent(_signerOne, _signerTwo))  {
        // Run whatever code needed 2/2 consent
        _;
      }
    }

    function _mutualConsent(address _signerOne, address _signerTwo) internal returns(bool) {
        if(msg.sender != _signerOne && msg.sender != _signerTwo) { revert Unauthorized(); }
        address nonCaller = _getNonCaller(_signerOne, _signerTwo);
        // The consent hash is defined by the hash of the transaction call data and sender of msg,
        // which uniquely identifies the function, arguments, and sender.
        bytes32 expectedHash = keccak256(abi.encodePacked(msg.data, nonCaller));
        if (!mutualConsents[expectedHash]) {
            bytes32 newHash = keccak256(abi.encodePacked(msg.data, msg.sender));
            mutualConsents[newHash] = true;
            emit MutualConsentRegistered(newHash);
            return false;
        }
        delete mutualConsents[expectedHash];
        return true;
    }
    
    /* ============ Internal Functions ============ */
    function _getNonCaller(address _signerOne, address _signerTwo) internal view returns(address) {
        return msg.sender == _signerOne ? _signerTwo : _signerOne;
    }
}
```

`LineOfCredit.setRates()` function:

```solidity
    function setRates(
        bytes32 id,
        uint128 drate,
        uint128 frate
    )
      external
      override
      mutualConsentById(id)
      returns (bool)
    {
        Credit memory credit = credits[id];
        credits[id] = _accrue(credit, id);
        require(interestRate.setRate(id, drate, frate));
        emit SetRates(id, drate, frate);
        return true;
    }
```
### Impact

Contracts that inherit from the `MutualConsent` contract, have access to a `mutualConsent` modifier.

Functions that use this modifier need consent from two parties to be called successfully.

Once one party has given consent for a function call, it cannot revoke consent.

This means that the other party can call this function at any time now.

This opens the door for several exploitation paths.

Most notably though the functions `LineOfCredit.setRates()`, `LineOfCredit.addCredit()` and `LineOfCredit.increaseCredit()` can cause problems.

One party can use Social Engineering to make the other party consent to multiple function calls and exploit the multiple consents.
### Proof of Concept

1. A borrower and lender want to change the rates for a credit. The borrower wants to create the possibility for himself to change the rates in the future without the lender's consent.
2. The borrower and lender agree to set `dRate` and `fRate` to 5%.
3. The lender calls the `LineOfCredit.setRates()` function to give his consent.
4. The borrower might now say to the lender "Let's put the rate to 5.1% instead, I will give an extra 0.1%"
5. The borrower and lender now both call the `LineOfCredit.setRates()` function to set the rates to 5.1%.
6. The borrower can now set the rates to 5% at any time. E.g. they might increase the rates further in the future (the borrower playing by the rules) and at some point the borrower can decide to set the rates to 5%.
### Recommended Mitigation

There are several options to fix this issue:

1. Add a function to the `MutualConsent` contract to revoke consent for a function call.
2. Make consent valid only for a certain amount of time.
3. Invalidate existing consents for a function when function is called with different arguments.

Option 3 requires a lot of additional bookkeeping but is probably the cleanest solution.

### Discussion

### Notes & Impressions

#### Notes 
Here's how the mechanism works:

1. When a party calls a function protected by the `mutualConsent` modifier, their consent is recorded in the `mutualConsents` mapping
2. The consent is stored as a hash of the function call data and the address of the other party
3. When the second party calls the same function with the same parameters, the operation executes
4. After execution, the consent record is deleted

#### Attack Scenario

The finding describes a scenario where this vulnerability could be exploited:

1. A borrower and lender agree to change interest rates to 5%
2. The lender gives consent by calling `setRates()` with the 5% parameters
3. The borrower suggests a better rate (5.1%) before executing the first change
4. Both parties consent to and execute the new 5.1% rate change
5. The borrower can now, at any time, revert to the 5% rate using the lender's original consent that was never invalidated

#### Impressions

similar like [[2022-11-debtdao#[H-03] `addCredit` / `increaseCredit` cannot be called by lender first when token is ETH|[H-03] `addCredit` / `increaseCredit` cannot be called by lender first when token is ETH]]

### Tools
- [[Mutual_Consent]]
### Refine

- [[1-Business_Logic]]

---

---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}