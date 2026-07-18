import { homedir } from 'node:os';
import path from 'node:path';

const codexJustfile = path.join(homedir(), '.codex', 'justfile');

/**
 * @type {import("lint-staged").Configuration}
 */
export default {
  // Format markdown files with Prettier
  '*.md': 'bunx --no-install prettier --write --cache --log-level warn',
  // Rebuild Codex instructions when the root CLAUDE.md changed
  './CLAUDE.md': () =>
    `just --justfile ${JSON.stringify(codexJustfile)} build`,
  // Always regenerate settings.json from JSONC sources on every commit
  '*': [
    "bash helpers/merge_settings.sh",
  ],
};
