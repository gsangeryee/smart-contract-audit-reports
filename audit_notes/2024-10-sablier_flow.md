# 2024-10-sablier_flow
---
- Category: chose from [[protocol_categories]]
- Note Create 2024-10-30
- Platform: cantina
- report url: [https://cantina.xyz/portfolio/0e86d73a-3c3b-4b2b-9be5-9cecd4c7a5ac](https://cantina.xyz/portfolio/0e86d73a-3c3b-4b2b-9be5-9cecd4c7a5ac)
---
## Findings Summary

### High Severity Findings
1. [[High Findings]](link to details)
2. [[High Findings]](link to details)

### Medium Severity Findings
1. [[Medium Findings]](link to details)
2. [[Medium Findings]](link to details)

---
# High Risk Findings (xx)

---

## [H-01] Sender can brick stream by forcing overflow in debt calculation

----
- **Tags**:  [[report_tags]]
- Number of finders: 2
---
### Detail

The `_ongoingDebtOf()` internal function is used to calculate the amount of funds owed to the stream recipient since the last snapshot. As a part of these calculations, the `scaledOngoingDebt` is calculated by multiplying the seconds that have passed since the last snapshot by the rate per second.

```solidity
uint128 scaledOngoingDebt = elapsedTime * ratePerSecond;
```

Since `elapsedTime` and `scaledOngoingDebt` are both uint128, any result of the multiplication that is greater than `uint128` will overflow and cause a revert. 

Note that this multiplication does not require an unrealistically high balance of the token, only for `ratePerSecond` to be set to a high value, which is completely in the control of the `sender`. 

This is a major concern because, once this calculation overflows, any calls to `withdraw()`, `refund()`, or to adjust the rate back down will all fail, because they all rely on this function. As a result, once this change happens, there is nothing anyone can do to receive funds from the stream, and all funds will permanently be stuck. 

This fact could lead to problems in two situations: 
1. It could be abused by a sender who is angry with a recipient to lock all previously streamed funds that have not yet been withdrawn, which should be the property of the recipient. 
2. It could occur because a `ratePerSecond` is set to too high of a value accidentally, and then cannot be recovered by either party.

### Proof of Concept

The following proof of concept (which can be placed in any file that imports `Integration_Test`) demonstrates the issue:

```solidity
function test_HighRPSRevert() public { 
	deal(address(usdc), address(this), DEPOSIT_AMOUNT_6D);
	usdc.approve(address(flow), DEPOSIT_AMOUNT_6D);
	
	address receiver = makeAddr("receiver");
	
	uint streamId = flow.createAndDeposit({ 
		sender: address(this),
		recipient: receiver,
		ratePerSecond: UD21x18.wrap(type(uint128).max),
		token: usdc,
		transferable: true,
		amount: DEPOSIT_AMOUNT_6D 
	});
	
	vm.warp(block.timestamp + 12); 
	
	vm.expectRevert();
	flow.totalDebtOf(streamId);
	
	vm.expectRevert();
	flow.pause(streamId);
	
	vm.expectRevert();
	vm.prank(receiver);
	flow.withdraw(streamId, receiver, 1);
}
```
### Recommended Mitigation

Use a `uint256` for `scaledOngoingDebt`, and carry this type through all functions until the value is compared to the balance. At that point, you can safely downcast to `uint128`.
### Notes

- `uint(128, 64) = uint(128, 64) * uint(128, 64)`
#### Impressions

*For any multiplication involving unsigned integers (`uint`), attention should be paid if the result is not stored in a `uint256`*

### Refine

- [[common_issues#Integer Overflow]]

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