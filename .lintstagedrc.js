/**
 * @type {import("lint-staged").Configuration}
 */
export default {
  // Format markdown files with mdformat
  '*.md': 'mdformat',
  // Always regenerate settings.json from JSONC sources on every commit
  '*': [
    "bash helpers/merge_settings.sh",
  ],
};
