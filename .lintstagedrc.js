import { homedir } from 'node:os';
import path from 'node:path';

const codexJustfile = path.join(homedir(), '.codex', 'justfile');

/**
 * @type {import("lint-staged").Configuration}
 */
export default {
  // Format markdown files with Prettier
  '*.md': 'bunx --no-install prettier --write --cache --log-level warn',
  // Rebuild Codex instructions when the root CLAUDE.md changed, then commit
  // the regenerated AGENTS.md in ~/.codex and ~/.agents if it's the only
  // thing dirty in those repos
  './CLAUDE.md': [
    () => `just --justfile ${JSON.stringify(codexJustfile)} build`,
    'bash helpers/commit_codex_agents.sh',
    'bash helpers/commit_agents_repo.sh',
  ],
  // Always regenerate settings.json from JSONC sources on every commit
  '*': [
    "bash helpers/merge_settings.sh",
  ],
};
