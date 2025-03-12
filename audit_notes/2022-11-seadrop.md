# 2022-11-SeaDrop
---
- Category: #Dexes #CDP #services #cross-chain #leveraged_farming 
- Note Create 2025-03-12
- Platform: Spearbit
- Report Url: [2022-11-SeaDrop](https://github.com/spearbit/portfolio/blob/master/pdfs/Seadrop-Spearbit-Security-Review.pdf)
---
# Critical & High Risk Findings (xx)

---

{{Copy from High Risk Finding Template.md}}

---

# Medium Risk Findings (xx)

---
## [M-04] Token gated drops with a self-allowed `ERC721SeaDrop` or a variant of that can lead to the drop getting
----
- **Tags**: #business_logic 
- Number of finders: 3
- Difficulty: Medium
---
### Detail

There are scenarios where an actor with only 1 token from an allowed NFT can drain Token Gated Drops that are happening simultaneously or back to back. 
- Scenario 1 - An ERC721SeaDrop is registered as an `allowedNftToken` for itself
This is a simple example where an `ERC721SeaDrop` $N$ is registered by the owner or the `admin` as an `allowedNftToken` for its own token gated drop and during or before this drop (let's call this drop $D$) there is another token gated drop ($D^{\prime}$) for another `allowedNftToken` $N^{\prime}$, which does not need to be necessarily an `IERC721SeaDrop` token. Here is how an actor can drain the self-registered token gated drop:
1. The actor already owns or buys an $N^{\prime}$ token $t^{\prime}$ with wallet $w_0$. 
2. During $D^{\prime}$, the actor mints an $N$ token $t_0$ with wallet $w_0$ passing $N^{\prime}$ , $t^{\prime}$ to `mintAllowedTokenHolder` and transfer $t_0$ to another wallet if necessary to avoid the max mint per wallet limit (call this wallet $w_1$ which could still be $w_0$). 
3. Once $D$ starts or if it is already started, the actor mints another $N$ token $t_1$ with $w_1$ passing $N$, $t_0$ to `mintAllowedTokenHolder` and transfers $t_1$ to another wallet if necessary to avoid the max mint per wallet limit (call this wallet $w_2$ which could still be $w_1$) 
4. Repeat step 3 with the new parameters till we hit the `maxTokenSupplyForStage` limit for $D$.

```solidity
# during token gated drop D' 
t = seaDrop.mintAllowedTokenHolder(N, f, w, {N', [t']}) 

# during token gated drop D 
while ( have not reached maxTokenSupplyForStage ): 
	if ( w has reached max token per wallet ): 
		w' = newWallet() 
		N.transfer(w, w', t) 
		w = w' 
	t = seaDrop.mintAllowedTokenHolder(N, f, w, {N, [t]})
```

- Scenario 2 - Two `ERC721SeaDrop` tokens are doing a simultaneous token gated drop promotion
In this scenario, there are 2 `ERC721SeaDrop` tokens $N_1$, $N_2$ where they are running simultaneous token gated drop promotions. Each is allowing a wallet/bag holder from the other token to mint a token from their project. So if you have an $N_1$ token you can mint an $N_2$ token and vice versa. Now if an actor already has an $N_1$ or $N_2$ token maybe from another token gated drop or from an allow list mint, they can drain these 2 drops till one of them hits `maxTokenSupplyForStage` limit.

```
# wallet already holds token from N1 

while ( have not reached N1.maxTokenSupplyForStage or N2.maxTokenSupplyForStage): 

	w = newWalletIfMaxMintReached(N1, w, t) # this also transfers t to the new wallet 
	w = newWalletIfMaxMintReached(N2, w, t) # this also transfers t to the new wallet 
	
	t = seaDrop.mintAllowedTokenHolder(N2, f, w, {N1, [t]}) 
	t = seaDrop.mintAllowedTokenHolder(N1, f, w, {N2, [t]})
```

This scenario can be extended to more complex systems, but the core logic stays the same. 

Also, it's good to note that in general `maxTotalMintableByWallet` for token gated drops and `maxMintsPerWallet` for public mints are not fully enforceable since actors can either distribute their allowed tokens between multiple wallets to mint to their full potential for the token gated drops. And for public mints, they would just use different wallets. It does add extra gas for them to mint since they can't batch mint. That said these limits are enforceable for the signed and allowed mints (or you could say the enforcing has been moved to some off-chain mechanism)
### Discussion

**OpenSea**: 
In scenario 1, I think a check against allowing a token to register itself as an allowed token-gated-drop is reasonable. 

In scenario 2, we could also check against allowing a token to register a second token as an allowed-token-gateddrop if that token's` currentSupply < maxSupply` and has the first token registered as its own token-gated drop. This has the caveat that a token could implement itself to have a changeable `maxSupply`, which would bypass these checks... open to other implementation ideas. 

I think both cases should be documented in the comments

**Spearbit**: 
Agree with OpenSea regarding a check for a self-allowed token gated drop in scenario 1. 
For scenario 2 or a more complex variant of it like (can be even more complex than below):

```
// N1, N2: IERC721SeaDrop tokens with token gated drop promotions 
// Each arrow in the diagram below represents an allowed mint mechanism 
// A -> B : a person with a t_a token from A can mint a token of B (B can potentially mark t_a as redeemed on mint) 

M0 -> N1 -> M1 -> M2 -> ... -> Mk -> 
	  N2 -> O1 -> O2 -> ... -> Oj -> N1
```

It would be hard to have an implementation that would check for these kind of behaviors. But we agree that documenting these scenarios in the comments would be great.

**OpenSea**: 
Added `error TokenGatedDropAllowedNftTokenCannotBeDropToken()` and added comments for scenario no 2.
### Notes & Impressions

**When designing systems with privileged access based on ownership of other assets, always check for and prevent circular dependencies**.
### Tools
### Refine
- [[1-Business_Logic]]

---
## [M-05] `ERC721A` has mint caps that are not checked by `ERC721SeaDrop`
----
- **Tags**: #business_logic #min/max_cap_validation #erc721a
- Number of finders: 4
- Difficulty: Medium
---
### Context

```solidity
    function mintSeaDrop(address minter, uint256 quantity)
        external
        payable
        override
        onlySeaDrop
    {
        // Mint the quantity of tokens to the minter.
        _mint(minter, quantity);
    }
```
### Description

`ERC721SeaDrop` inherits from ERC721A which packs balance, `numberMinted`, `numberBurned`, and an extra data chunk in 1 storage slot (64 bits per substorage) for every address. This would add an inherent cap of $2^{64}-1$ to all these different fields. Currently, there is no check in ERC721A's `_mint` for `quantity` nor in ERC721SeaDrop's `mintSeaDrop` function. 

Also, if we almost reach the max cap for a `balance` by an owner and someone else transfers a token to this owner, there would be an overflow for the `balance` and possibly the number of mints in the `_packedAddressData`. The overflow could possibly reduce the balance and the `numberMinted` to a way lower number and `numberBurned` to a way higher number
### Recommended Mitigation

We should have an additional check if `quantity` would exceed the mint cap in `mintSeaDrop`
### Discussion

We will add checks around ERC721A limits. We have added a restraint that `maxSupply` cannot be set to greater than $2^{64}-1$ so balance nor number minted can exceed this. 
See the below:
```solidity
        // Ensure the max supply does not exceed the maximum value of uint64.
        if (newMaxSupply > 2**64 - 1) {
            revert CannotExceedMaxSupplyOfUint64(newMaxSupply);
        }
```

### Notes & Impressions

The `ERC721A` contract (which `ERC721SeaDrop` inherits from) uses an optimization technique called storage packing. This means it efficiently stores multiple pieces of data in a single storage slot to save gas. Specifically, it packs four different values for each address into a single 256-bit storage slot:

1. Token balance (64 bits)
2. Number of tokens minted (64 bits)
3. Number of tokens burned (64 bits)
4. Extra data (64 bits)

This means each of these values has an inherent maximum cap of 2^64-1 (approximately 18.4 quintillion). While this seems enormous, the issue is that the `mintSeaDrop` function doesn't check if a mint would exceed this limit.

### Tools
### Refine

- [[1-Business_Logic]]
- [[19-MinOrMax_Cap_Validation]]

---
---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}