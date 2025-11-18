/**
 * @type {import("lint-staged").Configuration}
 */
export default {
  'settings/**/*.{json,jsonc}': [
    "just merge-settings",
    "git add settings.json",
  ],
};
