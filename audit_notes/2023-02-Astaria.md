# 2023-02-Astaria
---
- Category: #Dexes #CDP #services #cross-chain #rwa 
- Note Create 2025-01-08
- Platform: Spearbit
- Report Url: [2023-02-Astaria](https://github.com/spearbit/portfolio/blob/master/pdfs/Astaria-Spearbit-Security-Review.pdf)
---
# High Risk Findings (xx)

---
## [H-01] Collateral owner can steal funds by taking liens while asset is listed for sale on Seaport
----
- **Tags**:  #validation #business_logic 
- Number of finders: 4
- Difficulty: Medium
---
### Description: 

We only allow collateral holders to call `listForSaleOnSeaport` if they are listing the collateral at a price that is sufficient to pay back all of the liens on their collateral. 

When a new lien is created, we check that `collateralStateHash != bytes32("ACTIVE_AUCTION")` to ensure that the collateral is able to accept a new lien. 

However, calling `listForSaleOnSeaport` does not set the `collateralStateHash`, so it doesn't stop us from taking new liens. 

As a result, a user can deposit collateral and then, in one transaction: 
- List the asset for sale on Seaport for `1 wei`. 
- Take the maximum possible loans against the asset. 
- Buy the asset on Seaport for `1 wei`. 
The `1 wei` will not be sufficient to pay back the lenders, and the user will be left with the collateral as well as the loans (minus `1 wei`). 
[LienToken.sol#L368-L372](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/LienToken.sol#L368-L372)
```solidity
  function _createLien(
    LienStorage storage s,
    ILienToken.LienActionEncumber memory params
  ) internal returns (uint256 newLienId, ILienToken.Stack memory newSlot) {
	if (
      s.collateralStateHash[params.collateralId] == bytes32("ACTIVE_AUCTION")
    ) {
      revert InvalidState(InvalidStates.COLLATERAL_AUCTION);
    }
    ... ...
```

### Recommendation: 
Either set the `collateralStateHash` when an item is listed for sale on Seaport, or check the `s.collateralIdToAuction` variable before allowing a lien to be taken. 
### Discussion
Astaria: `listForSaleOnSeaport` has been removed in the following PR and that resolves the issue PR 206.
Spearbit: Verified.

### Notes

#### Notes 
See: [[2023-02-Astaria#[H-05] A borrower can list their collateral on Seaport and receive almost all the listing price without paying back their liens|[H-05] A borrower can list their collateral on Seaport and receive almost all the listing price without paying back their liens]]
The Attack Sequence:

1. A user deposits a valuable NFT worth 100 ETH
2. In a single transaction, they:
    - List the NFT for sale on Seaport for just 1 wei (less than $0.01)
    - Take out loans against the NFT for 80 ETH
    - Buy back their own NFT for 1 wei

The Result:

- The attacker now has both the NFT and 80 ETH in loans
- The lenders are left with no way to recover their funds because the collateral was sold for just 1 wei

### Tools
### Refine

{{ Refine to typical issues}}

---
## [H-03] `VaultImplementation.buyoutLien` does not update the new public vault's parameters and does not transfer assets between the vault and the borrower
----
- **Tags**: #Do_not_update_state #business_logic 
- Number of finders: 4
- Difficulty: Medium
---
### Description: 

`VaultImplementation.buyoutLien` does not update the accounting for the vault (if it's public). The `slope`, `yIntercept`, and `s.epochData[...].liensOpenForEpoch` (for the new lien's end epoch) are not updated. They are updated for the payee of the swapped-out lien if the `payee` is a public vault by calling `handleBuyoutLien`. 

[VaultImplementation.sol#L305C1-L355C4](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/VaultImplementation.sol#L305C1-L355C4)
```solidity
  function buyoutLien(
    uint256 collateralId,
    uint8 position,
    IAstariaRouter.Commitment calldata incomingTerms,
    ILienToken.Stack[] calldata stack
  )
    external
    whenNotPaused
    returns (ILienToken.Stack[] memory, ILienToken.Stack memory)
  {
    (uint256 owed, uint256 buyout) = IAstariaRouter(ROUTER())
      .LIEN_TOKEN()
      .getBuyout(stack[position]);


    if (buyout > ERC20(asset()).balanceOf(address(this))) {
      revert IVaultImplementation.InvalidRequest(
        InvalidRequestReason.INSUFFICIENT_FUNDS
      );
    }


    _validateCommitment(incomingTerms, recipient());


    ERC20(asset()).safeApprove(address(ROUTER().TRANSFER_PROXY()), buyout);


    LienToken lienToken = LienToken(address(ROUTER().LIEN_TOKEN()));


    if (
      recipient() != address(this) &&
      !lienToken.isApprovedForAll(address(this), recipient())
    ) {
      lienToken.setApprovalForAll(recipient(), true);
    }


    return
      lienToken.buyoutLien(
        ILienToken.LienActionBuyout({
          incoming: incomingTerms,
          position: position,
          encumber: ILienToken.LienActionEncumber({
            collateralId: collateralId,
            amount: incomingTerms.lienRequest.amount,
            receiver: recipient(),
            lien: ROUTER().validateCommitment({
              commitment: incomingTerms,
              timeToSecondEpochEnd: _timeToSecondEndIfPublic()
            }),
            stack: stack
          })
        })
      );
  }
```

[LienToken.sol#L102-L114](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/LienToken.sol#L102-L114)
```solidity
  function buyoutLien(ILienToken.LienActionBuyout calldata params)
    external
    validateStack(params.encumber.collateralId, params.encumber.stack)
    returns (Stack[] memory, Stack memory newStack)
  {
    if (msg.sender != params.encumber.receiver) {
      require(
        _loadERC721Slot().isApprovedForAll[msg.sender][params.encumber.receiver]
      );
    }


    return _buyoutLien(_loadLienStorageSlot(), params);
  }
```

[LienToken.sol#L116-L187](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/LienToken.sol#L116-L187)
```solidity
  function _buyoutLien(
    LienStorage storage s,
    ILienToken.LienActionBuyout calldata params
  ) internal returns (Stack[] memory, Stack memory newStack) {
... ...
    if (_isPublicVault(s, payee)) {
      IPublicVault(payee).handleBuyoutLien(
        IPublicVault.BuyoutLienParams({
          lienSlope: calculateSlope(params.encumber.stack[params.position]),
          lienEnd: params.encumber.stack[params.position].point.end,
          increaseYIntercept: buyout -
            params.encumber.stack[params.position].point.amount
        })
      );
    }
```

Also, the buyout amount is paid out by the vault itself. The difference between the new lien amount and the buyout amount is not worked out between the `msg.sender` and the new vault. 

### Recommendation: 

1. If the vault that `VaultImplementation.buyoutLien` endpoint was called into is a public vault, make sure to update its `slope, yIntercept, and s.epochData[...].liensOpenForEpoch` (for the new lien's end epoch) when the new lien is created. 
2. The difference between the new lien amount and the buyout amount is not worked out between the `msg.sender` that called `VaultImplementation.buyoutLien` and the vault. If the buyout amount is higher than the new lien amount, we need to make sure the `msg.sender` also transfers some assets (`wETH`) to the vault. And the other way around, if the new lien amount is higher than the buyout amount, the vault needs to transfer some assets (`wETH`) to the `borrower / msg.sender`.
### Discussion

### Notes

#### Impressions

Check the updates of states  
	- Correctness of the update.
	- Whether all updates have been made.
### Tools
### Refine

- [[1-Business_Logic]]

---
## [H-05] A borrower can list their collateral on Seaport and receive almost all the listing price without paying back their liens
----
- **Tags**:  #business_logic 
- Number of finders: 4
- Difficulty: Medium
---
### Description: 

When the collateral is listed on `SeaPort` by the borrower using `listForSaleOnSeaport`, `s.auctionData` is not populated and thus, if that order gets `fulfilled/matched` and ClearingHouse's `fallback` function gets called since `stack.length` is 0, this loop will not run and no payment is sent to the lending vaults. 

[CollateralToken.sol/listForSaleOnSeaport](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/CollateralToken.sol#L406-L443)
```solidity
  function listForSaleOnSeaport(ListUnderlyingForSaleParams calldata params)
    external
    onlyOwner(params.stack[0].lien.collateralId)
  {
    //check that the incoming listed price is above the max total debt the asset can occur by the time the listing expires
    CollateralStorage storage s = _loadCollateralSlot();


    //check the collateral isn't at auction


    if (s.collateralIdToAuction[params.stack[0].lien.collateralId]) {
      revert InvalidCollateralState(InvalidCollateralStates.AUCTION_ACTIVE);
    }
    //fetch the current total debt of the asset
    uint256 maxPossibleDebtAtMaxDuration = s
      .LIEN_TOKEN
      .getMaxPotentialDebtForCollateral(
        params.stack,
        block.timestamp + params.maxDuration
      );


    if (maxPossibleDebtAtMaxDuration > params.listPrice) {
      revert ListPriceTooLow();
    }


    OrderParameters memory orderParameters = _generateValidOrderParameters(
      s,
      params.stack[0].lien.collateralId,
      params.listPrice,
      params.listPrice,
      params.maxDuration
    );


    _listUnderlyingOnSeaport(
      s,
      params.stack[0].lien.collateralId,
      Order(orderParameters, new bytes(0))
    );
  }
```

[ClearingHouse.sol/fallback()](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/ClearingHouse.sol#L30-L33)
```solidity
  fallback() external payable {
    IAstariaRouter ASTARIA_ROUTER = IAstariaRouter(_getArgAddress(0));
    require(msg.sender == address(ASTARIA_ROUTER.COLLATERAL_TOKEN().SEAPORT()));
    WETH(payable(address(ASTARIA_ROUTER.WETH()))).deposit{value: msg.value}();
    uint256 payment = ASTARIA_ROUTER.WETH().balanceOf(address(this));
    ASTARIA_ROUTER.WETH().safeApprove(
      address(ASTARIA_ROUTER.TRANSFER_PROXY()),
      payment
    );
    ASTARIA_ROUTER.LIEN_TOKEN().payDebtViaClearingHouse(
      _getArgUint256(21),
      payment
    );
  }
}
```

The rest of the payment is sent to the borrower. And the collateral token and its related data gets `burnt/deleted` by calling `settleAuction`. The lien tokens and the vaults remain untouched as though nothing has happened.

[settleAuction](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/LienToken.sol#L442-L460C1)
```solidity
  function payDebtViaClearingHouse(uint256 collateralId, uint256 payment)
    external
  {
    LienStorage storage s = _loadLienStorageSlot();
    require(msg.sender == s.COLLATERAL_TOKEN.getClearingHouse(collateralId));


    uint256 spent = _payDebt(s, collateralId, payment, msg.sender);
    delete s.collateralStateHash[collateralId];


    if (spent < payment) {
      s.TRANSFER_PROXY.tokenTransferFrom(
        s.WETH,
        msg.sender,
        s.COLLATERAL_TOKEN.ownerOf(collateralId),
        payment - spent
      );
    }
    s.COLLATERAL_TOKEN.settleAuction(collateralId);
  }
```

So basically a borrower can: 
1. `Take/borrow` liens by offering a collateral. 
2. List their collateral on SeaPort through the `listForSaleOnSeaport` endpoint. 
3. Once/if the SeaPort order `fulfills/matches`, the borrower would be paid the listing price minus the amount sent to the liquidator (`address(0)` in this case, which should be corrected). 
4. Collateral `token/data` gets `burnt/deleted`. 
5. Lien token data remains and the loans are not paid back to the vaults. 

And so the borrower could end up with all the loans they have taken plus the listing price from the SeaPort order. 

Note that when a user lists their own collateral on Seaport, it seems that we intentionally do not kick off the auction process: 
- Liens are continued. 
- Collateral state hash is unchanged. 
- liquidator isn't set. 
- Vaults aren't updated. 
- Withdraw proxies aren't set, etc. 

Related issue 88. 
### Recommendation: 

Be careful and also pay attention that listing by a borrower versus auctioning by a liquidator take separate `return/payback` paths. It is recommended to separate the listing and liquidating logic and make sure auction funds and distributed appropriately. Most importantly, the auction stack must be set. 
### Discussion
Astaria: We've removed the ability for self-listing on seaport as the fix for v0, will add this feature this in a future release. 
Spearbit: Fixed in the following PR by removing the `listForSaleOnSeaport` endpoint PR 206.
### Notes

#### Impressions

- Immaturity: The self-listing feature was not fully integrated with the protocol's core lending and liquidation mechanics. This is evident from how it bypasses critical auction data population and debt repayment logic that exists in the regular liquidation path.
- Subtlety: The vulnerability is complex because it involves:
    - Interaction between multiple contracts (CollateralToken, ClearingHouse, Seaport)
    - Lack of state updates (auctionData not being populated)
    - A non-obvious control flow where the fallback function fails silently
    - Different execution paths for self-listing vs liquidator auctions
### Tools
### Refine
- [[1-Business_Logic]]

---
## [H-11] `processEpoch()` needs to be called regularly
----
- **Tags**:  #business_logic 
- Number of finders: 4
- Difficulty: Medium
---
### Description: 

If the `processEpoch()` endpoint does not get called regularly (especially close to the epoch boundaries), the updated `currentEpoch` would lag behind the actual expected value and this will introduce arithmetic errors in formulas regarding epochs and timestamps. 

```solidity
  function processEpoch() public {
    // check to make sure epoch is over
    if (timeToEpochEnd() > 0) {
      revert InvalidState(InvalidStates.EPOCH_NOT_OVER);
    }
    VaultData storage s = _loadStorageSlot();

	... ...
    // increment epoch
    unchecked {
      s.currentEpoch++;
    }
  }
```
### Recommendation: 

Thus public vaults need to create a mechanism so that the `processEpoch()` gets called regularly maybe using relayers or off-chain bots. 

Also if there are any outstanding withdraw reserves, the vault needs to be topped up with assets (and/or the current withdraw proxy) so that the full amount of withdraw reserves can be transferred to the withdraw proxy from the epoch before using `transferWithdrawReserve`, otherwise, the processing of epoch would be halted. And if this halt continues more than one epoch length, the inaccuracy in the epoch number will be introduced in the system. 

Another mechanism that can be introduced into the system is of incrementing the current epoch not just by one but by an amount depending on the amount of time passed since the last call to the `processEpoch()` or the timestamp of the current epoch. 

### Discussion
Astaria: Acknowledged. 
Spearbit: Acknowledged.
### Notes

#### Notes 
The function can only increment the epoch counter by 1 each time it's called (`s.currentEpoch++`), and it can only be called after the current epoch has completely ended (`timeToEpochEnd() > 0`). This creates several potential problems:

Think of it like a clock that needs someone to manually push the minute hand forward. If nobody pushes it for an hour, the clock will still only move forward one minute when someone finally does push it, even though an hour has passed in real time.
#### Impressions
- Check whether time-based epochs increase as expected
	- Epoch/period increments
	- Required sequential processing
	- Blocking conditions
### Tools
### Refine

- [[1-Business_Logic]]

---

# Medium Risk Findings (xx)

---

## [M-08] Expired liens taken from public vaults need to be liquidated otherwise processing an epoch `halts/reverts`
----
- **Tags**:  #business_logic 
- Number of finders: 4
- Difficulty: Medium
---
### Description: 
`s.epochData[s.currentEpoch].liensOpenForEpoch` is decremented or is supposed to be decremented, when for a lien with an end that falls on this epoch: 
- The full payment has been made, 
- Or the lien is bought out by a lien that is from a different vault or ends at a higher epoch, 
- Or the lien is liquidated. 
If for some reason a lien expires and no one calls liquidate, then `s.epochData[s.currentEpoch].liensOpenForEpoch > 0` will be true and `processEpoch()` would revert till someones calls `liquidate`. 

```solidity
function processEpoch() public {
......
    if (s.epochData[s.currentEpoch].liensOpenForEpoch > 0) {
      revert InvalidState(InvalidStates.LIENS_OPEN_FOR_EPOCH_NOT_ZERO);
    }
......
```

Note that a lien's end falling in the `s.currentEpoch and timeToEpochEnd() == 0` imply that the lien is expired.
### Recommended Mitigation

Astaria would need to have a monitoring solution setup to make sure the `liquidate` endpoint gets called for expired liens without delay.
### Discussion

### Notes

#### Notes 

Here's where the problem comes in: If a lien expires but nobody calls the `liquidate` function, the counter stays positive
#### Impressions

The need to update critical state variables in a timely manner

same as [[2023-02-Astaria#[H-11] `processEpoch()` needs to be called regularly|[H-11] `processEpoch()` needs to be called regularly]]
### Tools
### Refine

- [[1-Business_Logic]]

---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}