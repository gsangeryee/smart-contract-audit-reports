# Bypass Limit

Bypass limit refers to a scenario where a smart contract or function lacks proper checks and allows users to exceed predefined limits or constraints.

## **User-Controlled Address Inputs**

- Any function accepting tokens or addresses as user input
- Approval mechanisms with externally provided parameters
### Examples:
- [[2022-10-lifi#[M-12] Facets approve arbitrary addresses for ERC20 tokens]]

## Bypass the frontend (API)

If a developer interacts with the bridge contracts directly—bypassing the frontend—they can use the bridge without paying any fees.

### Examples
- [[2022-10-lifi#[M-13] `FeeCollector` not well integrated|[M-13] `FeeCollector` not well integrated]]

