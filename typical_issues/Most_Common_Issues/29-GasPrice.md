## minGasPrice
- The protocol would define a minimum acceptable gas price for transactions
- If a user sets a `gasPrice` below this threshold, the transaction would be rejected upfront
- Operators would never be forced to choose between executing unprofitable transactions or being locked out
### Examples
- [[2022-10-holograph#[H-02] If user sets a low `gasPrice` the operator would have to choose between being locked out of the pod or executing the job anyway|[H-02] If user sets a low `gasPrice` the operator would have to choose between being locked out of the pod or executing the job anyway]]
	- Set `minGasPrice`

## Gas Spike

### Examples
- [[2022-10-holograph#[M-03] Beaming job might freeze on dest chain under some conditions, leading to owner losing (temporarily) access to token|[M-03] Beaming job might freeze on dest chain under some conditions, leading to owner losing (temporarily) access to token]]
	1. #gas_spike 