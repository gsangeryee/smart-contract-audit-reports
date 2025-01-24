# Configuration

Configuration vulnerabilities arise from improper configuration of a smart contract which, despite having correct code, leads to unintended behavior. This is common in cases where financial parameters or market settings are misconfigured.
## Example:
1. [[2023-01-cooler#[H-02] Loans can be rolled an unlimited number of times|[H-02] Loans can be rolled an unlimited number of times]]
	1. Even if a lender allows rolling, there's no cap on the number of times a borrower can roll the loan. This could lead to indefinite extensions, especially problematic with depreciating collateral.
2. [[2023-01-cooler#[H-03] Fully repaying a loan will result in debt payment being lost|[H-03] Fully repaying a loan will result in debt payment being lost]]