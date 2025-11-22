---
name: web3-frontend
description: This skill should be used when the user asks to "build a dApp", "integrate wallet connection", "interact with smart contracts", "use Viem", "use Wagmi", or mentions web3, blockchain, EVM, Ethereum, or decentralized applications.
---

# Web3 Frontend Engineer

Apply these principles when building battle-tested EVM dApps that interact with smart contracts.

## Core Architecture Principles

- **Type Safety First**: Fully type every contract interaction. Avoid `any` types to prevent runtime surprises.
- **Defensive Programming**: Assume every RPC will fail, every wallet will disconnect, and every transaction will revert.
- **Gas Optimization**: Batch reads, minimize writes, and use multicall when sensible. Users pay for inefficiency.
- **Security Paranoia**: Validate addresses, sanitize inputs, and protect against reentrancy on the frontend.

## Tech Stack & Rationale

### Viem (NOT ethers.js)

Use Viem as the primary blockchain interface. Prefer it over ethers for:

- Type-safe contract interactions out of the box
- Better error messages that actually help debugging
- Smaller bundle size (~40% reduction)
- Built-in utilities that prevent common mistakes (checksummed addresses, unit conversions)

Apply these critical patterns:

- Use `publicClient` for reads, `walletClient` for writes
- Implement retry logic with exponential backoff for RPC calls
- Use `watchContractEvent` for real-time updates instead of polling

Documentation: https://viem.sh/llms.txt

### Wagmi

Use Wagmi for wallet connection and reactive blockchain state. Apply these key patterns:

- Use `usePrepareContractWrite` + `useContractWrite` for transaction UX
- Implement proper loading states: preparing, confirming, processing, success/error
- Cache aggressively with React Query integration
- Handle chain switching gracefully without breaking the UI

Documentation: https://wagmi.sh/react/getting-started

### React Query (via Wagmi)

- Set `staleTime` appropriately to avoid refetching block data every second
- Use optimistic updates for transaction states
- Implement proper error boundaries for failed queries

## Non-Negotiable Requirements

1. **Transaction Safety**

   - Implement slippage protection with user controls
   - Add transaction simulation when possible

2. **Error Handling**

   - Provide user-friendly error messages instead of "execution reverted"
   - Include actionable recovery steps
   - Implement fallback UI states for all error conditions

## Context7 Usage

Fetch latest documentation for libraries BEFORE implementation. The ecosystem moves fast - don't assume yesterday's patterns still apply.
