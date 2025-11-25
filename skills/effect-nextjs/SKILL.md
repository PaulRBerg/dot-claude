---
name: effect-nextjs
description: This skill should be used when the user asks to "use Effect with Next.js", "create Effect server actions", "add Effect middleware to Next.js", "integrate Effect runtime in App Router", "build API routes with Effect", "create HttpApi handlers", "use @effect/platform in Next.js", mentions @mcrovero/effect-nextjs or @effect/platform HttpApi, or works with Effect-based pages, routes, server components, or API handlers in Next.js 15+.
---

# Effect + Next.js Integration

`@mcrovero/effect-nextjs` provides typed helpers for integrating Effect with Next.js 15+ App Router—pages, server actions, route handlers, and server components.

## Effect Documentation

For Effect-ts fundamentals, fetch from these Context7 MCP resources:

- `/effect-ts/effect` - Core Effect library
- `/llmstxt/effect_website_llms_txt` - Official Effect docs
- `/llmstxt/effect_website_llms-full_txt` - Full Effect documentation

Or fetch directly: https://effect.website/llms.txt

This skill covers **only** the effect-nextjs integration patterns.

## Core API

### Creating Handlers

```typescript
import { Next } from "@mcrovero/effect-nextjs"
import { Layer } from "effect"

// Stateless layers (recommended)
const AppLive = Layer.mergeAll(ServiceA.Default, ServiceB.Default)
export const BasePage = Next.make("BasePage", AppLive)

// Stateful layers (database connections, etc.)
import { ManagedRuntime, globalValue } from "effect"
export const runtime = globalValue("AppRuntime", () => {
  const rt = ManagedRuntime.make(StatefulLive)
  process.on("SIGINT", () => rt.dispose())
  return rt
})
export const BasePage = Next.makeWithRuntime("BasePage", runtime)
```

### Chaining Middleware

```typescript
export const AuthenticatedPage = Next.make("Base", AppLive)
  .middleware(AuthMiddleware)
  .middleware(LoggingMiddleware)  // Left-to-right execution
```

### Building Handlers

```typescript
const HomePage = Effect.fn("HomePage")(function* () {
  const user = yield* CurrentUser
  return <div>Hello {user.name}</div>
})

export default BasePage.build(HomePage)
```

## Middleware Definition

Define middleware with `NextMiddleware.Tag()`:

```typescript
import { NextMiddleware } from "@mcrovero/effect-nextjs"
import { Context, Layer, Schema, Effect } from "effect"

// 1. Define the capability tag
export class CurrentUser extends Context.Tag("CurrentUser")<
  CurrentUser,
  { id: string; name: string }
>() {}

// 2. Define the middleware
export class AuthMiddleware extends NextMiddleware.Tag<AuthMiddleware>()(
  "AuthMiddleware",
  {
    provides: CurrentUser,           // What this middleware provides
    failure: Schema.String,          // Error type on failure
  }
) {}

// 3. Implement the middleware
export const AuthMiddlewareLive = Layer.succeed(
  AuthMiddleware,
  AuthMiddleware.of(
    Effect.fn("AuthMiddleware")(() => Effect.succeed({ id: "1", name: "Ada" }))
  )
)
```

**Middleware options:**
- `provides` - Context.Tag this middleware injects
- `failure` - Schema for error type
- `wrap: true` - Interceptor pattern (run before AND after)
- `catches` - Error types to catch when `wrap: true`
- `returns` - Custom return type when `wrap: true`

## Handler Patterns

```typescript
// Page
export default BasePage.build(pageEffect)

// Server Action
export const myAction = BaseAction.build(actionEffect)

// Route Handler
export const GET = BaseApi.build(getEffect)
export const POST = BaseApi.build(postEffect)

// Server Component (same pattern)
export default BasePage.build(componentEffect)
```

## Utilities

### Navigation

```typescript
import { Redirect, PermanentRedirect, NotFound } from "@mcrovero/effect-nextjs/Navigation"

yield* Redirect("/new-path")           // 307 redirect
yield* PermanentRedirect("/new-path")  // 308 redirect
yield* NotFound                        // Render 404
```

### Cache Revalidation

```typescript
import { RevalidatePath, RevalidateTag } from "@mcrovero/effect-nextjs/Cache"

yield* RevalidatePath("/")
yield* RevalidateTag("my-tag")
```

### Request Data

```typescript
import { Headers, Cookies, DraftMode } from "@mcrovero/effect-nextjs/Headers"

const headers = yield* Headers
const cookies = yield* Cookies
const draftMode = yield* DraftMode
```

### Params Decoding

```typescript
import { decodeParamsUnknown, decodeSearchParamsUnknown } from "@mcrovero/effect-nextjs/Params"

const HomePage = Effect.fn("HomePage")(function* (props) {
  const params = yield* decodeParamsUnknown(
    Schema.Struct({ id: Schema.String })
  )(props.params)

  const search = yield* decodeSearchParamsUnknown(
    Schema.Struct({ q: Schema.optional(Schema.String) })
  )(props.searchParams)

  return <div>ID: {params.id}, Query: {search.q}</div>
})
```

## Best Practices

1. **Use `Effect.fn()`** - Automatic telemetry spans and better stack traces
2. **Keep layers stateless** - Use `Next.makeWithRuntime()` + `globalValue` only for stateful services
3. **Centralize base handlers** - Create `BasePage`, `BaseAction`, `BaseApi` with appropriate middleware
4. **Error handling** - Use `.catchAll()` for Effect-level errors, middleware `failure` schema for typed errors
5. **Request caching** - Use `@mcrovero/effect-react-cache` for request-scoped memoization

## Additional Resources

Reference files are located in the `references/` directory.

`PATTERNS.md` - Complete implementation examples:
- Service definition patterns
- Middleware implementations
- Base layer configuration
- Full page and action examples

`API_HANDLERS.md` - Native `@effect/platform` API patterns:
- Raw HTTP handlers with `HttpApp.toWebHandlerRuntime`
- Type-safe HttpApi framework with OpenAPI/Swagger
- Background task execution with `waitUntil` (Vercel/Cloudflare)
