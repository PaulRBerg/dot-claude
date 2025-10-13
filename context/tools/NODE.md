### Node.js

#### `ni` utility

Use the [`ni`](https://github.com/antfu-collective/ni) utility to interact with and manage Node.js dependencies. `ni` is
a drop-in replacement for `npm`, `yarn`, `pnpm`, `bun`, etc.

| Run this command    | Instead of                           |
| ------------------- | ------------------------------------ |
| `nlx package-name`  | `npx package-name`                   |
| `ni`                | `npm install`                        |
| `ni package-name`   | `npm install package-name`           |
| `ni -D dev-package` | `npm install --save-dev dev-package` |
| `nun package-name`  | `npm uninstall package-name`         |
| `nr my-script`      | `npm run my-script`                  |

#### Dependencies in Private Packages

Private packages (with `"private": true` in `package.json`) do not follow the same dependency conventions as public
packages. All dependencies are declared under `dependencies` - there is no need to also use `devDependencies`.
