# 2022-12-NounsDAO
---
- Category: #Dexes #CDP #services #cross-chain #Synthetics #steam
- Note Create 2025-03-05
- Platform: Sherlock
- Report Url: [2022-12-NounsDAO](https://app.sherlock.xyz/audits/contests/27)
---
# Critical & High Risk Findings (xx)

---

{{Copy from High Risk Finding Template.md}}

---

# Medium Risk Findings (xx)

---
## [M-07] Payer cannot withdraw accidental extra funds sent to the contract without canceling
----
- **Tags**: #business_logic 
- Number of finders: 8
- Difficulty: Easy
---
### Summary

If a different ERC20 is accidentally sent to the contract, the Payer can withdraw it using the `rescueERC20` function. However, if they accidentally send extra of the streaming token's funds to the contract, the only way to withdraw it is to cancel the stream.
### Detail

The Nouns team seems to have made the decision that they should protect against accidental funds being sent into the contract. They implemented the `rescueERC20` function to accomplish this.

However, the `rescueERC20` function only works for non-stream tokens. If they accidentally send too much of the streaming token (which seems like a likely scenario), there is no similar rescue function to retrieve it.

Instead, their only option is to cancel the stream. In a protocol that's intended to be run via a governance system, canceling the stream could cause problems for the receiver (for example, if they are unable to pass a vote to restart the stream).
### Impact

If too many stream tokens are sent into the contract, the whole stream will need to be canceled to retrieve them.
### Proof of Concept

[Stream.sol#L237-L259](https://github.com/sherlock-audit/2022-11-nounsdao/blob/5def6ce65aeae7c55c66bbeb0e5f92f2ad169211/src/Stream.sol#L237-L259)
```
    function cancel() external onlyPayerOrRecipient {
        address payer_ = payer();
        address recipient_ = recipient();
        IERC20 token_ = token();


        uint256 recipientBalance = balanceOf(recipient_);


        // This zeroing is important because without it, it's possible for recipient to obtain additional funds
        // from this contract if anyone (e.g. payer) sends it tokens after cancellation.
        // Thanks to this state update, `balanceOf(recipient_)` will only return zero in future calls.
        remainingBalance = 0;


        if (recipientBalance > 0) token_.safeTransfer(recipient_, recipientBalance);


        // Using the stream's token balance rather than any other calculated field because it gracefully
        // supports cancelling the stream even if payer hasn't fully funded it.
        uint256 payerBalance = tokenBalance();
        if (payerBalance > 0) {
            token_.safeTransfer(payer_, payerBalance);
        }


        emit StreamCancelled(msg.sender, payer_, recipient_, payerBalance, recipientBalance);
    }
```
### Recommended Mitigation

Adjust the rescueERC20 function to also allow for withdrawing excess stream tokens, as follows:
```
function rescueERC20(address tokenAddress, uint256 amount) external onlyPayer {
-    if (tokenAddress == address(token())) revert CannotRescueStreamToken();
+    if (tokenAddress == address(token()) && amount < tokenBalance() - remainingBalance) revert AmountExceedsBalance;

    IERC20(tokenAddress).safeTransfer(msg.sender, amount);
}
```

### Discussion

### Notes & Impressions

Streaming Token should be `rescue`
### Tools
### Refine

- [[1-Business_Logic]]

---


## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}