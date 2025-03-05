# 2023-02-Astaria
---
- Category: #Dexes #CDP #services #cross-chain #rwa 
- Note Create 2025-01-08
- Platform: Spearbit
- Report Url: [2023-02-Astaria](https://github.com/spearbit/portfolio/blob/master/pdfs/Astaria-Spearbit-Security-Review.pdf)
---
# High Risk Findings (xx)

---
## [H-02] Inequalities involving `liquidationInitialAsk` and `potentialDebt` can be broken when `buyoutLien` is called
----
- **Tags**:  #business_logic 
- Number of finders: 4
- Difficulty: Medium
---
### Context

[LienToken.sol/buyoutLien](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/LienToken.sol#L102C1-L114C4)
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

[VaultImplementation.sol/buyoutLien](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/VaultImplementation.sol#L305-L355)
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

[LienToken.sol/`_createLien`](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/LienToken.sol#L377-L378)
```solidity
function _createLien(
    LienStorage storage s,
    ILienToken.LienActionEncumber memory params
  ) internal returns (uint256 newLienId, ILienToken.Stack memory newSlot) {
... ...
    if (
      params.lien.details.liquidationInitialAsk < params.amount ||
      params.lien.details.liquidationInitialAsk == 0
    ) {
      revert InvalidState(InvalidStates.INVALID_LIQUIDATION_INITIAL_ASK);
    }
... ...
}
```

[`LienToken.sol/_appendStack`](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/LienToken.sol#L427)
```solidity
  function _appendStack(
    LienStorage storage s,
    Stack[] memory stack,
    Stack memory newSlot
  ) internal returns (Stack[] memory newStack) {
    ... ...
      if (potentialDebt > newStack[j].lien.details.liquidationInitialAsk) {
        revert InvalidState(InvalidStates.INITIAL_ASK_EXCEEDED);
      }
	... ...
```

[AstariaRouter.sol#L542](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/AstariaRouter.sol#L542)
```solidity
  function liquidate(ILienToken.Stack[] memory stack, uint8 position)
    public
    returns (OrderParameters memory listedOrder)
  {
    ... ...
    listedOrder = s.COLLATERAL_TOKEN.auctionVault(
      ICollateralToken.AuctionVaultParams({
        settlementToken: address(s.WETH),
        collateralId: stack[position].lien.collateralId,
        maxDuration: uint256(s.auctionWindow + s.auctionWindowBuffer),
        startingPrice: stack[0].lien.details.liquidationInitialAsk,
        endingPrice: 1_000 wei
      })
    );
  }
```
### Description

When we commit to a new lien, the following gets checked to be true for all $j\in 0, \cdots, n-1$:
$$
o_{\text {new }}+o_{n-1}+\cdots+o_j \leq L_j
$$

where:

| parameter      | description                                          |
| -------------- | ---------------------------------------------------- |
| $o_i$          | `_getOwed(newStack[i], newStack[i].point.end)`       |
| $o_{new}$      | `_getOwed(newSlot, newSlot.point.end`                |
| $n$            | `stack.length`                                       |
| $L_i$          | `newStack[i].lien.details.liquidationInitialAsk`     |
| $L_k^{\prime}$ | `params.encumber.lien.details.liquidationInitialAsk` |
| $k$            | `params.position`                                    |
| $A_k^{\prime}$ | `params.encumber.amount`                             |
so in a `stack` in general we should have the:
$$
\cdots+o_{j+1}+o_j \leq L_j
$$
But when an old lien is replaced with a new one, we only perform the following checks for $L_k^{\prime}$:
$$
L_k^{\prime} \geq A_k^{\prime} \wedge L_k^{\prime}>0
$$
And thus we can introduce:
- $L_k^{\prime} \ll L_k$ or
- $o_k^{\prime} \gg o_k$ (by pushing the lien duration)
Which would break the inequality regarding $o_i$ s and $L_i$.
If the inequality is broken, for example, if we buy out the first lien in the stack, then if the lien expires and goes into a Seaport auction the auction's starting price $L_0$ would not be able to cover all the potential debts even at the beginning of the auction.



### Recommended Mitigation

When `buyoutLien` is called, we would need to loop over $j$ and check the inequalities again:
$$
\cdots+o_{j+1}+o_j \leq L_j
$$

### Discussion

### Notes

#### Notes 
The system has a crucial safety requirement: For any position in the stack, the liquidation ask price must be greater than or equal to the sum of all the potential debts above it. This ensures that if liquidation happens, there's enough value to cover all the loans.

The Problem: The report identifies that when someone uses the `buyoutLien` function to replace an existing loan with a new one, the system doesn't properly check if this safety requirement is maintained. It only verifies two simple conditions:

1. The new liquidation ask price is greater than zero
2. The new liquidation ask price is greater than the immediate loan amount
### Tools
### Refine

- [[1-Business_Logic]]

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
See: [[2023-02-astaria#[H-05] A borrower can list their collateral on Seaport and receive almost all the listing price without paying back their liens|[H-05] A borrower can list their collateral on Seaport and receive almost all the listing price without paying back their liens]]
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
## [H-06] Incorrect auction end validation in `liquidatorNFTClaim()`
----
- **Tags**:  #validation #business_logic 
- Number of finders: 4
- Difficulty: Medium
### Description

`liquidatorNFTClaim()` does the following check to recognize that Seaport auction has ended:

[CollateralToken.sol#L119](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/CollateralToken.sol#L119)
```solidity
  function liquidatorNFTClaim(OrderParameters memory params) external {
  ... ...
	if (block.timestamp < params.endTime) {
	  //auction hasn't ended yet 
	  revert InvalidCollateralState(InvalidCollateralStates.AUCTION_ACTIVE); 
	}
  ... ...
  }
```

Here, `params` is completely controlled by users and hence to bypass this check, the caller can set `params.endTime` to be less than `block.timestamp`. 

Thus, a possible exploit scenario occurs when `AstariaRouter.liquidate()` is called to list the underlying asset on Seaport which also sets `liquidator` address. Then, anyone can call `liquidatorNFTClaim()` to transfer the underlying asset to liquidator by setting `params.endTime < block.timestamp`. 
### Recommendation: 

The parameter passed to `liquidatorNFTClaim()` should be validated against the parameters created for the Seaport auction. To do that: 
- `collateralIdToAuction` mapping which currently maps `collateralId` to a boolean value indicating an active auction, should instead map from `collateralId` to Seaport order hash. 
- All usages of `collateralIdToAuction` should be updated. For example, `isValidOrder()` and `isValidOrderIncludingExtraData()` should be updated:
```javascript
return 
- s.collateralIdToAuction[uint256(zoneHash)] 
+ s.collateralIdToAuction[uint256(zoneHash)] == orderHash 
    ? ZoneInterface.isValidOrder.selector 
    : bytes4(0xffffffff);
```
- `liquidatorNFTClaim()` should verify that hash of `params` matches the value stored in `collateralIdToAuction` mapping. This validates that `params.endTime` is not spoofed.
### Notes

#### Notes 
First, let's understand the normal auction flow:

1. When a liquidation happens, the `AstariaRouter.liquidate()` function is called
2. This lists the NFT asset on Seaport (a popular NFT marketplace protocol)
3. After the auction ends, someone should be able to call `liquidatorNFTClaim()` to finalize the transfer

The vulnerability exists in how the contract checks if the auction has ended. The current code simply compares the current time (`block.timestamp`) with a user-provided end time (`params.endTime`):

The fundamental problem is that `params` is entirely controlled by the user calling the function. This means anyone could pass in an artificially early `endTime` that's already passed, making the contract think the auction has ended when it hasn't.

#### Impression

*In smart contracts, time is not reliable; it can be altered.*
### Tools
### Refine

- [[1-Business_Logic]]

---
## [H-10] Refactor `_paymentAH()`
----
- **Tags**: #validation #business_logic #array_index 
- Number of finders: 4
- Difficulty: Medium
---
### Description

`_paymentAH`
```solidity
  function _paymentAH(
    LienStorage storage s,
    uint256 collateralId,
    AuctionStack[] memory stack,
    uint256 position,
    uint256 payment,
    address payer
  ) internal returns (uint256) {
    uint256 lienId = stack[position].lienId;
    uint256 end = stack[position].end;
    uint256 owing = stack[position].amountOwed;
    //checks the lien exists
    address owner = ownerOf(lienId);
    address payee = _getPayee(s, lienId);


    if (owing > payment.safeCastTo88()) {
      stack[position].amountOwed -= payment.safeCastTo88();
    } else {
      payment = owing;
    }
    s.TRANSFER_PROXY.tokenTransferFrom(s.WETH, payer, payee, payment);


    delete s.lienMeta[lienId]; //full delete
    delete stack[position];
    _burn(lienId);


    if (_isPublicVault(s, payee)) {
      if (owner == payee) {
        IPublicVault(payee).updateAfterLiquidationPayment(
          IPublicVault.LiquidationPaymentParams({lienEnd: end})
        );
      } else {
        IPublicVault(payee).decreaseEpochLienCount(stack[position].end);
      }
    }
    emit Payment(lienId, payment);
    return payment;
  }
```

`_paymentAH()` has several vulnerabilities: 
- `stack` is a memory parameter. So all the updates made to stack are not applied back to the corresponding storage variable. 
- No need to update `stack[position]` as it's deleted later. 
- `decreaseEpochLienCount()` is always passed `0`, as `stack[position]` is already deleted. Also `decreaseEpochLienCount()` expects epoch, but end is passed instead. 
- This `if/else` block can be merged.` updateAfterLiquidationPayment()` expects `msg.sender` to be `LIEN_- TOKEN`, so this should work.

### Recommended Mitigation

```solidity
  function _paymentAH(
    LienStorage storage s,
    uint256 collateralId,
    AuctionStack[] storage stack,
    uint256 position,
    uint256 payment,
    address payer
  ) internal returns (uint256) {
    uint256 lienId = stack[position].lienId;
    uint256 end = stack[position].end;
    uint256 owing = stack[position].amountOwed;
    //checks the lien exists
    address owner = ownerOf(lienId);
    address payee = _getPayee(s, lienId);


    if (owing < payment.safeCastTo88()) {
      payment = owing;
    }
    s.TRANSFER_PROXY.tokenTransferFrom(s.WETH, payer, payee, payment);


    delete s.lienMeta[lienId]; //full delete
    delete stack[position];
    _burn(lienId);


    if (_isPublicVault(s, payee)) {
        IPublicVault(payee).updateAfterLiquidationPayment(
          IPublicVault.LiquidationPaymentParams({lienEnd: end})
        );
    }
    emit Payment(lienId, payment);
    return payment;
  }
```

### Discussion

### Notes

#### Notes 
The issues center around memory vs storage conflicts and inefficient logic flow in the `_paymentAH` function. Here's the key problems:

1. Memory vs Storage Array Issue:
```solidity
AuctionStack[] memory stack   // Changes don't persist to storage
```
Changes to memory arrays don't affect storage state. Like modifying a copy instead of the original.

2. Redundant Stack Updates:
```solidity
stack[position].amountOwed -= payment.safeCastTo88();  // Unnecessary
delete stack[position];  // Gets deleted anyway
```

3. Invalid Parameter in `decreaseEpochLienCount`:
```solidity
decreaseEpochLienCount(stack[position].end)  // Passes end time instead of epoch
stack[position] is already deleted  // Passes 0
```

4. Unnecessary Logic Split:
```solidity
if (owner == payee) {
  IPublicVault(payee).updateAfterLiquidationPayment(...);
} else {
  IPublicVault(payee).decreaseEpochLienCount(...);
}
```
Can be consolidated since `updateAfterLiquidationPayment` checks `msg.sender`.

To identify similar issues:
1. Check array parameter types (memory vs storage)
2. Look for redundant state updates before deletions 
3. Trace parameter values after state changes
4. Review function call requirements and permissions
5. Look for overly complex conditional logic

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
## [H-20] `commitToLiens` transfers extra assets to the borrower when protocol fee is present 
----
- **Tags**: #wrong_math #business_logic 
- Number of finders: 4
- Difficulty: Medium
---
### Description

`totalBorrowed` is the `sum` of all `commitments[i].lienRequest.amount` But if `s.feeTo` is set, some of `funds/assets` from the vaults get transferred to `s.feeTo` when `_handleProtocolFee` is called and only the remaining is sent to the `ROUTER()`. So in this scenario, the total amount of assets sent to `ROUTER()` (so that it can be transferred to `msg.sender`) is up to rounding errors:

$$
\left(1-\frac{n_p}{d_p}\right) T
$$
Where:
- $T$ is the `totalBorrowed`
- $n_p$ is `s.protocolFeeNumerato`
- $d_p$ is `s.protocolFeeDenominator`
But we are transferring $T$ to `msg.sender` which is more than we are supposed to send,

[AstariaRouter.sol#L391-L423]https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/AstariaRouter.sol#L391-L423()
```solidity
  function commitToLiens(IAstariaRouter.Commitment[] memory commitments)
    public
    whenNotPaused
    returns (uint256[] memory lienIds, ILienToken.Stack[] memory stack)
  {
    RouterStorage storage s = _loadRouterSlot();


    uint256 totalBorrowed;
    lienIds = new uint256[](commitments.length);
    _transferAndDepositAssetIfAble(
      s,
      commitments[0].tokenContract,
      commitments[0].tokenId
    );
    for (uint256 i; i < commitments.length; ) {
      if (i != 0) {
        commitments[i].lienRequest.stack = stack;
      }
      (lienIds[i], stack) = _executeCommitment(s, commitments[i]);
      totalBorrowed += commitments[i].lienRequest.amount;
      unchecked {
        ++i;
      }
    }
    s.WETH.safeApprove(address(s.TRANSFER_PROXY), totalBorrowed);


    s.TRANSFER_PROXY.tokenTransferFrom(
      address(s.WETH),
      address(this),
      address(msg.sender),
      totalBorrowed
    );
  }
```

[VaultImplementation.sol#L378-L393](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/VaultImplementation.sol#L378-L393)
```solidity
  function _requestLienAndIssuePayout(
    IAstariaRouter.Commitment calldata c,
    address receiver
  )
    internal
    returns (
      uint256 newLienId,
      ILienToken.Stack[] memory stack,
      uint256 slope
    )
  {
    _validateCommitment(c, receiver);
    (newLienId, stack, slope) = ROUTER().requestLienPosition(c, recipient());
    uint256 payout = _handleProtocolFee(c.lienRequest.amount);
    ERC20(asset()).safeTransfer(receiver, payout);
  }
```
### Recommended Mitigation

Make sure only $\left(1-\frac{n_p}{d_p}\right)T$  is transferred to the borrower
### Discussion
Astaria: Acknowledged. 
Spearbit: Acknowledge
### Notes

#### Notes 

The Process: When someone takes out a loan in this protocol, two main things happen:

1. The protocol collects a fee (similar to a service charge)
2. The borrower receives their loan amount

The Mathematical Error: Let's say someone wants to borrow 100 ETH and the protocol fee is 2%. Here's what should happen:

- Protocol fee: 2 ETH
- Amount to borrower: 98 ETH
- Total: 100 ETH

But there's a bug in the code. The `commitToLiens` function calculates the total borrowed amount (`totalBorrowed`) by adding up all loan amounts, but it doesn't account for the protocol fees that were already deducted. So in our example:

- Protocol already took 2 ETH
- But the code tries to send the full 100 ETH to the borrower
- Result: The borrower gets more than they should
#### Impressions

*we should repeatedly verify whether the financial calculations(such as interest and fees) are correctly implemented in the code during future audit tasks.*

### Tools
### Refine

- [[1-Business_Logic]]

---
## [H-21] `WithdrawProxy` allows redemptions before `PublicVault` calls `transferWithdrawReserve`
----
- **Tags**:  #business_logic #validation #ERC4626_EIP4626 #withdraw #withdraw_proxy
- Number of finders: 4
- Difficulty: Medium
---
### Description 

Anytime there is a `withdraw` pending (i.e. someone holds `WithdrawProxy` shares), shares may be redeemed so long as `totalAssets() > 0` and `s.finalAuctionEnd == 0`. 

Under normal operating conditions `totalAssets()` becomes greater than 0 when then `PublicVault` calls `transferWithdrawReserve`. 

`totalAssets()` can also be increased to a non zero value by anyone transferring `WETH` to the contract. If this occurs and a user attempts to redeem, they will receive a smaller share than they are owed. 

Exploit scenario: 
- Depositor redeems from `PublicVault` and receives `WithdrawProxy` shares. 
- Malicious actor deposits a small amount of `WETH` into the `WithdrawProxy`. 
- Depositor accidentally redeems, or is tricked into `redeeming`, from the `WithdrawProxy` while `totalAssets()` is smaller than it should be. 
- `PublicVault` properly processes epoch and full `withdrawReserve` is sent to `WithdrawProxy`. 
- All remaining holders of `WithdrawProxy` shares receive an outsized share as the previous shares we `redeemed` for the incorrect value. 
[WithdrawProxy.sol#L164C1-L178C4](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/WithdrawProxy.sol#L164C1-L178C4)
```solidity
  function redeem(
    uint256 shares,
    address receiver,
    address owner
  ) public virtual override(ERC4626Cloned, IERC4626) returns (uint256 assets) {
    WPStorage storage s = _loadSlot();
    // If auction funds have been collected to the WithdrawProxy
    // but the PublicVault hasn't claimed its share, too much money will be sent to LPs
    if (s.finalAuctionEnd != 0) {
      // if finalAuctionEnd is 0, no auctions were added
      revert InvalidState(InvalidStates.NOT_CLAIMED);
    }


    return super.redeem(shares, receiver, owner);
  }
```
### Recommendation: 
- Option 1: 
Consider being explicit in opening the `WithdrawProxy` for redemptions (`redeem/withdraw`) by requiring `s.withdrawReserveReceived` to be a non zero value:
```javascript
- if (s.finalAuctionEnd != 0) { 
+ if (s.finalAuctionEnd != 0 || s.withdrawReserveReceived == 0) { 
  // if finalAuctionEnd is 0, no auctions were added 
  revert InvalidState(InvalidStates.NOT_CLAIMED); 
}
```

Astaria notes there is a second scenario where funds are sent to the `WithdrawProxy`: auction payouts. For the above recommendation to be complete, auction payouts or claiming MUST also set `withdrawReserveReceived`. 
- Option 2: 
Instead of inferring when it is safe to withdraw based on `finalAuctionEnd` and `withdrawReserveReceived`, consider explicitly marking the withdraws as `open` when it is both safe to `withdraw` (i.e. expected funds deposited) and the vault has claimed its share.
### Discussion

### Notes

#### Notes 
Here's how it should work:

1. When Alice initiates her withdrawal for 100 ETH, she receives 100 withdraw shares
2. These shares represent a claim on the FUTURE withdrawal funds
3. The price relationship should be locked at 1 share = 1 ETH

What's happening instead:

1. Alice has 100 withdraw shares
2. Bob maliciously deposits 1 ETH
3. The vault recalculates the share price based on current assets:
    - Share price = Total Assets / Total Shares
    - Share price = 1 ETH / 100 shares
    - Therefore 1 share = 0.01 ETH
#### Impressions
The correct logic is that Alice holds 100 withdraw shares worth 100eth, but when the PublicVault only has 1 ETH, the value of 100 shares becomes 1 ETH. So, the root problem is that by default, 1 share equals 1 ETH, but when the PublicVault is insufficient, 1 share equals 0.01 ETH. Essentially, withdrawal shares should have a price, and that price should be fixed.

### Tools
### Refine

- [[1-Business_Logic]]

---
## [H-22] Withdraw proxy's `claim()` endpoint updates public vault's `yIntercept` incorrectly
----
- **Tags**: #business_logic 
- Number of finders: 4
- Difficulty: Medium
---
### Context
[WithdrawProxy.sol#L235-L261](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/WithdrawProxy.sol#L235-L261)
```solidity

function claim() public {

... ...
    uint256 balance = ERC20(asset()).balanceOf(address(this)) -
      s.withdrawReserveReceived;


    if (balance < s.expected) {
      PublicVault(VAULT()).decreaseYIntercept(
        (s.expected - balance).mulWadDown(
          10**ERC20(asset()).decimals() - s.withdrawRatio
        )
      );
    }


    if (s.withdrawRatio == uint256(0)) {
      ERC20(asset()).safeTransfer(VAULT(), balance);
    } else {
      transferAmount = uint256(s.withdrawRatio).mulDivDown(
        balance,
        10**ERC20(asset()).decimals()
      );


      unchecked {
        balance -= transferAmount;
      }


      if (balance > 0) {
        ERC20(asset()).safeTransfer(VAULT(), balance);
      }
    }
... ... 
}
```

[WithdrawProxy.sol#L239](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/WithdrawProxy.sol#L239)
```solidity
function claim() public {
... ...
    if (balance < s.expected) {
      PublicVault(VAULT()).decreaseYIntercept(
        (s.expected - balance).mulWadDown(
          10**ERC20(asset()).decimals() - s.withdrawRatio
        )
      );
    }
... ...
}
```
### Description

| parameter | description                                                                                      |
| --------- | ------------------------------------------------------------------------------------------------ |
| $y_0$     | the `yIntercept` of our public vault in the question.                                            |
| $n$       | `n` the current epoch for the public vault                                                       |
| $E_{n-1}$ | the `expected` storage parameter of the previous withdraw proxy                                  |
| $B_{n-1}$ | the asset balance of the previous withdraw proxy                                                 |
| $W_{n-1}$ | the `withdrawReserveReceived` of the previous withdraw proxy                                     |
| $S_{n-1}$ | the total supply of the previous withdraw proxy                                                  |
| $S_v$     | the total supply of the public vault when `processEpoch()` was last called on the public vault.  |
| $B_v$     | the total balance of the public vault when `processEpoch()` was last called on the public vault. |
| $V$       | the public vault                                                                                 |
| $P_{n-1}$ | the previous withdraw proxy                                                                      |
Then $y_0$ updated/decremented according to the formula (up to rounding errors due to division):

$$
y_0=y_0-\max \left(0, E_{n-1}-\left(B_{n-1}-W_{n-1}\right)\right)\left(1-\frac{S_{n-1}}{S_v}\right)
$$
Whereas the amount ( $A$ ) of assets transferred from $P_{n-1}$ to $V$ is
$$
A=\left(B_{n-1}-W_{n-1}\right)\left(1-\frac{S_{n-1}}{S_v}\right)
$$
And the amount ( $B$ ) of asset left in $P_{n1}$ after this transfer would be:
$$
B=\left(B_{n-1}-W_{n-1}\right)\left(1-\frac{S_{n-1}}{S_v}\right)
$$
$\left(B_{n-1}-W_{n-1}\right)$  is supposed to represent the payment withdrawal proxy receives from Seaport auctions plus the amount of assets transferred to it by external actors. So $A$ represents the portion of this amount for users who have not withdrawn from the public vault on the previous epoch and it is transferred to $V$ and so $y_0$ should be compensated positively. Also note that this amount might be bigger than $E_{n-1}$ if a lien has a really high `liquidationInitialAsk` and its auction fulfills/matches near that price on Seaport. So it is possible that $E_{n-1} < A$.

The current update formula for updating the $y_0$ has the following flaws: 
- It only considers updating $y_0$ when $E_{n-1} -\left(B_{n-1}-W_{n-1}\right)>0$ which is not always the case
- Decrements $y_0$ by a portion of $E_{n-1}$.
The correct updating formula for $y_0$ should be:
$$
y_0=y_0-E_{n-1}+\left(B_{n-1}-W_{n-1}\right)\left(1-\frac{S_{n-1}}{S_v}\right)
$$
Also note, if we let $B_{n-1}-W_{n-1} = X_{n-1} + \epsilon$, where $X_{n-1}$ is the payment received by the withdraw proxy from Seaport auction payments and $\epsilon$ (if $W_{n-1}$ updated correctly) be assets received from external actors by the previous withdraw proxy. Then:

$$
B=W_{n-1} + (X_{n-1} + \epsilon)\frac{S_{n-1}}{S_v}) = [max(0,B_v-E_{n-1})+X_{n-1}+\epsilon]\frac{S_{n-1}}{S_v})
$$
The last equality comes from the fact that when the withdraw reserves is full transferred from the public vault and the current withdraw proxy (if necessary) to the previous withdraw proxy the amount $W_{n-1}$ would hold should be $max(0,B_v-E_{n-1})\frac{S_{n-1}}{S_v})$
### Recommended Mitigation

Make sure $y_0$ is updated in `claim()` according to the following formula:

$$
y_0=y_0-E_{n-1}+\left(B_{n-1}-W_{n-1}\right)\left(1-\frac{S_{n-1}}{S_v}\right)
$$
### Discussion

### Notes

#### Notes 
The report uses some complex mathematical notation to explain the correct formula that should be used. Let me simplify what should happen:

1. When users withdraw, the system needs to track exactly how much was withdrawn
2. The vault's value tracking parameter (yIntercept) needs to be adjusted based on both:
    - The expected withdrawal amount
    - The actual balance received from various sources (including auction payments)
    - The ratio of withdrawing users to total users

The current code doesn't handle cases where the actual balance might be higher than expected (which can happen if assets are sold at a higher price than anticipated in auctions). It also uses an incorrect formula that could lead to accounting errors in the vault.
#### Impressions


The current code only handles the case when `balance < s.expected`, but it should handle both cases:

1. When `balance < s.expected`: The vault received less than expected
2. When `balance > s.expected`: The vault received more than expected (e.g., from high-value auction sales)

### Tools
### Refine
- [[1-Business_Logic]]

---

# Medium Risk Findings (xx)

---
## [M-04] UniV3 tokens with fees can bypass strategist checks
----
- **Tags**: #validation #business_logic 
- Number of finders: 4
- Difficulty: Hard
---
### Description

Each UniV3 strategy includes a value for fee in `nlrDetails` that is used to constrain their strategy to UniV3 pools with matching fees. 

This is enforced with the following check (where `details.fee` is the strategist's set `fee`, and `fee` is the fee returned from Uniswap):

```solidity
  function validateAndParse(
    IAstariaRouter.NewLienRequest calldata params,
    address borrower,
    address collateralTokenContract,
    uint256 collateralTokenId
  )
    external
    view
    override
    returns (bytes32 leaf, ILienToken.Details memory ld)
  {
  ... ... 
	if (details.fee != uint24(0) && fee != details.fee) { 
	  revert InvalidFee(); 
	}
  ... ... 
```

This means that if you set `details.fee` to `0`, this check will pass, even if the real fee is greater than zero. 

### Recommendation: 

If this is the intended behavior and you would like strategists to have a number they can use to accept all fee levels, I would recommend choosing a number other than zero (since it's a realistic value that strategists may want to set fees for). 

Otherwise, adjust the check as follows:

```solidity
- if (details.fee != uint24(0) && fee != details.fee) { 
+ if (fee != details.fee) { 
    revert InvalidFee(); 
}
```

For more flexibility, you could also allow all fees lower than the strategist set fee to be acceptable:

```solidity
- if (details.fee != uint24(0) && fee != details.fee) { 
+ if (fee > details.fee) { 
    revert InvalidFee(); 
}
```

### Notes & Impressions

#### Notes 
Let's break it into two parts:

- Condition A: `details.fee != uint24(0)`
- Condition B: `fee != details.fee`

For the code to revert, BOTH conditions must be TRUE. Here's a truth table showing all possibilities:

```
details.fee    fee    Condition A    Condition B    Will Revert?
--------------------------------------------------------------
0              0      FALSE          FALSE          NO
0              0.3%   FALSE          TRUE           NO
0              1%     FALSE          TRUE           NO
0.3%           0      TRUE           TRUE           YES
0.3%           0.3%   TRUE           FALSE          NO
0.3%           1%     TRUE           TRUE           YES
1%             0      TRUE           TRUE           YES
1%             0.3%   TRUE           TRUE           YES
1%             1%     TRUE           FALSE          NO
```

The developer's actual intention was likely this: They wanted to create a system where strategists could either:

1. Specify an exact fee that must be matched (like saying "only work with 0.3% pools"), or
2. Allow their strategy to work with any fee pool by setting `details.fee` to zero (like a wildcard)

However, there's a design flaw in using zero as the wildcard value. Why? Because zero is actually a valid fee value that a pool might have. This creates ambiguity - when a strategist sets `details.fee` to zero, are they saying:

- "I want this to work with any fee pool" (wildcard), or
- "I specifically want this to work only with zero-fee pools"?

This is why the security researcher recommended using a different special value as the wildcard. For example, using the maximum possible value (type(uint24).max) would be better because it's not a realistic fee value - no Uniswap pool would ever have that fee.

#### Impressions

I think special attention should be given to situations where multiple conditions are connected with 'and' during the audit. We can use a truth table to analyze whether all conditions match the expected results.

### Tools
- [[truth_table]]
### Refine
- [[1-Business_Logic]]

---
## [M-05] If auction time is reduced, `withdrawProxy` can lock funds from final auctions
----
- **Tags**: #business_logic 
- Number of finders: 4
- Difficulty: Medium
---
### Description

```solidity
  function handleNewLiquidation(
    uint256 newLienExpectedValue,
    uint256 finalAuctionDelta
  ) public {
    require(msg.sender == VAULT());
    WPStorage storage s = _loadSlot();
    unchecked {
      s.expected += newLienExpectedValue.safeCastTo88();
      s.finalAuctionEnd = (block.timestamp + finalAuctionDelta).safeCastTo40();
    }
  }
```

When a new liquidation happens, the `withdrawProxy` sets `s.finalAuctionEnd` to be equal to the new incoming auction end. This will usually be fine, because new auctions start later than old auctions, and they all have the same length. 

However, if the auction time is reduced on the Router, it is possible for a new auction to have an end time that is sooner than an old auction. The result will be that the WithdrawProxy is claimable before it should be, and then will lock and not allow anyone to claim the funds from the final auction. 

### Recommendation: 

Replace this with a check like:
```solidity
uint40 auctionEnd = (block.timestamp + finalAuctionDelta).safeCastTo40(); 
if (auctionEnd > s.finalAuctionEnd) s.finalAuctionEnd = auctionEnd;
```
### Discussion

### Notes & Impressions

#### Notes 

The problem occurs because the code always overwrites the `finalAuctionEnd` time with the end time of the newest auction. Usually, this works fine because:

- New auctions typically start after old ones
- All auctions normally have the same duration
- Therefore, newer auctions would naturally end later than older ones

However, imagine this scenario:

1. Auction A starts at time 100 with a duration of 48 hours (ends at time 148)
2. The protocol admin reduces the auction duration to 24 hours
3. Auction B starts at time 110 with the new shorter duration (ends at time 134)
4. The `finalAuctionEnd` gets set to 134 (Auction B's end)
5. But Auction A is still running and won't finish until time 148!

This creates two problems:

1. The withdraw proxy becomes claimable too early (at time 134)
2. Once claimed, it becomes locked and can't receive funds from Auction A when it finally ends at time 148
#### Impressions
- Check how duration changes affect existing process
### Tools
### Refine
- [[1-Business_Logic]]

---
## [M-07] Call to Royalty Engine can block NFT auction
----
- **Tags**: #business_logic 
- Number of finders: 4
- Difficulty: Medium
---
### Description: 

`_generateValidOrderParameters()` calls `ROYALTY_ENGINE.getRoyaltyView()` twice. The first call is wrapped in a `try/catch`. This lets Astaria to continue even if the `getRoyaltyView()` reverts. However, the second call is not safe from this. 

Both these calls have the same parameters passed to it except the price (`startingPrice vs endingPrice`). In case they are different, there exists a possibility that the second call can revert. 

[CollateralToken.sol#L445-L535](https://github.com/AstariaXYZ/astaria-core/blob/7e9574606344f832855632f5ce8087a71ee480eb/src/CollateralToken.sol#L445-L535)
```solidity
  function _generateValidOrderParameters(
    CollateralStorage storage s,
    uint256 collateralId,
    uint256 startingPrice,
    uint256 endingPrice,
    uint256 maxDuration
  ) internal returns (OrderParameters memory orderParameters) {
    OfferItem[] memory offer = new OfferItem[](1);

... ...


    try
      s.ROYALTY_ENGINE.getRoyaltyView( //@audit once
        underlying.tokenContract,
        underlying.tokenId,
        startingPrice
      )
    returns (
      address payable[] memory foundRecipients,
      uint256[] memory foundAmounts
    ) {
      if (foundRecipients.length > 0) {
        recipients = foundRecipients;
        royaltyStartingAmounts = foundAmounts;
        (, royaltyEndingAmounts) = s.ROYALTY_ENGINE.getRoyaltyView( //@audit twice
          underlying.tokenContract,
          underlying.tokenId,
          endingPrice
        );
      }
    } catch {
      //do nothing
    }
    ... ...
  }
```
### Recommendation: 

Wrap the second call in a `try/catch`. In case of a revert, the execution will be transferred to an empty `catch` block. Here is a sample:

```solidity
if (foundRecipients.length > 0) { 
  try 
    s.ROYALTY_ENGINE.getRoyaltyView( 
      underlying.tokenContract, 
      underlying.tokenId, 
      endingPrice 
    ) returns (, uint256[] memory foundEndAmounts) { 
    recipients = foundRecipients; 
    royaltyStartingAmounts = foundAmounts; 
    royaltyEndingAmounts = foundEndAmounts; 
  } catch {} 
}
```
### Discussion

Astaria: Acknowledged. We have a change pending that removes the royalty engine as apart of multi token. 
Spearbit: Acknowledged.

### Notes & Impressions

#### Notes 
- The same function was called twice with different parameters
- One instance had error handling while the other didn't

#### Impressions
The developer might have reasoned: "If the first `getRoyaltyView()` call succeeds with `startingPrice`, then the second call with `endingPrice` should also work"


### Tools
### Refine

- [[1-Business_Logic]]

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

same as [[2023-02-astaria#[H-11] `processEpoch()` needs to be called regularly|[H-11] `processEpoch()` needs to be called regularly]]
### Tools
### Refine

- [[1-Business_Logic]]

---
## [M-10] `redeemFutureEpoch` transfers the shares from the `msg.sender` to the vault instead of from the `owner`
----
- **Tags**: #business_logic #mgs_sender_vs_owner
- Number of finders: 4
- Difficulty: Medium
---
### Description: 
`redeemFutureEpoch` transfers the vault shares from the `msg.sender` to the vault instead of from the owner. 
```solidity
  function redeemFutureEpoch(
    uint256 shares,
    address receiver,
    address owner,
    uint64 epoch
  ) public virtual returns (uint256 assets) {
... ...
    // check for rounding error since we round down in previewRedeem.


    ERC20(address(this)).safeTransferFrom(msg.sender, address(this), shares);
... ...
```
### Recommendation: 
The 1st parameter passed to the `ERC20(address(this)).safeTransferFrom` needs to be the owner:

```solidity
- ERC20(address(this)).safeTransferFrom(msg.sender, address(this), shares); 
+ ERC20(address(this)).safeTransferFrom(owner, address(this), shares);
```
### Discussion

### Notes & Impressions

#### Notes 
To understand why this is problematic, consider this scenario:

1. Alice owns 100 shares in the vault
2. Alice authorizes Bob to manage her shares
3. Bob tries to help Alice redeem her shares by calling `redeemFutureEpoch`
4. The function attempts to take the shares from Bob's account (`msg.sender`) instead of Alice's account (`owner`)
5. The transaction fails if Bob doesn't have the required shares, even though Alice has given permission
#### Impressions

`owner ≠ msg.sender`

### Tools
### Refine

- [[1-Business_Logic]]

---
## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}