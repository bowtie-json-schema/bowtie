import { join } from "node:path";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { tmpdir } from "node:os";

import { describe, expect, test } from "vitest";

import Dialect from "./Dialect";
import { fromSerialized } from "./parseReportData";

function tag(image: string) {
  // Should match what's used in our `noxfile`, certainly until we handle image
  // building here from the frontend test suite.
  return `bowtie-ui-tests/${image}`;
}

function bowtie(args: string[] = [], input?: string, status = 0) {
  const result = spawnSync("bowtie", args, { input });

  try {
    expect(result.status).toStrictEqual(status);
  } catch (error: unknown) {
    if (!(error instanceof Error)) {
      throw error;
    }
    error.message =
      error.message +
      `
      stdout contained:

        ${result.stdout?.toString()}

      stderr contained:

        ${result.stderr?.toString()}
    `;
    throw error;
  }
  return result.stdout.toString();
}

describe("parseReportData", () => {
  test("it parses reports", async () => {
    let lines: string;

    const tempdir = await mkdtemp(join(tmpdir(), "bowtie-ui-tests-"));

    try {
      const schema = join(tempdir, "schema.json");
      await writeFile(schema, "{}");

      const instance = join(tempdir, "instance.json");
      await writeFile(instance, "37");

      lines = bowtie(["validate", "-i", tag("envsonschema"), schema, instance]);
    } finally {
      await rm(tempdir, { recursive: true });
    }

    const report = fromSerialized(lines);

    const metadata = report.runInfo.implementations[tag("envsonschema")];
    const testCase = report.cases.get(1);

    // FIXME: Remove Seqs + duplication all over from the UI's representation
    expect(report).toStrictEqual({
      runInfo: {
        started: report.runInfo.started,
        bowtie_version: report.runInfo.bowtie_version,
        dialect: Dialect.withName("draft2020-12").uri,
        implementations: {
          [tag("envsonschema")]: {
            name: "envsonschema",
            language: "python",
            dialects: metadata?.dialects,
            homepage: metadata?.homepage,
            issues: metadata?.issues,
            source: metadata?.source,
            links: metadata?.links,
          },
        },
        metadata: {},
      },
      implementationsResults: new Map([
        [
          tag("envsonschema"),
          {
            erroredCases: 0,
            erroredTests: 0,
            skippedTests: 0,
            failedTests: 1,

            id: tag("envsonschema"),
            cases: new Map([[1, [{ state: "failed", valid: false }]]]),
          },
        ],
      ]),
      cases: new Map([
        [
          1,
          {
            description: testCase?.description,
            schema: {},
            tests: [
              {
                description: testCase?.tests[0].description,
                instance: 37,
                valid: null,
              },
            ],
          },
        ],
      ]),
      didFailFast: false,
    });
  });
});
