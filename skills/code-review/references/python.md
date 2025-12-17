# Python Code Review Reference

## Type Hints

Use `from __future__ import annotations` at module top to enable forward references and postpone evaluation. Prefer `TypeVar` for generics over `Any`—`Any` disables type checking entirely. For structural typing, use Protocols instead of abstract base classes; Protocols support duck typing without inheritance.

Avoid `Any` by using `object` for truly unknown types that need no operations. Use `TypeGuard` for runtime type narrowing in validation functions. When functions return different types based on arguments, define overloads with `@overload` decorator to preserve type information.

Run Pyright in strict mode during development—it catches more errors than mypy's default configuration. Configure mypy with `--strict` flag for production code. For runtime validation, integrate Pydantic models; they enforce types at runtime and catch serialization bugs early.

## Common Bugs

Mutable default arguments share state across function calls. `def foo(items=[])` creates one list reused by all invocations. Always use `None` as default, then initialize inside: `def foo(items=None): items = items or []`.

Late binding in closures captures variable references, not values. `[lambda: x for x in range(3)]` creates three lambdas all returning 2. Fix with default argument to bind immediately: `[lambda x=x: x for x in range(3)]`.

Generators and iterators exhaust after one pass. Calling `list(gen)` twice yields one full list, then empty. Materialize with `list()` if multiple iterations needed, or use `itertools.tee()` to create independent iterators.

Name shadowing overwrites built-ins silently. Never assign to `list`, `dict`, `id`, `type`, `input`, `str`. Module imports can shadow locals—watch for variable names matching imported modules.

Use `is` only for singleton comparisons: `None`, `True`, `False`. Never use `is` for numbers or strings. Python caches small integers (-5 to 256), making `is` work accidentally but fail unpredictably. Always use `==` for value comparison.

## Async Patterns

Blocking calls freeze the entire event loop. Never call `time.sleep()`, `requests.get()`, or blocking I/O in async functions. Use `loop.run_in_executor()` to offload synchronous I/O to thread pool. Understand `asyncio.gather()` fails fast on first exception while `asyncio.wait()` waits for all tasks regardless.

Cleanup resources with `async with` for async context managers. Handle task cancellation by catching `CancelledError`—cleanup must happen in finally blocks. Use `asyncio.timeout()` context manager for deadline enforcement instead of manual `wait_for()`.

asyncio runs single-threaded but concurrent. Shared mutable state still requires synchronization. Operations like `dict[key] = value` are atomic, but read-modify-write sequences need protection. Use `asyncio.Lock` for critical sections accessing shared state.

## Security

Never pass user input to `eval()` or `exec()`. Both execute arbitrary Python code with full interpreter access. Use `ast.literal_eval()` for safe evaluation of literals like lists and dicts. Sandboxing Python is ineffective—determined attackers escape trivially.

Pickle deserialization executes arbitrary code during `__reduce__` calls. Never `pickle.load()` untrusted data from network or user files. Use JSON for simple data or Protocol Buffers for structured messages from untrusted sources.

ORM raw queries bypass protection mechanisms. Django's `.extra()` and `.raw()` are injection vectors. SQLAlchemy's `text()` requires bound parameters: `text("WHERE id = :id").bindparams(id=user_id)`. Never interpolate strings into SQL.

Passing `shell=True` to `subprocess` enables shell injection. Use list form instead: `subprocess.run(['git', 'log', user_ref])`. If shell required, quote arguments with `shlex.quote()` before interpolation.

Server-side request forgery allows internal network access. Validate URLs before fetching with `requests` or `urllib`. Block RFC 1918 addresses (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) and link-local (169.254.0.0/16). Maintain domain allow-lists when fetching user-provided URLs.
