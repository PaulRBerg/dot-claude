/**
 * @type {import("lint-staged").Configuration}
 */
export default {
  'settings/**/*.{json,jsonc}': [
    "bash helpers/merge-settings.sh",
    "git add settings.json",
  ],
};
