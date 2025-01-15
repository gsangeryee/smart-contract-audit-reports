# Truth Table

We should special attention should be given to situations where multiple conditions are connected with 'and' during the audit. We can use a truth table to analyze whether all conditions match the expected results.

Example:

```solidity
if (details.fee != uint24(0) && fee != details.fee)
```

Truth table analysis:

```solidity
details.fee    fee    Condition A    Condition B    Will Revert?   
------------------------------------------------------------------
0              0      FALSE          FALSE          NO             
0              0.3%   FALSE          TRUE           NO            
0              1%     FALSE          TRUE           NO             
0.3%           0      TRUE           TRUE           YES            
0.3%           0.3%   TRUE           FALSE          NO             
0.3%           1%     TRUE           TRUE           YES           
1%             0      TRUE           TRUE           YES            
1%             0.3%   TRUE           TRUE           YES          
1%             1%     TRUE           FALSE          NO            
```

