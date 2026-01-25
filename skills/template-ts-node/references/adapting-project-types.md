# Adapting for Specific Project Types

## CLI Tools

**Add dependencies:**

```bash
bun add commander chalk ora
bun add -d @types/node
```

**Update `package.json`:**

```json
{
  "bin": {
    "cli-name": "./dist/cli.js"
  }
}
```

**Create `src/cli.ts`:**

```typescript
#!/usr/bin/env node

import { Command } from "commander";
import { VERSION } from "./index.js";

const program = new Command();

program
  .name("cli-name")
  .description("CLI description")
  .version(VERSION);

program.parse();
```

## Libraries

**Update `package.json` for library distribution:**

```json
{
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "types": "./dist/index.d.ts"
    }
  },
  "files": ["dist"]
}
```

**Configure `tsconfig.json` for declaration generation:**

```json
{
  "compilerOptions": {
    "declaration": true,
    "declarationMap": true
  }
}
```

## Backend Services

**Add server dependencies:**

```bash
bun add express
bun add -d @types/express
```

**Create `src/server.ts`:**

```typescript
import express from "express";

const app = express();
const PORT = process.env.PORT || 3000;

app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```
