# Effect-Next.js Implementation Patterns

## Service Definition

Define services using `Effect.Service` with methods wrapped in `Effect.fn()`:

```typescript
import { Effect, Schema, Data } from "effect"
import { FileSystem } from "@effect/platform"

// Custom error type
export class TodoError extends Data.TaggedError("TodoError")<{
  message: string
}> {}

// Service definition
export class TodoStore extends Effect.Service<TodoStore>()("app/TodoStore", {
  effect: Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem

    return {
      getAll: Effect.fn("getAll")(function* () {
        const content = yield* fs.readFileString("todos.json")
        return yield* Schema.decodeUnknown(Schema.Array(TodoSchema))(JSON.parse(content))
      }),

      create: Effect.fn("create")(function* (title: string) {
        const todos = yield* this.getAll
        const newTodo = { id: crypto.randomUUID(), title, done: false }
        yield* fs.writeFileString("todos.json", JSON.stringify([...todos, newTodo]))
        return newTodo
      }),
    }
  }),
}) {}
```

## Middleware Implementation

### Provider Middleware (Non-Wrapped)

```typescript
import { NextMiddleware } from "@mcrovero/effect-nextjs"
import { Context, Layer, Schema, Effect } from "effect"

export class CurrentUser extends Context.Tag("CurrentUser")<
  CurrentUser,
  { id: string; name: string }
>() {}

export class AuthMiddleware extends NextMiddleware.Tag<AuthMiddleware>()(
  "AuthMiddleware",
  { provides: CurrentUser, failure: Schema.String }
) {}

export const AuthMiddlewareLive = Layer.succeed(
  AuthMiddleware,
  AuthMiddleware.of(
    Effect.fn("AuthMiddleware")(() =>
      Effect.gen(function* () {
        // Validate session, fetch user, etc.
        return { id: "user-123", name: "Ada Lovelace" }
      })
    )
  )
)
```

### Interceptor Middleware (Wrapped)

```typescript
export class LoggingMiddleware extends NextMiddleware.Tag<LoggingMiddleware>()(
  "LoggingMiddleware",
  { wrap: true }
) {}

export const LoggingMiddlewareLive = Layer.succeed(
  LoggingMiddleware,
  LoggingMiddleware.of(({ next }) =>
    Effect.gen(function* () {
      yield* Effect.log("Request started")
      const result = yield* next
      yield* Effect.log("Request completed")
      return result
    })
  )
)
```

## Base Layer Configuration

```typescript
import { Next } from "@mcrovero/effect-nextjs"
import { Layer, Logger, LogLevel } from "effect"
import { NodeContext } from "@effect/platform-node"

// Compose all layers
const AppLive = Layer.mergeAll(
  AuthMiddlewareLive,
  LoggingMiddlewareLive,
  TodoStore.Default.pipe(Layer.provide(NodeContext.layer))
).pipe(
  Layer.provide(Logger.minimumLogLevel(LogLevel.Debug))
)

// Create specialized handlers
export const BasePage = Next.make("Base", AppLive)
  .middleware(AuthMiddleware)

export const BaseAction = Next.make("Base", AppLive)
  .middleware(AuthMiddleware)

export const BaseApi = Next.make("Base", AppLive)
  .middleware(LoggingMiddleware)
  .middleware(AuthMiddleware)
```

## Page Example

```typescript
import { Effect, Schema } from "effect"
import { decodeSearchParamsUnknown } from "@mcrovero/effect-nextjs/Params"
import { BasePage, CurrentUser, TodoStore } from "@/lib/base"

const SearchSchema = Schema.Struct({
  q: Schema.optional(Schema.String),
})

const HomePage = Effect.fn("HomePage")(function* (props) {
  const user = yield* CurrentUser
  const { q } = yield* decodeSearchParamsUnknown(SearchSchema)(props.searchParams)
  const todos = yield* TodoStore.pipe(Effect.flatMap((s) => s.getAll))

  const filtered = q ? todos.filter((t) => t.title.includes(q)) : todos

  return (
    <main>
      <h1>Welcome, {user.name}</h1>
      <ul>
        {filtered.map((todo) => (
          <li key={todo.id}>{todo.title}</li>
        ))}
      </ul>
    </main>
  )
})

export default BasePage.build(HomePage)
```

## Server Action Example

```typescript
"use server"
import { Effect } from "effect"
import { BaseAction, TodoStore } from "@/lib/base"

const _createTodo = Effect.fn("createTodo")(function* (input: { title: string }) {
  const store = yield* TodoStore
  const todo = yield* store.create(input.title)
  const todos = yield* store.getAll
  return { todo, todos, error: null }
}).pipe(
  Effect.catchAll((err) =>
    Effect.succeed({ todo: null, todos: [], error: err.message })
  )
)

export const createTodo = BaseAction.build(_createTodo)
```

## Error Handling Patterns

### Effect-Level Catch

```typescript
const action = Effect.fn("action")(function* () {
  // ... effect logic
}).pipe(
  Effect.catchAll((err) =>
    Effect.succeed({ data: null, error: err.message ?? "Unknown error" })
  )
)
```

### Middleware Failure Schema

```typescript
export class AuthMiddleware extends NextMiddleware.Tag<AuthMiddleware>()(
  "AuthMiddleware",
  {
    provides: CurrentUser,
    failure: Schema.Struct({
      _tag: Schema.Literal("Unauthorized"),
      message: Schema.String,
    }),
  }
) {}
```

### Custom Tagged Errors

```typescript
import { Data } from "effect"

export class NotFoundError extends Data.TaggedError("NotFoundError")<{
  resource: string
}> {}

export class ValidationError extends Data.TaggedError("ValidationError")<{
  field: string
  message: string
}> {}
```
