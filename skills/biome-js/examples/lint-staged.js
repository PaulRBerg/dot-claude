/**
 * Lint-staged configuration for Biome + Prettier
 *
 * Pattern:
 * 1. biome check --write for formatting and linting
 * 2. prettier for markdown/yaml (Biome doesn't handle these well)
 * 3. Separate pass for noUnusedImports (disabled during dev, enforced at commit)
 *
 * @type {import("lint-staged").Configuration}
 */
module.exports = {
  // Format and lint JS/TS/JSON with Biome
  "*.{js,json,jsonc,ts,tsx}": "bun biome check --write",

  // Format markdown and yaml with Prettier
  "*.{md,yml,yaml}": "bun prettier --cache --write",

  // Enforce unused imports cleanup at commit time
  // This runs after biome check, so it only affects imports
  "*.{ts,tsx}": "bun biome lint --write --only correctness/noUnusedImports",
};
