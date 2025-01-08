# 2023-02-Astaria
---
- Category: #Dexes #CDP #services #cross-chain #rwa 
- Note Create 2025-01-08
- Platform: Spearbit
- Report Url: [2023-02-Astaria](https://github.com/spearbit/portfolio/blob/master/pdfs/Astaria-Spearbit-Security-Review.pdf)
---
# High Risk Findings (xx)

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