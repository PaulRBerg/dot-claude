/**
 * @type {import("lint-staged").Configuration}
 */
export default {
  // Format documentation and configuration with Prettier
  '**/*.{md,json,jsonc,yaml,yml}':
    'bunx --no-install prettier --write --cache --cache-location .cache/prettier/.prettier-cache --log-level warn',
  // Run the same Python checks CI runs
  '*.py': [() => 'just ruff-check', () => 'just pyright-check'],
  // Always regenerate settings.json from JSONC sources on every commit
  '*': [
    "bash helpers/merge_settings.sh",
  ],
};
