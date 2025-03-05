# 2022-11-isomorph
---
- Category: #liquid_staking #yield #Synthetics #privacy
- Note Create 2025-03-04
- Platform: sherlock
- Report Url: [2022-11-isomorph](https://audits.sherlock.xyz/contests/22/report)
---
# Critical & High Risk Findings (xx)

---
## [H-01] User is unable to partially payback loan if they aren't able to post enough isoUSD to bring them back to minOpeningMargin
----
- **Tags**: #business_logic #Excessive_Constraint_Propagation 
- Number of finders: 1
- Difficulty: Hard
---
The only way for a user to reduce their debt is to call closeLoan. If the amount repaid does not bring the user back above minOpeningMargin then the transaction will revert. This is problematic for users that wish to repay their debt but don't have enough to get back to `minOpeningMargin` as it could lead to unfair liquidations.
### Detail

```
    if(outstandingisoUSD >= TENTH_OF_CENT){ //ignore leftover debts less than $0.001
        uint256 collateralLeft = collateralPosted[_collateralAddress][msg.sender] - _collateralToUser;
        uint256 colInUSD = priceCollateralToUSD(currencyKey, collateralLeft); 
        uint256 borrowMargin = (outstandingisoUSD * minOpeningMargin) / LOAN_SCALE;
        require(colInUSD > borrowMargin , "Remaining debt fails to meet minimum margin!");
    }
```

The checks above are done when a user calls closeLoan. This ensures that the user's margin is back above minOpeningMargin before allowing them to remove any collateral. This is done as a safeguard to block loans users from effectively opening loans at lower than desired margin. This has the unintended consequence that as user cannot pay off any of their loan if they do not increase their loan back above minOpeningMargin. This could prevent users from being able to save a loan that is close to liquidation causing them to get liquidated when they otherwise would have paid off their loan.
### Impact

User is unable to make partial repayments if their payment does not increase margin enough
### Code Snippet

[Vault_Synths.sol#L197-L248](https://github.com/sherlock-audit/2022-11-isomorph/blob/5d4137b91c432dddb1ef9c1ac3e5b7be3dbd0d3a/contracts/Isomorph/contracts/Vault_Synths.sol#L197-L248)
```solidity
    function closeLoan(
        address _collateralAddress,
        uint256 _collateralToUser,
        uint256 _USDToVault
        ) external override whenNotPaused 
        {
        _collateralExists(_collateralAddress);
        _closeLoanChecks(_collateralAddress, _collateralToUser, _USDToVault);
        //make sure virtual price is related to current time before fetching collateral details
        //slither-disable-next-line reentrancy-vulnerabilities-1
        _updateVirtualPrice(block.timestamp, _collateralAddress);
        (   
            bytes32 currencyKey,
            uint256 minOpeningMargin,
            ,
            ,
            ,
            uint256 virtualPrice,
            
        ) = _getCollateral(_collateralAddress);
        //check for frozen or paused collateral
        _checkIfCollateralIsActive(currencyKey);
        uint256 isoUSDdebt = (isoUSDLoanAndInterest[_collateralAddress][msg.sender] * virtualPrice) / LOAN_SCALE;
        require( isoUSDdebt >= _USDToVault, "Trying to return more isoUSD than borrowed!");
        uint256 outstandingisoUSD = isoUSDdebt - _USDToVault;
        if(outstandingisoUSD >= TENTH_OF_CENT){ //ignore leftover debts less than $0.001
            uint256 collateralLeft = collateralPosted[_collateralAddress][msg.sender] - _collateralToUser;
            uint256 colInUSD = priceCollateralToUSD(currencyKey, collateralLeft); 
            uint256 borrowMargin = (outstandingisoUSD * minOpeningMargin) / LOAN_SCALE;
            require(colInUSD > borrowMargin , "Remaining debt fails to meet minimum margin!");
        }
        
        //record paying off loan principle before interest
        //slither-disable-next-line uninitialized-local-variables
        uint256 interestPaid;
        uint256 loanPrinciple = isoUSDLoaned[_collateralAddress][msg.sender];
        if( loanPrinciple >= _USDToVault){
            //pay off loan principle first
            isoUSDLoaned[_collateralAddress][msg.sender] = loanPrinciple - _USDToVault;
        }
        else{
            interestPaid = _USDToVault - loanPrinciple;
            //loan principle is fully repaid so record this.
            isoUSDLoaned[_collateralAddress][msg.sender] = 0;
        }
        //update mappings with reduced amounts
        isoUSDLoanAndInterest[_collateralAddress][msg.sender] = isoUSDLoanAndInterest[_collateralAddress][msg.sender] - ((_USDToVault * LOAN_SCALE) / virtualPrice);
        collateralPosted[_collateralAddress][msg.sender] = collateralPosted[_collateralAddress][msg.sender] - _collateralToUser;
        emit ClosedLoan(msg.sender, _USDToVault, currencyKey, _collateralToUser);
        //Now all effects are handled, transfer the assets so we follow CEI pattern
        _decreaseLoan(_collateralAddress, _collateralToUser, _USDToVault, interestPaid);
        }
```
### Recommended Mitigation

I recommend adding a separate function that allows users to pay off their loan without removing any collateral:

```solidity
function paybackLoan(
    address _collateralAddress,
    uint256 _USDToVault
    ) external override whenNotPaused 
    {
    _collateralExists(_collateralAddress);
    _closeLoanChecks(_collateralAddress, 0, _USDToVault);
    //make sure virtual price is related to current time before fetching collateral details
    //slither-disable-next-line reentrancy-vulnerabilities-1
    _updateVirtualPrice(block.timestamp, _collateralAddress);
    (   
        bytes32 currencyKey,
        uint256 minOpeningMargin,
        ,
        ,
        ,
        uint256 virtualPrice,
        
    ) = _getCollateral(_collateralAddress);
    //check for frozen or paused collateral
    _checkIfCollateralIsActive(currencyKey);

    uint256 isoUSDdebt = (isoUSDLoanAndInterest[_collateralAddress][msg.sender] * virtualPrice) / LOAN_SCALE;
    require( isoUSDdebt >= _USDToVault, "Trying to return more isoUSD than borrowed!");
    uint256 outstandingisoUSD = isoUSDdebt - _USDToVault;

    uint256 collateral = collateralPosted[_collateralAddress][msg.sender];
    uint256 colInUSD = priceCollateralToUSD(currencyKey, collateral); 
    uint256 borrowMargin = (outstandingisoUSD * liquidatableMargin) / LOAN_SCALE;
    require(colInUSD > borrowMargin , "Liquidation margin not met!");
    
    //record paying off loan principle before interest
    //slither-disable-next-line uninitialized-local-variables
    uint256 interestPaid;
    uint256 loanPrinciple = isoUSDLoaned[_collateralAddress][msg.sender];
    if( loanPrinciple >= _USDToVault){
        //pay off loan principle first
        isoUSDLoaned[_collateralAddress][msg.sender] = loanPrinciple - _USDToVault;
    }
    else{
        interestPaid = _USDToVault - loanPrinciple;
        //loan principle is fully repaid so record this.
        isoUSDLoaned[_collateralAddress][msg.sender] = 0;
    }
    //update mappings with reduced amounts
    isoUSDLoanAndInterest[_collateralAddress][msg.sender] = isoUSDLoanAndInterest[_collateralAddress][msg.sender] - ((_USDToVault * LOAN_SCALE) / virtualPrice);
    emit ClosedLoan(msg.sender, _USDToVault, currencyKey, 0);
    //Now all effects are handled, transfer the assets so we follow CEI pattern
    _decreaseLoan(_collateralAddress, 0, _USDToVault, interestPaid);
}
```

### Discussion

**kree-dotcom**

Sponsor confirmed. This is a difficult fix, it is highly likely that adding an extra function to Vault_Lyra and Vault_Velo will lead to "code too big" errors preventing them compiling, we will have to consult with 0x52/Sherlock to see what else can be done to fix this.

**kree-dotcom**

Proposing to change the `closeLoan()` check to

`if((outstandingisoUSD > 0) && (_collateralToUser > 0)){ //leftover debt must meet minOpeningMargin if requesting collateral back` `uint256 collateralLeft = ...` `...` `}`

This way checks are only triggered if the user is repaying some of their loan and requesting capital back. This allows us to prevent people from opening loans with a lower than minOpeningMargin but allows them to reduce their loan without needing to match the minOpeningMargin.

**kree-dotcom**

Note `Vault_Velo` has to use a slightly different method because we are handling NFTs instead of ERC20s. I have checked the `_calculateProposedReturnedCapital()` function we are relying on will also work fine if given an array of non-owned NFTs (i.e. the user is not receiving any collateral back just reducing their loan) by returning 0.
### Notes

#### Impressions

*Excessive Constraint Propagation*

The protocol implemented a safety check (minimum margin requirement) that makes sense when withdrawing collateral, but incorrectly applied this same constraint to all debt repayment scenarios. This prevents users from taking risk-reducing actions (paying down debt) unless they can meet an unnecessarily high threshold.

### Tools
### Refine

- [[1-Business_Logic]]

---
## [H-02]  The calculation of `totalUSDborrowed` in `openLoan()` is not correct
----
- **Tags**: #business_logic #Double-check_the_complex_calculation #loan_with_interest 
- Number of finders: 8
- Difficulty: Medium
---
The `openLoan()` function wrongly use `isoUSDLoaned` to calculate `totalUSDborrowed`. Attacker can exploit it to bypass security check and loan isoUSD with no enough collateral.
### Detail

vulnerability point

```solidity
function openLoan(
    // ...
    ) external override whenNotPaused 
    {
    //...
    uint256 colInUSD = priceCollateralToUSD(currencyKey, _colAmount
                        + collateralPosted[_collateralAddress][msg.sender]);
    uint256 totalUSDborrowed = _USDborrowed 
        +  (isoUSDLoaned[_collateralAddress][msg.sender] * virtualPrice)/LOAN_SCALE;
        // @audit should be isoUSDLoanAndInterest[_collateralAddress][msg.sender]
    require(totalUSDborrowed >= ONE_HUNDRED_DOLLARS, "Loan Requested too small");
    uint256 borrowMargin = (totalUSDborrowed * minOpeningMargin) / LOAN_SCALE;
    require(colInUSD >= borrowMargin, "Minimum margin not met!");

    // ...
}
```

Attack example: 
1. Attacker normally loans and produces `10000` isoUSD interest.
2. Attacker repays principle but left interest.
3. Attacker open a new `10000` isoUSD loan without providing collateral.
### Impact

Attacker can loan isoUSD with no enough collateral.

### Recommended Mitigation

```solidity
function openLoan(
    // ...
    ) external override whenNotPaused 
    {
    //...
    uint256 colInUSD = priceCollateralToUSD(currencyKey, _colAmount
                        + collateralPosted[_collateralAddress][msg.sender]);
-   uint256 totalUSDborrowed = _USDborrowed + (isoUSDLoaned[_collateralAddress][msg.sender] * virtualPrice)/LOAN_SCALE;
+   uint256 totalUSDborrowed = _USDborrowed + (isoUSDLoanAndInterest[_collateralAddress][msg.sender] * virtualPrice)/LOAN_SCALE;
    require(totalUSDborrowed >= ONE_HUNDRED_DOLLARS, "Loan Requested too small");
    uint256 borrowMargin = (totalUSDborrowed * minOpeningMargin) / LOAN_SCALE;
    require(colInUSD >= borrowMargin, "Minimum margin not met!");

    // ...
}
```

### Discussion

### Notes

#### Notes 
- `isoUSDLoaned` - Appears to track only the principal amount of the loan
- `isoUSDLoanAndInterest` - Tracks both the principal and accumulated interest
- Total debt = loan + interest
#### Impressions
1. #Double-check_the_complex_calculation

### Tools
### Refine

- [[1-Business_Logic]]

---
## [H-07] User can steal rewards from other users by withdrawing their Velo Deposit NFTs from other users' depositors
----
- **Tags**: #business_logic #access_control #withdraw_from_gauge #gauge #deposit_receipt
- Number of finders: 2
- Difficulty: Hard
---
### Summary

Rewards from staking AMM tokens accumulate to the depositor used to deposit them. The rewards accumulated by a depositor are passed to the owner when they claim. A malicious user to steal the rewards from other users by manipulating other users depositors. Since any NFT of a `DepositReceipt` can be withdrawn from any depositor with the same `DepositReceipt`, a malicious user could mint an NFT on their depositor then withdraw in from another user's depositor. The net effect is that that the victims deposits will effectively be in the attackers depositor and they will collect all the rewards.
### Detail

```solidity
function withdrawFromGauge(uint256 _NFTId, address[] memory _tokens)  public  {
    uint256 amount = depositReceipt.pooledTokens(_NFTId);
    depositReceipt.burn(_NFTId);
    gauge.getReward(address(this), _tokens);
    gauge.withdraw(amount);
    //AMMToken adheres to ERC20 spec meaning it reverts on failure, no need to check return
    //slither-disable-next-line unchecked-transfer
    AMMToken.transfer(msg.sender, amount);
}
```

Every user must create a `Depositor` using `Templater` to interact with vaults and take loans. `Depositor#withdrawFromGauge` allows any user to withdraw any NFT that was minted by the same `DepositReciept`. This is where the issues arises. Since rewards are accumulated to the `Depositor` in which the underlying is staked a user can deposit to their `Depositor` then withdraw their NFT through the `Depositor` of another user's `Depositor` that uses the same `DepositReciept`. The effect is that the tokens will remained staked to the attackers `Depositor` allowing them to steal all the other user's rewards.

Example: `User A` and `User B` both create a `Depositor` for the same `DepositReciept`. Both users deposit 100 tokens into their respective `Depositors`. `User B` now calls `withdrawFromGauge` on `Depositor A`. `User B` gets their 100 tokens back and `Depositor B` still has 100 tokens deposited in it. `User B` cannot steal these tokens but they are now collecting the yield on all 100 tokens via `Depositor B` and `User A` isn't getting any rewards at all because `Depositor A` no longer has any tokens deposited into Velodrome gauge.
### Impact

Malicious user can steal other user's rewards
### Recommended Mitigation

Depositors should only be able to burn NFTs that they minted. Change `DepositReciept_Base#burn` to enforce this:

```solidity
    function burn(uint256 _NFTId) external onlyMinter{
+       //tokens must be burned by the depositor that minted them
+       address depositor = relatedDepositor[_NFTId];
+       require(depositor == msg.sender, "Wrong depositor");
        require(_isApprovedOrOwner(msg.sender, _NFTId), "ERC721: caller is not token owner or approved");
        delete pooledTokens[_NFTId];
        delete relatedDepositor[_NFTId];
        _burn(_NFTId);
    }
```

### Discussion

### Notes

#### Notes 
- **Depositors**: Personal contracts users create to interact with vaults and take loans
- **DepositReceipt**: An NFT contract that represents staked AMM tokens
- **Gauge**: A contract that distributes rewards for staked tokens
- User A and User B both create Depositors for the same DepositReceipt(with the same DepositReceipt contract)

#### Impressions
- Check `DepositReceipt`  same?
- Missing authentication checks

### Tools
### Refine
- [[1-Business_Logic]]
- [[14-Accrss_Control]]

---
## [H-09] Swapping 100 tokens in `DepositReceipt_ETH` and `DepositReciept_USDC` breaks usage of `WBTC LP` and other high value tokens
----
- **Tags**: #business_logic #decimals
- Number of finders: 2
- Difficulty: Hard
---
### Summary

`DepositReceipt_ETH` and `DepositReciept_USDC` checks the value of liquidity by swapping 100 tokens through the swap router. `WBTC` is a good example of a token that will likely never work as LP due to the massive value of swapping 100 `WBTC`. This makes `DepositReceipt_ETH` and `DepositReciept_USDC` revert during slippage checks after calculating amount out. As of the time of writing this, `WETH` also experiences a 11% slippage when trading 100 tokens. Since `DepositReceipt_ETH` only supports 18 decimal tokens, `WETH`/`USDC` would have to use `DepositReciept_USDC`, resulting in `WETH/USDC` being incompatible. The fluctuating liquidity could also make this a big issue as well. If liquidity reduces after deposits are made, user deposits could be permanently trapped.
### Detail

```solidity
    //check swap value of 100tokens to USDC to protect against flash loan attacks
    uint256 amountOut; //amount received by trade
    bool stablePool; //if the traded pool is stable or volatile.
    (amountOut, stablePool) = router.getAmountOut(HUNDRED_TOKENS, token1, USDC);
```

The above lines try to swap 100 tokens from token1 to `USDC`. In the case of `WBTC` 100 tokens is a monstrous amount to swap. Given the low liquidity on the network, it simply won't function due to slippage requirements.

```solidity
function _priceCollateral(IDepositReceipt depositReceipt, uint256 _NFTId) internal view returns(uint256){  
    uint256 pooledTokens = depositReceipt.pooledTokens(_NFTId);      
    return( depositReceipt.priceLiquidity(pooledTokens));
}

function totalCollateralValue(address _collateralAddress, address _owner) public view returns(uint256){
    NFTids memory userNFTs = loanNFTids[_collateralAddress][_owner];
    IDepositReceipt depositReceipt = IDepositReceipt(_collateralAddress);
    //slither-disable-next-line uninitialized-local-variables
    uint256 totalPooledTokens;
    for(uint256 i =0; i < NFT_LIMIT; i++){
        //check if each slot contains an NFT
        if (userNFTs.ids[i] != 0){
            totalPooledTokens += depositReceipt.pooledTokens(userNFTs.ids[i]);
        }
    }
    return(depositReceipt.priceLiquidity(totalPooledTokens));
}
```

One of the two functions above are used to price `LP` for every vault action on `Vault_Velo`. If liquidity is sufficient when user deposits but then drys up after, the users deposit would be permanently trapped in the in the vault. In addition to this liquidation would also become impossible causing the protocol to assume bad debt.

This could also be exploited by a malicious user. First they deposit a large amount of collateral into the Velodrome `WBTC/USDC` pair. They take a portion of their LP and take a loan against it. Now they withdraw the rest of their LP. Since there is no longer enough liquidity to swap 100 tokens with 5% slippage, they are now safe from liquidation, allowing a risk free loan.
### Impact

LPs that contain high value tokens will be unusable at best and freeze user funds or be abused at the worst case
### Recommended Mitigation

Change the number of tokens to an immutable, so that it can be set individually for each token. Optionally you can add checks (shown below) to make sure that the number of tokens being swapped will result in at least some minimum value of `USDC` is received. Similar changes should be made for `DepositReceipt_ETH`:

```solidity
constructor(string memory _name, 
            string memory _symbol, 
            address _router, 
            address _token0,
            address _token1,
            uint256 _tokensToSwap,
            bool _stable,
            address _priceFeed) 
            ERC721(_name, _symbol){

    ...

    if (keccak256(token0Symbol) == keccak256(USDCSymbol)){
        require( IERC20Metadata(_token1).decimals() == 18, "Token does not have 18dp");

+       (amountOut,) = _router.getAmountOut(_tokensToSwap, token1, USDC);

+       //swapping tokens must yield at least 100 USDC
+       require( amountOut >= 1e8);
+       tokensToSwap = _tokensToSwap;
    }
    else
    {   
        bytes memory token1Symbol = abi.encodePacked(IERC20Metadata(_token1).symbol());
        require( keccak256(token1Symbol) == keccak256(USDCSymbol), "One token must be USDC");
        require( IERC20Metadata(_token0).decimals() == 18, "Token does not have 18dp");
        
+       (amountOut, ) = _router.getAmountOut(_tokensToSwap, token0, USDC);

+       //swapping tokens must yield at least 100 USDC
+       require( amountOut >= 1e8);
+       tokensToSwap = _tokensToSwap;
    }
```

### Discussion

### Notes

**Dynamic vs. Fixed Parameters:**  
Always question whether a fixed parameter (like a set number of tokens or a fixed value threshold) is appropriate across all contexts. Consider if the value, decimals, or liquidity characteristics of different tokens might require dynamic or configurable parameters.

### Tools
### Refine
- [[1-Business_Logic]]

---
# Medium Risk Findings (xx)

---
## [M-05]  `increaseCollateralAmount` : User is not allowed to increase collateral freely.
----
- **Tags**: #business_logic #liquidation #Excessive_Constraint_Propagation 
- Number of finders: 3
- Difficulty: Medium
---
### Summary

For all the tree type of vault, a user is allowed to increase collateral only if the overall collateral value is higher than the margin value.

imo, this restriction may not be needed. anyway user is adding the collateral that could eventually save from liquidation.

Protocol will loose advantage due to this restriction.
### Detail

Codes from lyra (synth, velo) vault implementation :


```
        //debatable check begins here 
        uint256 totalCollat = collateralPosted[_collateralAddress][msg.sender] + _colAmount;
        uint256 colInUSD = priceCollateralToUSD(currencyKey, totalCollat);
        uint256 USDborrowed = (isoUSDLoanAndInterest[_collateralAddress][msg.sender] * virtualPrice) / LOAN_SCALE;
        uint256 borrowMargin = (USDborrowed * liquidatableMargin) / LOAN_SCALE;
        require(colInUSD >= borrowMargin, "Liquidation margin not met!");
        //debatable check ends here
```
### Impact

User may not have the collateral all at once, but they can add like an EMI.

Protocol will loose the repayment anyway.

What is no one comes for liquidation - again this could lose.

### Recommended Mitigation

Allow user add collateral freely. Delete `debatable check`

### Discussion

### Notes & Impressions

#### Impressions
#Excessive_Constraint_Propagation 
### Tools
### Refine

- [[1-Business_Logic]]
- [[21-Liquidation]]

---

---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}