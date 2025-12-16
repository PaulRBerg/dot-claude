# Smart Contract Security Patterns

## Solidity Patterns

### Reentrancy

Guard against reentrancy in all state-changing functions that make external calls. Single-function reentrancy occurs when an attacker re-enters the same function before state updates complete. Cross-function reentrancy exploits interactions between multiple functions sharing state. Cross-contract reentrancy leverages calls to other contracts that callback into the original contract.

Apply the Checks-Effects-Interactions pattern: validate inputs first, update state second, interact with external contracts last. This ordering ensures state reflects the operation before any external code executes. Use OpenZeppelin's ReentrancyGuard for automatic protection via the `nonReentrant` modifier, which sets a lock before execution and releases it afterward.

Watch for read-only reentrancy where view functions read inconsistent state during a reentrant call. Even though no state changes occur, returning stale data can enable exploits in dependent protocols. Protect critical view functions or ensure callers handle potential inconsistency.

### Access Control

Implement Ownable for simple single-owner scenarios with ownership transfer capability. Always include ownership transfer to prevent permanent lock-out. Use AccessControl for role-based permissions where multiple parties need different privilege levels. Define granular roles like MINTER_ROLE, PAUSER_ROLE, DEFAULT_ADMIN_ROLE and assign them explicitly.

Require multi-signature approval for critical operations like upgrades, parameter changes, or emergency withdrawals. Single points of failure create unacceptable risk in high-value contracts. Validate that ownership mechanisms include transfer or renunciation—contracts with `onlyOwner` but no transfer function trap control permanently.

### Integer Handling

Solidity 0.8+ includes built-in overflow and underflow protection that reverts on arithmetic errors. This eliminates the need for SafeMath libraries in modern contracts. Exercise caution with `unchecked` blocks used to optimize gas—manually validate that operations cannot overflow or underflow within the unchecked scope.

Remember division truncates toward zero, discarding remainders. For precision-sensitive calculations, multiply before dividing or scale values to fixed-point representations. Rounding errors accumulate in iterative calculations, potentially causing significant drift.

### External Calls

Low-level `.call()` returns a tuple `(bool success, bytes memory data)`. Always check the success boolean—failed calls return false without reverting. Decode the data bytes only after confirming success to avoid misinterpreting error data as valid returns.

Be aware of gas stipends when transferring ETH. `.transfer()` and `.send()` forward only 2300 gas, insufficient for contracts with fallback logic. Use `.call{value: amount}("")` and check the return value instead. Consider recipient reentrancy when using higher gas limits.

### Gas Optimization

Optimize gas without sacrificing security or readability. Use custom errors instead of require strings—they cost significantly less gas and support parameters for debugging. In loops, prefer `++i` over `i++` to avoid creating a temporary variable, though compilers often optimize this difference away.

Pack related variables into single storage slots by ordering struct fields from smallest to largest type. A struct with uint128, uint128, and address fits in two slots instead of three. Balance optimization against code clarity—premature optimization creates maintenance burden.

## Solana Patterns

### Account Validation

Validate account ownership before processing instructions. Check that the account owner matches the expected program ID to prevent accounts from malicious programs masquerading as valid data. Confirm required accounts have signed the transaction using the `is_signer` flag—missing signer checks allow unauthorized operations.

Deserialize account data and validate the discriminator (type identifier) matches expectations. Type confusion vulnerabilities arise when programs trust unverified account data. Implement runtime checks that reject unexpected account types early in instruction processing.

### PDA Derivation

Derive Program Derived Addresses deterministically using consistent seeds. PDAs enable programs to sign CPIs without exposing private keys. Use canonical bumps (the highest valid bump seed) to prevent multiple PDAs from the same seeds. Store bumps in account data or recompute them—recomputation costs more compute units but eliminates storage.

Validate PDA derivation in instructions that accept PDAs. Attackers may supply valid PDAs with incorrect seeds, bypassing intended constraints. Re-derive the PDA from expected seeds and compare against the provided address.

### Authority Patterns

Implement program-derived authorities for CPIs requiring signatures. PDAs allow programs to act as signers without private keys. Secure update authority carefully—it controls program upgrades and data modifications. Evaluate freeze authority implications when creating token accounts—frozen accounts block all transfers.

