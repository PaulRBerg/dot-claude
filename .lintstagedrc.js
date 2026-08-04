/**
 * @type {import("lint-staged").Configuration}
 */
export default {
  // Format markdown files with Prettier
  '*.md': 'bunx --no-install prettier --write --cache --log-level warn',
  // Run the same Python checks CI runs
  '*.py': [() => 'just ruff-check', () => 'just pyright-check'],
  // Always regenerate settings.json from JSONC sources on every commit
  '*': [
    "bash helpers/merge_settings.sh",
  ],
};
