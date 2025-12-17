import { type UserConfig, mergeConfig } from "vitest/config";

const isCI = process.env.CI === "true";

export const sharedConfig: UserConfig = {
  test: {
    environment: "node",
    globals: true,
    testTimeout: isCI ? 120_000 : 60_000,
    retry: isCI ? 5 : 0,
    reporters: isCI ? ["github-actions", "json"] : ["default"],
    outputFile: isCI ? "./test-results.json" : undefined,
  },
};

export function createProjectConfig(config: UserConfig): UserConfig {
  return mergeConfig(sharedConfig, config);
}
