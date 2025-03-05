# 2023-02-23-seaport
---
- Category: #Dexes #cross-chain #rwa #NFT_Marketplace #Prediction_Market #seaport
- Note Create 2025-01-06
- Platform: Separbit
- Report Url: [2023-02-23-Seaport](https://github.com/spearbit/portfolio/blob/master/pdfs/Seaport-Spearbit-Security-Review.pdf)
---
# High Risk Findings (xx)

---

{{Copy from High Risk Finding Template.md}}

---

# Medium Risk Findings (xx)

---
## [M-01] The spent offer amounts provided to `OrderFulfilled` for collection of (advanced) orders is not the actual amount spent in general
----
- **Tags**: #wrong_math #business_logic 
- Number of finders: 4
- Difficulty: Hard
---
### Context:
[lib/OrderCombiner.sol#L455-L463](https://github.com/ProjectOpenSea/seaport/blob/8d95af1a952ac0ebf784e323e5e1a2b5d687cc4f/contracts/lib/OrderCombiner.sol#L455-L463)
```solidity
                // Emit an OrderFulfilled event.
                _emitOrderFulfilledEvent(
                    orderHash,
                    orderParameters.offerer,
                    orderParameters.zone,
                    recipient,
                    orderParameters.offer,
                    orderParameters.consideration
                );
```

[lib/OrderFulfiller.sol#L377-L385](https://github.com/ProjectOpenSea/seaport/blob/8d95af1a952ac0ebf784e323e5e1a2b5d687cc4f/contracts/lib/OrderFulfiller.sol#L377-L385)
```solidity
        // Emit an event signifying that the order has been fulfilled.
        emit OrderFulfilled(
            orderHash,
            offerer,
            zone,
            fulfiller,
            spentItems,
            receivedItems
        );
```
### Description
When `Seaport` is called to `fulfill` or match a collection of (advanced) orders, the `OrderFulfilled` is called before applying fulfillments and executing transfers. The offer and consideration items have the following forms:

$$
C=\left(I_t, T, i, a_{\text {curr }}, R, a_{\text {curr }}\right)
$$

$$
O=\left(I_t, T, i, a_{\text {curr }},a_{\text {curr }}\right)
$$
Where

| parameter  | description                                                                                            |
| ---------- | ------------------------------------------------------------------------------------------------------ |
| $I_t$      | itemType                                                                                               |
| $T$        | token                                                                                                  |
| $i$        | identifier                                                                                             |
| $a_{curr}$ | the interpolation of `starAmount` and `endAmount` depending on the time and the fraction of the order. |
| $R$        | consideration item's `recipient`                                                                       |
| $O$        | offer item                                                                                             |
| $C$        | consideration item                                                                                     |
The `SpentItems` and `ReceivedItem` items provided to `OrderFulfilled` event ignore the last component of the `offer/consideration` items in the above form since they are redundant. 

`Seaport` enforces that all consideration items are used. But for the endpoints in this context, we might end up with offer items with only a portion of their amounts being spent. So in the end $O.a_{curr}$ might not be the amount spent for this offer item, but `OrderFulfilled` emits $O.a_{curr}$ as the amount spent. This can cause discrepancies in off-chain bookkeeping by agents listening for this event. 

The `fulfillOrder` and `fulfillAdvancedOrder` do not have this issue, since all items are enforced to be used. These two endpoints also differ from when there are collections of (advanced) orders, in that they would emit the `OrderFulfilled` at the of their call before clearing the reentrancy guard. 

### Recommendation: 

Make sure the accounting is updated to only provide the spent offer item amounts to `OrderFulfilled`. Moving the emission of this event to the end of the call flow, before clearing the reentrancy guard like the above mentioned simpler endpoint would make it easier to provide the correct values (and also would make the whole flow between different endpoints more consistent and potentially create an opportunity to refactor the codebase further). 
### Discussion

**Seaport**: Fixed in PR 839 by making sure all unspent offer amounts are transferred to the recipient provided by the `msg.sender`. 

```solidity
// Get the offer items from the order parameters
OfferItem[] memory offer = parameters.offer;

// Store the total number of offer items for efficiency
uint256 totalOfferItems = offer.length;

// Process each offer item to handle any unspent amounts
for (uint256 j = 0; j < totalOfferItems; ++j) {
    OfferItem memory offerItem = offer[j];
    
    // originalAmount represents what was initially offered
    uint256 originalAmount = offerItem.endAmount;
    
    // unspentAmount represents what wasn't used in the trade
    uint256 unspentAmount = offerItem.startAmount;

    // If there's any unspent amount, transfer it to the recipient
    if (unspentAmount != 0) {
        _transfer(
            _convertOfferItemToReceivedItemWithRecipient(
                offerItem,
                _recipient
            ),
            parameters.offerer,
            parameters.conduitKey,
            accumulator
        );
    }

    // Restore the original amount for accurate event emission
    offerItem.startAmount = originalAmount;
}
```

**Spearbit**: Verified.

### Notes & Impressions

#### Notes 
When the protocol emits the `OrderFulfilled` event for collection orders, it reports the full amount from the offer, even if only a portion of that offer was actually used in the transaction
#### Impressions

*event emission issues*

### Tools
### Refine

- [[1-Business_Logic]]

---
## [M-02] The spent offer item amounts shared with a `zone` for restricted (advanced) orders or with a contract `offerer` for orders of `CONTRACT` order type is not the actual spent amount in general
----
- **Tags**: #business_logic 
- Number of finders: 4
- Difficulty: Hard
---
### Detail

same as [[2023-02-seaport#[M-01] The spent offer amounts provided to `OrderFulfilled` for collection of (advanced) orders is not the actual amount spent in general|[M-01] The spent offer amounts provided to `OrderFulfilled` for collection of (advanced) orders is not the actual amount spent in general]]

#### Impressions

### Tools
### Refine

- [[1-Business_Logic]]

---
## [M-03] Empty `criteriaResolvers` for criteria-based contract orders
----
- **Tags**: #business_logic #validation #bait_and_switch
- Number of finders: 4
- Difficulty: Medium
---
### Description

There is a deviation in how criteria-based items are resolved for contract orders. For contract orders which have offers with criteria, the `_compareItems` function checks that the contract offerer returned a corresponding non-criteria based `itemType` when `identifierOrCriteria` for the original item is `0`, i.e., offering from an entire collection. Afterwards, the `orderParameters.offer` array is replaced by the `offer` array returned by the contract offerer. 
[lib/OrderValidator.sol#L312-L315](https://github.com/ProjectOpenSea/seaport/blob/8d95af1a952ac0ebf784e323e5e1a2b5d687cc4f/contracts/lib/OrderValidator.sol#L312-L315)
```solidity
    function _compareItems(
        MemoryPointer originalItem,
        MemoryPointer newItem
    ) internal pure returns (uint256 isInvalid) {
    ... ...
            if and(gt(itemType, 3), iszero(identifier)) {
                // replace item type
                itemType := sub(3, eq(itemType, 4))
                identifier := mload(add(newItem, Common_identifier_offset))
```

[lib/OrderValidator.sol#L434](https://github.com/ProjectOpenSea/seaport/blob/8d95af1a952ac0ebf784e323e5e1a2b5d687cc4f/contracts/lib/OrderValidator.sol#L434)
```solidity
            orderParameters.offer = offer;  // replaced by offer
```

For other criteria-based orders such as offers with `identifierOrCriteria = 0`, the `itemType` of the order is only updated during the criteria resolution step. 
[lib/CriteriaResolution.sol#L119](https://github.com/ProjectOpenSea/seaport/blob/8d95af1a952ac0ebf784e323e5e1a2b5d687cc4f/contracts/lib/CriteriaResolution.sol#L119)
```solidity
    function _applyCriteriaResolvers(
        AdvancedOrder[] memory advancedOrders,
        CriteriaResolver[] memory criteriaResolvers
    ) internal pure {
   ... ...
                    _updateCriteriaItem(.  // criteria solution step
```

This means that for such offers there should be a corresponding `CriteriaResolver` struct. See the following test:

```javascript
modified test/advanced.spec.ts 
@@ -3568,9 +3568,8 @@ describe(`Advanced orders (Seaport v${VERSION})`, function () { 
		// Seller approves marketplace contract to transfer NFTs 
		await set1155ApprovalForAll(seller, marketplaceContract.address, true); 
		
-       const { root, proofs } = merkleTree([nftId]); 

-       const offer = [getTestItem1155WithCriteria(root, toBN(1), toBN(1))]; 
+       const offer = [getTestItem1155WithCriteria(toBN(0), toBN(1), toBN(1))]; 
        
        const consideration = [ 
	      getItemETH(parseEther("10"), parseEther("10"), seller.address), 
@@ -3578,8 +3577,9 @@ describe(`Advanced orders (Seaport v${VERSION})`, function () { 
		  getItemETH(parseEther("1"), parseEther("1"), owner.address), 
		]; 
+       // Replacing by `const criteriaResolvers = []` will revert 
        const criteriaResolvers = [ 
-         buildResolver(0, 0, 0, nftId, proofs[nftId.toString()]), 
+         buildResolver(0, 0, 0, nftId, []), 
        ]; 
        
        const { order, orderHash, value } = await createOrder(
```

However, in case of contract offers with `identifierOrCriteria = 0`, Seaport 1.2 does not expect a corresponding `CriteriaResolver` struct and will revert if one is provided as the `itemType` was updated to be the corresponding non-criteria based `itemType`. See `advanced.spec.ts#L510` for a test case. 
[itemType](https://github.com/ProjectOpenSea/seaport/blob/8d95af1a952ac0ebf784e323e5e1a2b5d687cc4f/contracts/lib/CriteriaResolution.sol#L192)
```solidity
        // Ensure the specified item type indicates criteria usage.
        if (!_isItemWithCriteria(itemType)) {
            _revertCriteriaNotEnabledForItem();
        }
```

*Note*: this also means that the fulfiller cannot explicitly provide the identifier when a contract order is being fulfilled. 

A malicious contract may use this to their advantage. For example, assume that a contract offerer in Seaport only accepts criteria-based offers. The fulfiller may first call `previewOrder` where the criteria is always resolved to a rare NFT, but the actual execution would return an uninteresting NFT. If such offers also required a corresponding resolver (similar behaviour as regular criteria based orders), then this could be fixed by explicitly providing the `identifier--`akin to a slippage check. 

In short, for regular criteria-based orders with `identifierOrCriteria = 0` the fulfiller can pick which `identifier` to receive by providing a `CriteriaResolver` (as long as it's valid). For contract orders, fulfillers don't have this option and contracts may be able to abuse this. 

### Recommendation: 
An alternative approach to criteria-based contract orders would be to remove the extra case in `_compareItems`. Now, contract offers will have to return the same `itemType` and `identifierOrCriteria` when a `generateOrder` call is made. However, this means that the fulfiller will be able to choose the `identifier` it wants to receive. This may not be the ideal in some cases, but it remains consistent with regular orders. 

### Discussion
Seaport: We documented this deviation in PR 849. 
Spearbit: Verified
### Notes & Impressions

#### Notes 
- When someone checks the order preview (`previewOrder`), the contract shows it will give a valuable, rare NFT
- But when the actual order executes, it gives a different, less valuable NFT
- Because fulfillers can't provide a CriteriaResolver for contract orders, they have no way to ensure they get the specific NFT they saw in the preview

#### Impressions
"bait and switch" scenario
>*"Bait and switch" is a deceptive marketing tactic in which a seller advertises a product or service at a very low price (the "bait") to attract customers, but then tries to convince them to buy a more expensive product or service (the "switch").*
### Tools
### Refine

- [[1-Business_Logic]]

---
## [M-04] Advance orders of CONTRACT order types can generate orders with less consideration items that would break the aggregation routine
----
- **Tags**: #business_logic #array_index 
- Number of finders: 4
- Difficulty: Medium
---
### Description: 

When `Seaport` gets a collection of advanced orders to fulfill or match, if one of the orders has a CONTRACT order type, Seaport calls the `generateOrder(...)` endpoint of that order's `offerer. generateOrder(...)` can provide fewer consideration items for this order. So the total number of consideration items might be less than the ones provided by the `caller`. 
[OrderValidator.sol#L444-L447](https://github.com/ProjectOpenSea/seaport/blob/8d95af1a952ac0ebf784e323e5e1a2b5d687cc4f/contracts/lib/OrderValidator.sol#L444-L447)
```solidity
    function _getGeneratedOrder(
        OrderParameters memory orderParameters,
        bytes memory context,
        bool revertOnInvalid
    )
    ... ...
            // New consideration items cannot be created.
            if (newConsiderationLength > originalConsiderationArray.length) {
                return _revertOrReturnEmpty(revertOnInvalid, orderHash);
            }
```

But since the `caller` would need to provide the fulfillment data beforehand to `Seaport`, they might use indices that would turn to be out of range for the consideration in question after the modification applied for the contract `offerer` above. If this happens, the whole call will be reverted. 

[FulfillmentApplier.sol#L561-L569](https://github.com/ProjectOpenSea/seaport/blob/8d95af1a952ac0ebf784e323e5e1a2b5d687cc4f/contracts/lib/FulfillmentApplier.sol#L561-L569)
```solidity
    function _aggregateValidFulfillmentConsiderationItems(
        AdvancedOrder[] memory advancedOrders,
        FulfillmentComponent[] memory considerationComponents,
        Execution memory execution
    ) internal pure {
    ... ...
            // Retrieve item index using an offset of the fulfillment pointer.
            let itemIndex := mload(
                add(mload(fulfillmentHeadPtr), Fulfillment_itemIndex_offset)
            )


            // Ensure that the order index is not out of range.
            if iszero(lt(itemIndex, mload(considerationArrPtr))) {
                throwInvalidFulfillmentComponentData()
            }
```

This issue is in the same category as *Advance orders of CONTRACT order types can generate orders with different consideration recipients that would break the aggregation routine.*
### Recommendation: 

In order for the `caller` to be able to `fulfill/match` orders by figuring out how to aggregate and match different consideration and offer items, they would need to be able to have access to all the data before calling into `Seaport`. Contract `offerers` are supposed to (it is not enforced currently) implement previewOrder which the caller can use before making a call to Seaport. But there is no guarantee that the data returned by `previewOrder` and `generateOrder` for the same shared inputs would be the same. 

We can enforce that the contract offerer does not return fewer consideration items. If it needed to return less it can either revert or provide a `0` amount. If the current conditions are going to stay the same, it is recommended to document this scenario and also provide more comments/documentation for `ContractOffererInterface`. 

### Discussion
Seaport: Addressed in PR 842. 
Spearbit: Verified.
### Notes & Impressions

#### Notes 
Real-World Analogy: Imagine you're running a trading card marketplace where people can make complex trades. Let's say Alice wants to trade with Bob through your marketplace.

Alice says: "I'll give my rare Charizard card, and in return, I want:

1. Two Pikachu cards
2. One Mewtwo card
3. Three energy cards"

Now, Bob is a special kind of trader (like a CONTRACT order type) who can modify what he gives in return after Alice makes her offer. The marketplace (Seaport) allows this.

Alice creates instructions for how to handle the trade: "Take the third item (energy cards) and give them to my friend Charlie" "Take the second item (Mewtwo) and give it to my sister Diana" "Take the first item (Pikachu cards) and keep them for myself"

But when Bob actually processes the trade, he decides to only give:

1. Two Pikachu cards
2. One Mewtwo card

The problem: Alice's instructions mentioned the third item (energy cards), but they no longer exist in Bob's final offer! The trade would fail because the instructions reference something that's no longer there.

#### Impressions
Focus on:
1. State Changes Between Preview and Execution
2. Array Index Validation

### Tools
### Refine

{{ Refine to typical issues}}

---
## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}