# Native Effect Platform API Handlers

Build Next.js API handlers directly with `@effect/platform` without wrapper libraries. These patterns complement `@mcrovero/effect-nextjs` by providing lower-level control.

## Raw HTTP APIs

Use `HttpApp.toWebHandlerRuntime` for simple API handlers with full Effect capabilities.

```typescript
// src/app/api/example/route.ts
import {
  HttpApp,
  HttpServerRequest,
  HttpServerResponse,
} from "@effect/platform";
import { Effect, Layer, ManagedRuntime, Schema } from "effect";

// Main layer representing all services the handler needs (db, auth, etc.)
const mainLive = Layer.empty;

const managedRuntime = ManagedRuntime.make(mainLive);
const runtime = await managedRuntime.runtime();

// Handler effect consumes request from context and produces HTTP response
const exampleEffectHandler = Effect.gen(function* () {
  // Consume request from context with schema validation
  const { name } = yield* HttpServerRequest.schemaBodyJson(
    Schema.Struct({
      name: Schema.String,
    }),
  );
  return yield* HttpServerResponse.json({
    message: `Hello, ${name}`,
  });
});

const handler = HttpApp.toWebHandlerRuntime(runtime)(exampleEffectHandler);

type Handler = (req: Request) => Promise<Response>;
export const POST: Handler = handler;
```

## Effect HttpApi Framework

Build type-safe APIs with automatic OpenAPI generation, Swagger UI, and client SDK.

### Schema Definition

Define API groups and endpoints with full type safety:

```typescript
// src/app/api/[[...path]]/route.ts
import {
  FetchHttpClient,
  HttpApi,
  HttpApiBuilder,
  HttpApiClient,
  HttpApiEndpoint,
  HttpApiGroup,
  HttpApiSwagger,
  HttpMiddleware,
  HttpServer,
  OpenApi,
} from "@effect/platform";
import { Config, Effect, Layer, Schema } from "effect";

// Custom error type
class FooError extends Schema.TaggedError<FooError>("FooError")(
  "FooError",
  {},
) {}

// API group with endpoints
class FooApi extends HttpApiGroup.make("foo")
  .add(
    HttpApiEndpoint.get("bar", "/bar")
      .setHeaders(Schema.Struct({ page: Schema.NumberFromString }))
      .addSuccess(Schema.String),
  )
  .add(
    HttpApiEndpoint.post("baz", "/baz/:id")
      .setPath(Schema.Struct({ id: Schema.NumberFromString }))
      .setPayload(Schema.Struct({ name: Schema.String }))
      .addSuccess(Schema.Struct({ ok: Schema.Boolean }))
      .addError(FooError),
  ) {}

// Compose API with prefix and OpenAPI metadata
class MyApi extends HttpApi.make("api")
  .add(FooApi)
  .prefix("/api")
  .annotateContext(
    OpenApi.annotations({
      title: "My API",
      description: "API for my endpoints",
    }),
  ) {}
```

### Implementation

Implement handlers with full type inference:

```typescript
const FooLive = HttpApiBuilder.group(MyApi, "foo", (handlers) =>
  handlers
    .handle("bar", (_) => Effect.succeed(`page: ${_.headers.page}`))
    .handle("baz", (_) =>
      Effect.gen(function* () {
        const id = _.path.id;
        if (id < 0) {
          return yield* new FooError();
        }
        return {
          ok: _.payload.name.length === id,
        };
      }),
    ),
);

const ApiLive = HttpApiBuilder.api(MyApi).pipe(Layer.provide(FooLive));
```

### Middleware Stack

Configure CORS, OpenAPI JSON, Swagger UI, and logging:

```typescript
const middleware = Layer.mergeAll(
  HttpApiBuilder.middlewareCors(),
  HttpApiBuilder.middlewareOpenApi({
    path: "/api/openapi.json",
  }),
  HttpApiSwagger.layer({
    path: "/api/docs",
  }),
  HttpApiBuilder.middleware(HttpMiddleware.logger),
);

const { handler } = Layer.empty.pipe(
  Layer.merge(middleware),
  Layer.provideMerge(ApiLive),
  Layer.merge(HttpServer.layerContext),
  HttpApiBuilder.toWebHandler,
);

type Handler = (req: Request) => Promise<Response>;
export const GET: Handler = handler;
export const POST: Handler = handler;
export const PUT: Handler = handler;
export const PATCH: Handler = handler;
export const DELETE: Handler = handler;
export const OPTIONS: Handler = handler;
```

### Type-Safe Client

Generate a fully typed client from the API schema:

```typescript
const example = Effect.gen(function* () {
  // Import schema only - no runtime dependency
  const client = yield* HttpApiClient.make(MyApi, {
    baseUrl: yield* Config.string("BASE_URL"),
  });

  const res = yield* client.foo.bar({ headers: { page: 1 } });
  const res2 = yield* client.foo.baz({
    path: { id: 1 },
    payload: { name: "test" },
  });
  return { res, res2 };
}).pipe(Effect.provide(FetchHttpClient.layer));
```

## waitUntil Pattern

Execute background tasks that continue after the response is sent. Essential for serverless environments.

### Service Definition

```typescript
import { Effect, Runtime, Context, Layer } from "effect";

class WaitUntil extends Context.Tag("WaitUntil")<
  WaitUntil,
  (promise: Promise<unknown>) => void
>() {}

const effectWaitUntil = <A, E, R>(
  effect: Effect.Effect<A, E, R>,
  abortSignal?: AbortSignal,
) =>
  Effect.runtime<R>().pipe(
    Effect.zip(WaitUntil),
    Effect.flatMap(([runtime, waitUntil]) =>
      Effect.sync(() =>
        waitUntil(Runtime.runPromise(runtime, effect, { signal: abortSignal })),
      ),
    ),
  );
```

### Vercel Integration

```typescript
import { waitUntil } from "@vercel/functions";

const VercelWaitUntil = Layer.succeed(WaitUntil, waitUntil);
```

### Cloudflare Integration

```typescript
interface ExecutionContext {
  waitUntil(promise: Promise<any>): void;
  passThroughOnException(): void;
  props: any;
}

const CloudflareWaitUntil = (ctx: ExecutionContext) =>
  Layer.succeed(WaitUntil, ctx.waitUntil);
```