Store authorities in account data rather than hardcoding them. This flexibility enables authority rotation without redeployment. Validate authority accounts sign transactions that modify protected state.

### Rent Exemption

Ensure accounts maintain minimum lamports for rent exemption based on data size. Underfunded accounts get deleted by the runtime during rent collection. Close unused accounts to recover rent lamports—the SOL returns to the specified destination account.

Account resizing requires additional rent for expanded storage. Calculate new rent requirements and fund the account before resizing. Shrinking accounts does not automatically refund rent—explicitly reclaim it.

### Compute Units

Instructions receive 200,000 compute units by default. Request higher limits using `ComputeBudgetInstruction::set_compute_unit_limit` for complex operations. Monitor compute usage in tests with transaction simulation to prevent runtime failures from exhaustion.

Optimize hot paths to reduce compute costs. Avoid redundant deserialization, minimize allocations, and leverage zero-copy deserialization for large accounts. Log compute usage during development to identify optimization opportunities.

## Economic Security

### Flash Loan Attacks

Flash loans enable undercollateralized borrowing within a single transaction. Attackers leverage enormous temporary capital to manipulate governance votes based on token holdings, distort oracle prices through market impact, or drain AMM liquidity via price manipulation.

Defend governance by requiring token locks or vote delegation periods that exceed single-transaction durations. Use time-weighted average prices (TWAP) instead of spot prices for oracles. Implement circuit breakers that halt operations when price movements exceed reasonable thresholds.

### Oracle Manipulation

TWAP oracles resist manipulation better than spot price oracles by averaging prices over time windows. Chainlink provides decentralized price feeds with aggregation across multiple data sources. Uniswap V3 oracles offer built-in TWAP but require sufficient liquidity for reliability.

Deploy circuit breakers that pause or limit operations when prices deviate beyond expected ranges. Sanity check oracle outputs against multiple sources. Consider staleness—reject prices older than acceptable thresholds to prevent using outdated data.

### MEV and Frontrunning

Maximal Extractable Value (MEV) arises when block producers reorder, insert, or censor transactions for profit. Frontrunning places transactions ahead of pending transactions to exploit known future state changes. Commit-reveal schemes split operations into commitment and revelation phases, hiding transaction details until commitments finalize.

Use private mempools like Flashbots to submit transactions directly to block builders, bypassing the public mempool. Implement slippage protection with minimum output amounts and transaction deadlines to bound acceptable price movement.

### Sandwich Attacks

Sandwich attacks surround victim transactions with buy and sell orders that profit from induced price impact. The attacker front-runs with a buy, lets the victim trade at a worse price, then back-runs with a sell. Users lose value to the attacker's spread.

Require deadline parameters that bound transaction validity windows—stale transactions abort rather than execute at unfavorable prices. Enforce minimum output amounts to prevent execution when price impact exceeds tolerance. Educate users to set appropriate slippage limits.

## Upgrade Safety

### Proxy Patterns

Transparent proxies separate admin calls from user calls to different implementations. Admins interact with the proxy itself while users get delegated to the implementation. UUPS (Universal Upgradeable Proxy Standard) places upgrade logic in the implementation, reducing proxy complexity and gas costs.

Prevent storage collisions by maintaining consistent storage layouts between implementations. Use ERC-1967 standard storage slots for proxy metadata. Ensure implementations cannot be directly initialized—disable initializers to prevent takeover of implementation contracts.

### Storage Layout

Append new variables only—never reorder, remove, or change types of existing storage variables in upgrades. Reordering shifts storage slots, causing data corruption when the new implementation reads old storage. Include gap variables (arrays like `uint256[50] __gap`) in base contracts to reserve slots for future additions without shifting derived contract storage.

Document storage layout explicitly. Use tools like OpenZeppelin's storage layout checker to validate compatibility between versions. Test upgrades against production-like state to detect incompatibilities before deployment.

### Initialization

Use the `initializer` modifier from OpenZeppelin's Initializable contract to ensure initialization runs exactly once. Disable initializers in implementation contracts with `_disableInitializers()` in the constructor—this prevents direct initialization of the implementation separate from the proxy.

Implement reinitializers for version bumps that need state migration. Reinitializers allow running initialization logic again with version guards. Track initialization state carefully to prevent reinitialization vulnerabilities that reset critical state.
