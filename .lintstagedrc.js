/**
 * @type {import("lint-staged").Configuration}
 */
export default {
  // Format markdown files with mdformat (excluding template resources)
  '*.md': (files) => {
    const filtered = files.filter(f => !f.includes('skills/template-ts-node/resources/'));
    return filtered.length > 0 ? `mdformat ${filtered.join(' ')}` : [];
  },
  // Always regenerate settings.json from JSONC sources on every commit
  '*': [
    "bash helpers/merge_settings.sh",
  ],
};
