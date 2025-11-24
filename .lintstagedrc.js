/**
 * @type {import("lint-staged").Configuration}
 */
export default {
  // Always regenerate settings.json from JSONC sources on every commit
  '*': [
    "bash helpers/merge_settings.sh",
  ],
};
