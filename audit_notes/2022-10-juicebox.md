# 2022-10-juicebox
---
- Category: #liquid_staking #Dexes #Bridge #CDP #yield 
- Note Create 2025-03-19
- Platform: code4rena
- Report Url: [2022-10-juicebox](https://code4rena.com/reports/2022-10-juicebox)
---
# Critical & High Risk Findings (xx)

---
## [H-01] Making a payment to the protocol with `_dontMint` parameter will result in lost fund for user.
----
- **Tags**: #Do_not_update_state #business_logic 
- Number of finders: 3
- Difficulty: Medium
---
User will have their funds lost if they tries to pay the protocol with `_dontMint = False`. A payment made with this parameter set should increase the `creditsOf[]` balance of user.

In `_processPayment()`, `creditsOf[_data.beneficiary]` is updated at the end if there are leftover funds. However, If `metadata` is provided and `_dontMint == true`, it immediately returns. 

```solidity
  function _processPayment(JBDidPayData calldata _data) internal override {
    // Keep a reference to the amount of credits the beneficiary already has.
    uint256 _credits = creditsOf[_data.beneficiary];
    ...
    if (
      _data.metadata.length > 36 &&
      bytes4(_data.metadata[32:36]) == type(IJB721Delegate).interfaceId
    ) {
      ...
      // Don't mint if not desired.
      if (_dontMint) return;
      ...
    }
    ...
    // If there are funds leftover, mint the best available with it.
    if (_leftoverAmount != 0) {
      _leftoverAmount = _mintBestAvailableTier(
        _leftoverAmount,
        _data.beneficiary,
        _expectMintFromExtraFunds
      );
      if (_leftoverAmount != 0) {
        // Make sure there are no leftover funds after minting if not expected.
        if (_dontOverspend) revert OVERSPENDING();
        // Increment the leftover amount.
        creditsOf[_data.beneficiary] = _leftoverAmount;
      } else if (_credits != 0) creditsOf[_data.beneficiary] = 0;
    } else if (_credits != 0) creditsOf[_data.beneficiary] = 0;
  }
```

### Proof of Concept

I've wrote a coded POC to illustrate this. It uses the same Foundry environment used by the project. Simply copy this function to `E2E.t.sol` to verify.

```solidity
  function testPaymentNotAddedToCreditsOf() public{
    address _user = address(bytes20(keccak256('user')));
    (
      JBDeployTiered721DelegateData memory NFTRewardDeployerData,
      JBLaunchProjectData memory launchProjectData
    ) = createData();
    uint256 projectId = deployer.launchProjectFor(
      _projectOwner,
      NFTRewardDeployerData,
      launchProjectData
    );
    // Get the dataSource
    IJBTiered721Delegate _delegate = IJBTiered721Delegate(
      _jbFundingCycleStore.currentOf(projectId).dataSource()
    );
    address NFTRewardDataSource = _jbFundingCycleStore.currentOf(projectId).dataSource();
    uint256 _creditBefore = IJBTiered721Delegate(NFTRewardDataSource).creditsOf(_user);
    // Project is initiated with 10 different tiers with contributionFee of 10,20,30,40, .... , 100
    // Make payment to mint 1 NFT
    uint256 _payAmount = 10;
    _jbETHPaymentTerminal.pay{value: _payAmount}(
      projectId,
      100,
      address(0),
      _user,
      0,
      false,
      'Take my money!',
      new bytes(0)
    );
    // Minted 1 NFT
    assertEq(IERC721(NFTRewardDataSource).balanceOf(_user), 1);
    // Now, we make the payment but supply _dontMint metadata
    bool _dontMint = true;
    uint16[] memory empty;
    _jbETHPaymentTerminal.pay{value: _payAmount}(
      projectId,
      100,
      address(0),
      _user,
      0,
      false,
      'Take my money!',
      //new bytes(0)
      abi.encode(
        bytes32(0),
        type(IJB721Delegate).interfaceId,
        _dontMint,
        false,
        false,
        empty
        )
    );
    // NFT not minted
    assertEq(IERC721(NFTRewardDataSource).balanceOf(_user), 1);
    // Check that credits of user is still the same as before even though we have made the payment
    assertEq(IJBTiered721Delegate(NFTRewardDataSource).creditsOf(_user),_creditBefore);
  }
```
### Recommended Mitigation

Update the `creditsOf[]` in the `if(_dontMint)` check.

```solidity
- if(_dontMint) return;
+ if(_dontMint){ creditsOf[_data.beneficiary] += _value; }
```
### Discussion

**mejango (Juicebox DAO) commented on duplicate issue #157:**

> mixed feels. `_dontMint` basically says "Save me gas at all costs.". I see the argument for value leaking being bad though. will mull over.

**drgorillamd (Juicebox DAO) commented on duplicate issue #157:**

> paying small amounts (under the floor or with `dontMint`) only to save them to later mint is a bit of a nonsense -> it's way cheaper to just not pay, save in an eoa then mint within the same tx.
> 
> I have the feeling the severity is based on seeing `_credit` as a saving account, while it's rather something to collect leftovers.
> 
> Anyway, we changed it, but not sure of high sev on this one, happy to see others' point of view.

**Picodes (judge) commented:**

> @drgorillamd @mejango I have to say that I don't see why someone would use the `dontMint` flag in the first place. Wasn't the original intent to use this flag specifically to modify `_credit` without minting? In the meantime I'll keep the High label for this one, the `dontMint` functionality being flawed and leading to a loss of funds.

**drgorillamd (Juicebox DAO) commented:**

> @Picodes `nftReward` is just an extension plugged into a Jb project -> `dontMint` is to avoid forcing users of the project who don't want a nft reward when contributing, i.e. "classic" use of a Jb project. The use case we had in mind was smaller payers, wanting to get the erc20 (or even just donating), without the gas burden of a nft reward (which might, on L1, sometimes be more than the contribution itself). Does that make sense?

**Picodes (judge) commented:**

> Definitely, thanks for the clarification @drgorillamd.

**Picodes (judge) commented:**

> The final decision for this issue was to keep the high severity because of the leak of value and the possibility that some users use the function thinking it will change `_credit`, despite the fact that it was not the original intent of the code.

**mejango (Juicebox DAO) commented:**

> We ended up adding credits even when `_dontMint` is true!!<br> It was a last minute design decision, initially we marked the issue as "Disagree with severity" and we were planning on keeping the code unchanged since it didn't pose a risk and was working as designed.<br> We ended up changing the design, but the wardens' feedback was ultimately helpful!
### Notes

#### How It Works in Code

The vulnerability exists in the `_processPayment()` function. Let's walk through the normal flow:

1. The function starts by storing the user's current credit balance
2. It processes the payment and potentially mints NFTs
3. If there are leftover funds after minting, it updates the user's credit balance

However, there's a critical early exit condition:

```solidity
if (_data.metadata.length > 36 &&
    bytes4(_data.metadata[32:36]) == type(IJB721Delegate).interfaceId) {
  // ... some code ...
  // Don't mint if not desired.
  if (_dontMint) return;  // <-- PROBLEM IS HERE
  // ... more code ...
}

```

When `_dontMint` is true, the function simply returns early without updating the user's credit balance. This means the user's payment is accepted, but they receive nothing in return – no NFTs and no credits.
#### Impressions
1. **Track State Changes vs. Inputs**: Always verify that every input value (like a payment) has a corresponding state change (like a balance update or token mint).
2. **Beware of Early Returns**: Early function returns can skip important code sections. Always check what state changes might be bypassed.
3. **Follow the Money**: For any function accepting value, trace exactly where that value goes in all possible execution paths.
4. **Check Flag Parameters**: Parameters that change behavior (like `_dontMint`) are common sources of bugs as they create branching logic.
5. **Look for Asymmetric Operations**: When a function has "debit" operations without corresponding "credit" operations, funds can disappear.
6. **Test Edge Cases**: The issue was found by specifically testing the `_dontMint` parameter, showing the importance of testing all configuration options.
7. **Understand Developer Intent**: The team comments reveal they viewed credits differently than users might, highlighting how mental models can create vulnerabilities.

### Tools
### Refine
- [[1-Business_Logic]]
- [[12-Do_not_Update_state]]

---

# Medium Risk Findings (xx)

---
## [M-05] NFT not minted when contributed via a supported payment terminal
----
- **Tags**: #business_logic 
- Number of finders: 2
- Difficulty: Medium
---
A contributor won't get an NFT they're eligible for if the payment is made through a payment terminal that's supported by the project but not by the NFT delegate.
### Proof of Concept

A Juicebox project can use multiple payment terminals to receive contributions. Payment terminals are single token payment terminals that support only one currency. Since projects can have multiple terminals, they can receive payments in multiple currencies.

However, the NFT delegate supports only one currency :

```solidity
function initialize(
  uint256 _projectId,
  IJBDirectory _directory,
  string memory _name,
  string memory _symbol,
  IJBFundingCycleStore _fundingCycleStore,
  string memory _baseUri,
  IJBTokenUriResolver _tokenUriResolver,
  string memory _contractUri,
  JB721PricingParams memory _pricing,
  IJBTiered721DelegateStore _store,
  JBTiered721Flags memory _flags
) public override {
  // Make the original un-initializable.
  require(address(this) != codeOrigin);
  // Stop re-initialization.
  require(address(store) == address(0));

  // Initialize the sub class.
  JB721Delegate._initialize(_projectId, _directory, _name, _symbol);

  fundingCycleStore = _fundingCycleStore;
  store = _store;
  pricingCurrency = _pricing.currency; // @audit only one currency is supported
  pricingDecimals = _pricing.decimals;
  prices = _pricing.prices;

  ...
}
```

When a payment is made in a currency that's supported by the project (via one of its terminals) but not by the NFT delegate, there's an attempt to convert the currency to a supported one ([JBTiered721Delegate.sol#L527-L534](https://github.com/jbx-protocol/juice-nft-rewards/blob/f9893b1497098241dd3a664956d8016ff0d0efd0/contracts/JBTiered721Delegate.sol#L527-L534)):

```solidity
if (_data.amount.currency == pricingCurrency) _value = _data.amount.value;
else if (prices != IJBPrices(address(0)))
  _value = PRBMath.mulDiv(
    _data.amount.value,
    10**pricingDecimals,
    prices.priceFor(_data.amount.currency, pricingCurrency, _data.amount.decimals)
  );
else return;
```

However, since `prices` is optional (it can be set to the zero address, as seen from the snippet), the conversion step can be skipped. When this happens, the contributor gets no NFT due to the early `return` even though the amount of their contribution might still be eligible for a tiered NFT.
### Recommended Mitigation

Short term, consider reverting when a different currency is used and `prices` is not set. Long term, consider supporting multiple currencies in the NFT delegate.
### Discussion

**drgorillamd (Juicebox DAO) disputed**

> This is poor project management from the project owner (not adding the appropriate price feed), not a vulnerability
> 
> And there is no revert here as to not freeze the Juicebox project (NFT reward is an add-on, there is a full project running behind)

**Picodes (judge) commented:**

> As this finding:
> - would lead to a leak of value
> - is conditional on the project owner's mistake (that seems not so unlikely as they may think that one currency is enough and that they don't need to set `prices`)
> - but ultimately lead to a loss of funds for users
> I believe Medium severity to be appropriate

### Notes & Impressions

#### Notes 
The core problem occurs because of a mismatch between two components of the system:

1. The main Juicebox project can accept multiple currencies through different payment terminals.
2. The NFT delegate (which handles minting reward NFTs) only supports a single currency defined during initialization.

Let's walk through a concrete example:

1. A Juicebox project is set up to accept both ETH and USDC contributions.
2. The NFT delegate for rewards is configured to only work with ETH (the `pricingCurrency`).
3. The project creator forgets to set up the `prices` variable, leaving it as the zero address.
4. A user contributes 500 USDC to the project, which would normally qualify them for a specific tier of NFT reward.
5. When the payment is processed:
    - The system detects that the payment currency (USDC) doesn't match the NFT delegate's currency (ETH).
    - It checks if `prices` is configured to convert USDC to ETH.
    - Finding `prices` is the zero address, it skips conversion and simply returns.
    - No NFT is minted for the user even though they made a valid contribution.
#### Impressions

**Currency/Type Mismatches**: Look for systems where one component accepts a broader range of input types than another interconnected component. These mismatches often lead to edge cases.

### Tools
### Refine
- [[1-Business_Logic]]
---
## [M-06] Beneficiary credit balance can unwillingly be used to mint low tier NFT
----
- **Tags**: #business_logic 
- Number of finders: 1
- Difficulty: Hard
---
In the function `_processPayment()`, it will use provided `JBDidPayData` from `JBPaymentTerminal` to mint to the beneficiary. The `_value` from `JBDidPayData` will be sum up with previous `_credits` balance of beneficiary. There are 2 cases that beneficiary credit balance is updated in previous payment:

1. The payment received does not meet a minting threshold or is in excess of the minted tiers, the leftover amount will be stored as credit for future minting.
2. Clients may want to accumulate to mint higher tier NFT, they might specify that the previous payment should not mint anything. (Currently it's incorrectly implemented in case `_dontMint=true`, but sponsor confirmed that it's a bug)

In both cases, an attacker can pay a small amount (just enough to mint lowest tier NFT) and specify the victim to be the beneficiary. Function `__processPayment()` will use credit balance of beneficiary from previous payment to mint low-value tier.

For example, there are 2 tiers

1. Tier A: mintingThreshold = 20 ETH, votingUnits = 100
2. Tier B: mintingThreshold = 10 ETH, votingUnits = 10

Obviously tier A is much more better than tier B in term of voting power, so Alice (the victim) might want to accumulate her credit to mint tier A.

Assume current credit balance `creditsOf[Alice] = 19 ETH`. Now Bob (the attacker) can pay `1 ETH` and specify Alice as beneficiary and mint `2` Tier B NFT. Alice will have to receive `2` Tier B NFT with just `20 voting power` instead of `100 voting power` for a Tier A NFT.

Since these NFTs can be used in a governance system, it may create much higher impact if this governance is used to make important decision. E.g: minting new tokens, transfering funds of community.
### Proof of Concept

Function `didPay()` only check that the caller is a terminal of the project

```solidity
function didPay(JBDidPayData calldata _data) external payable virtual override {
    // Make sure the caller is a terminal of the project, and the call is being made on behalf of an interaction with the correct project.
    if (
      msg.value != 0 ||
      !directory.isTerminalOf(projectId, IJBPaymentTerminal(msg.sender)) ||
      _data.projectId != projectId
    ) revert INVALID_PAYMENT_EVENT();

    // Process the payment.
    _processPayment(_data);
}
```

Attacker can specify any beneficiary and use previous credit balance

```solidity
// Keep a reference to the amount of credits the beneficiary already has.
uint256 _credits = creditsOf[_data.beneficiary];

// Set the leftover amount as the initial value, including any credits the beneficiary might already have.
uint256 _leftoverAmount = _value + _credits;
```
### Recommended Mitigation

Consider adding a config param to allow others from using beneficiary's credit balance. Its value can be default to `false` for every address. And if beneficiary want to, they can toggle this state for their address to allow other using their credit balance.
### Discussion

**mejango (Juicebox DAO) acknowledged**

> fancy. i think accumulating credits to "save up" is out of scope for this contract's design. Still a pretty cool pattern to note, thank you!

> yeah: if you are saving up for a specific nft, save up elsewhere, not through the credit system.

**minhquanym (warden) commented:**

> Thanks for your comments. Just put a note cause my writing might be vague. Saving up is just 1 case that I listed. The other case, funds are left after minting a specific tier in the docs.
> 
> > If a payment received does not meet a minting threshold or is in excess of the minted tiers, the balance is stored as a credit which will be added to future payments and applied to mints at that time.

### Notes & Impressions

#### Example Scenario

Let's walk through an example to understand this better:
##### Setup
- Tier A NFT: Costs 20 ETH, grants 100 voting units
- Tier B NFT: Costs 10 ETH, grants 10 voting units
##### Victim's Situation

Alice wants a Tier A NFT for its superior voting power. She has already accumulated 19 ETH in credits in the system (perhaps from previous payments that weren't enough to mint anything yet).
##### Attack

Bob notices Alice's credit balance and decides to attack:
1. Bob sends just 1 ETH to the contract
2. Bob specifies Alice as the beneficiary
3. The contract processes the payment by:
    - Looking up Alice's credit balance: 19 ETH
    - Adding Bob's payment: 19 ETH + 1 ETH = 20 ETH
    - Determining what can be minted with 20 ETH
    - Deciding to mint 2 Tier B NFTs (10 ETH each) for Alice
##### Result
- Alice receives 2 Tier B NFTs with a total of 20 voting power
- Alice loses the opportunity to get 1 Tier A NFT with 100 voting power
- Alice's accumulated credits are spent without her consent
- The governance system is potentially compromised if many users are affected this wa

#### Impressions
- Missing Ownership Controls

### Tools
### Refine

- [[1-Business_Logic]]

---
---

## Audit Summary Notes
- {{summary_notes}}

## Tags
- Category: {{tags_category}}
- Priority:{{tags_priority}}