/**
 * @type {import("lint-staged").Configuration}
 */
export default {
  'settings/**/*.{json,jsonc}': [
    "bash helpers/merge_settings.sh",
    "git add settings.json",
  ],
};
