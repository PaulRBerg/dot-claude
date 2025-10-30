---
name: web3-frontend
description: Expert frontend web3 engineering for secure wallet interactions and production-grade dApps. Use when working with web3, blockchain, EVM, Ethereum, smart contracts, Viem, Wagmi, wallet connections, or building decentralized applications (dApps).
---

# Web3 Frontend Engineer

Apply these principles when building battle-tested EVM dApps that interact with smart contracts.

## Core Architecture Principles

- **Type Safety First**: Every contract interaction must be fully typed. No `any` types, no runtime surprises.
- **Defensive Programming**: Assume every RPC will fail, every wallet will disconnect, and every transaction will revert.
- **Gas Optimization**: Users pay for your inefficiency. Batch reads, minimize writes, use multicall when sensible.
- **Security Paranoia**: Validate addresses, sanitize inputs, protect against reentrancy on the frontend.

## Tech Stack & Rationale

### Viem (NOT ethers.js)

Primary blockchain interface. Superior to ethers because:

- Type-safe contract interactions out of the box
- Better error messages that actually help debugging
- Smaller bundle size (~40% reduction)
- Built-in utilities prevent common mistakes (checksummed addresses, unit conversions)

Critical patterns:

- Always use `publicClient` for reads, `walletClient` for writes
- Implement retry logic with exponential backoff for RPC calls
- Use `watchContractEvent` for real-time updates, not polling

Documentation: https://viem.sh/llms.txt

### Wagmi

Wallet connection and reactive blockchain state. Key patterns:

- Use `usePrepareContractWrite` + `useContractWrite` for transaction UX
- Implement proper loading states: preparing, confirming, processing, success/error
- Cache aggressively with React Query integration
- Handle chain switching gracefully - don't break the UI

Documentation: https://wagmi.sh/react/getting-started

### React Query (via Wagmi)

- Set `staleTime` appropriately - block data shouldn't refetch every second
- Use optimistic updates for transaction states
- Implement proper error boundaries for failed queries

## Non-Negotiable Requirements

1. **Transaction Safety**

   - Implement slippage protection with user controls
   - Add transaction simulation when possible

2. **Error Handling**

   - User-friendly error messages (not "execution reverted")
   - Actionable recovery steps
   - Fallback UI states for all error conditions

## Context7 Usage

Fetch latest documentation for libraries BEFORE implementation. The ecosystem moves fast - don't assume yesterday's patterns still apply.
