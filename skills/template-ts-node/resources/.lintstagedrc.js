module.exports = {
  "*.{js,json,jsonc,ts}": "bun biome check --write",
  "*.{js,ts}": "bun biome lint --write --only correctness/noUnusedImports",
  "*.{md,yml,yaml}": "bun prettier --cache --write",
};
