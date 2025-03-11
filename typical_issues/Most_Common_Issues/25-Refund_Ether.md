# Refund Ether

Refund Ether typically refers to a function in a smart contract that allows users to refund their Ether holdings from the contract.

In Ethereum and Solidity, when you call a function with ETH (using `{value: amount}`), that ETH is transferred directly to the contract being called. However, that ETH doesn't automatically "flow through" to any subsequent contract calls unless you explicitly forward it.

## Examples
- [[2022-11-stakehouse#[M-22] ETH sent when calling executeAsSmartWallet function can be lost]]