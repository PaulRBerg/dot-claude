# TypeScript, React, and Node.js Patterns

## Type Safety

Avoid `any` by using `unknown` for truly unknown types, forcing explicit type narrowing before usage. Prefer generic constraints over type assertions—they provide compile-time safety rather than runtime assumptions. Use discriminated unions for state variants, enabling exhaustive pattern matching and eliminating impossible states.

Minimize type assertions (`as`). Prefer type guards that prove types at runtime. Double assertions (`as unknown as X`) signal architectural problems—redesign the types instead. Use the `satisfies` operator when you need type checking without widening the inferred type.

Enable strict mode. Set `strict: true` in tsconfig as a baseline. Add `noUncheckedIndexedAccess` to force null checks on array access, preventing out-of-bounds errors. Enable `exactOptionalPropertyTypes` to distinguish between `undefined` values and missing properties, making intent explicit and catching subtle bugs where presence matters.

## React Patterns

Respect exhaustive dependencies. Missing dependencies in hooks cause stale closures where callbacks reference outdated values. Add all referenced variables to dependency arrays.

Avoid derived state anti-patterns. Don't sync props to state—compute derived values directly during render. Choose the right state layer: lift state for sibling communication, use context for deep prop drilling, prefer external stores like Zustand or Jotai for global state that needs subscription batching.

Handle effects properly. Return cleanup functions for subscriptions, timers, and event listeners. Prevent race conditions in async effects by checking cancellation flags or using `AbortController` to cancel in-flight requests. The cleanup function runs before the next effect and on unmount.

NEVER suggest useMemo, useCallback, or React.memo. React 19's compiler handles all memoization automatically—do not recommend manual optimization under any circumstances. Extract constant object literals outside components to avoid unnecessary allocations, but let the compiler handle reference stability.

## Node.js Server

Avoid blocking the event loop. CPU-bound work blocks all concurrent requests since Node runs on a single thread. Offload heavy computation to worker threads. Never use synchronous I/O functions in request handlers—they freeze the entire process.

Respect stream backpressure. Check the boolean return value of `write()`—`false` means the buffer is full. Pause input streams until the `drain` event fires. Use `pipeline()` to chain streams correctly—it handles backpressure, errors, and cleanup automatically, preventing memory exhaustion and resource leaks.

Handle errors comprehensively. Unhandled promise rejections crash the process in Node 15+. Attach `.catch()` to all promises or use try-catch with async/await. Implement graceful shutdown on SIGTERM by closing servers, draining connections, and flushing logs before exit. Use `AsyncLocalStorage` for request-scoped error context without callback contamination.

## Common Bugs

Closures capture stale references. `setTimeout`, `setInterval`, and event handlers freeze variable values at creation time. React state in callbacks references the value from when the callback was created. Use `useRef` to hold mutable current values that persist across renders without triggering re-renders.

Race conditions corrupt state. Concurrent fetches can resolve out of order, overwriting newer data with stale responses. Implement request cancellation with `AbortController`. Version optimistic updates so out-of-order responses don't regress the UI. Track the latest request ID to ignore obsolete responses.

Memory leaks accumulate over time. Clear intervals and timeouts in cleanup functions. Remove event listeners when components unmount. Bound the size of caches implemented with `Map` or `Set`—add eviction policies or TTLs. Break circular references where closures capture objects that reference the closure.

Type narrowing doesn't persist across `await` boundaries. Checking a type before an async call doesn't guarantee the type after—the variable could be reassigned. Callbacks also reset narrowing since they execute later. Store narrowed values in `const` variables within the narrowed scope to preserve type information.
