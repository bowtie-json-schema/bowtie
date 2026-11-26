import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import type { Page } from "@playwright/test";

/**
 * The real-world benchmark results, from a scheduled run of
 * sourcemeta-research/jsonschema-benchmark. The page's own requests for them
 * are answered from this file, so the tests do not depend on the benchmark's
 * latest run (Bowtie's badges still come from the live site).
 */
const results = readFileSync(
  fileURLToPath(new URL("./jsonschema-benchmark.json", import.meta.url)),
);

export async function serveRealWorldResults(page: Page) {
  await page.route("**/jsonschema-benchmark/data.json", (route) =>
    route.fulfill({ body: results, contentType: "application/json" }),
  );
}
