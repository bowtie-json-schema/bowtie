import { platform, release } from "node:os";
import { join } from "node:path";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import { describe, expect, test } from "vitest";

import Dialect from "./Dialect";
import Implementation from "./Implementation";
import {
  RunMetadata,
  ReportData,
  fromSerialized,
  prepareDialectsComplianceReportFor,
} from "./parseReportData";

function run(command: string, args: string[] = [], input?: string, status = 0) {
  const result = spawnSync(command, args, { input });

  try {
    expect(result.status).toStrictEqual(status);
  } catch (error: unknown) {
    if (!(error instanceof Error)) {
      throw error;
    }
    error.message =
      error.message +
      `
      ran: bowtie ${args.join(" ")}
      stdout contained:

        ${result.stdout?.toString()}

      stderr contained:

        ${result.stderr?.toString()}

      stdin contained:

        ${input?.toString()}
    `;
    throw error;
  }
  return result.stdout.toString();
}

function miniature(name: string): Implementation {
  const id = `direct:bowtie.tests.miniatures:${name}`;

  // Should match what's used in our backend integration tests, obviously.
  return (
    Implementation.withId(id) ??
    new Implementation(id, {
      name,
      version: "v1.0.0",
      dialects: Array.from(Dialect.known()).map((dialect) => dialect.uri),
      homepage: "https://bowtie.report/",
      issues: "https://github.com/bowtie-json-schema/bowtie/issues",
      source: "https://github.com/bowtie-json-schema/bowtie",
      os: platform(),
      os_version: release(),
      language: "python",
      language_version: run("python", ["--version"]).split(" ")[1],
      links: [],
    })
  );
}

const testCases = {
  case1: {
    description: "case1",
    schema: {
      additionalProperties: { type: "boolean" },
      properties: { bar: {}, foo: {} },
    },
    tests: [
      {
        description: "one",
        instance: { foo: 1 },
        valid: true,
      },
      {
        description: "two",
        instance: { foo: 1, bar: 2, quux: true },
        valid: true,
      },
      {
        description: "three",
        instance: { foo: 1, bar: 2, quux: 12 },
        valid: false,
      },
    ],
  },
  case2: {
    description: "case2",
    schema: {
      additionalProperties: { type: "boolean" },
    },
    tests: [
      {
        description: "one",
        instance: { foo: true },
        valid: true,
      },
      {
        description: "two",
        instance: { foo: 1 },
        valid: false,
      },
    ],
  },
  case3: {
    description: "case3",
    schema: {
      allOf: [
        { $ref: "https://example.com/schema-with-anchor#foo" },
        { then: { $id: "http://example.com/ref/then", type: "integer" } },
      ],
    },
    tests: [
      {
        description: "one",
        instance: "foo",
        valid: false,
      },
      {
        description: "two",
        instance: 12,
        valid: true,
      },
    ],
  },
};

describe("parseReportData", () => {
  test("parses reports", async () => {
    let lines: string;

    const testImplementation = miniature("always_invalid");
    const tempdir = await mkdtemp(join(tmpdir(), "bowtie-ui-tests-"));

    try {
      const schema = join(tempdir, "schema.json");
      await writeFile(schema, "{}");

      const instance = join(tempdir, "instance.json");
      await writeFile(instance, "37");

      lines = run("bowtie", [
        "validate",
        "-i",
        testImplementation.id,
        schema,
        instance,
      ]);
    } finally {
      await rm(tempdir, { recursive: true });
    }

    const report = fromSerialized(lines);

    const testCase = report.cases.get(1);

    expect(report).toStrictEqual({
      runMetadata: new RunMetadata(
        Dialect.withName("draft2020-12"),
        new Map([[testImplementation.id, testImplementation]]),
        report.runMetadata.bowtieVersion,
        report.runMetadata.started,
        {},
      ),
      implementationsResults: new Map([
        [
          testImplementation.id,
          {
            totals: {
              erroredTests: 0,
              skippedTests: 0,
              failedTests: 1,
            },
            caseResults: new Map([[1, [{ state: "failed", valid: false }]]]),
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
              },
            ],
          },
        ],
      ]),
      didFailFast: false,
    });
  });

  test("parses reports with multiple test cases", () => {
    const testImplementation = miniature("always_invalid");
    const cases = Object.values(testCases).map((each) => JSON.stringify(each));

    const lines = run(
      "bowtie",
      ["run", "-i", testImplementation.id, "-D", "7"],
      cases.join("\n") + "\n",
    );

    const report = fromSerialized(lines);

    expect(report).toStrictEqual({
      runMetadata: new RunMetadata(
        Dialect.withName("draft7"),
        new Map([[testImplementation.id, testImplementation]]),
        report.runMetadata.bowtieVersion,
        report.runMetadata.started,
        {},
      ),
      implementationsResults: new Map([
        [
          testImplementation.id,
          {
            totals: {
              erroredTests: 0,
              skippedTests: 0,
              failedTests: 4,
            },
            caseResults: new Map([
              [
                1,
                [
                  { state: "failed", valid: false },
                  { state: "failed", valid: false },
                  { state: "successful", valid: false },
                ],
              ],
              [
                2,
                [
                  { state: "failed", valid: false },
                  { state: "successful", valid: false },
                ],
              ],
              [
                3,
                [
                  { state: "successful", valid: false },
                  { state: "failed", valid: false },
                ],
              ],
            ]),
          },
        ],
      ]),
      cases: new Map([
        [
          1,
          {
            description: testCases.case1.description,
            schema: testCases.case1.schema,
            tests: testCases.case1.tests,
          },
        ],
        [
          2,
          {
            description: testCases.case2.description,
            schema: testCases.case2.schema,
            tests: testCases.case2.tests,
          },
        ],
        [
          3,
          {
            description: testCases.case3.description,
            schema: testCases.case3.schema,
            tests: testCases.case3.tests,
          },
        ],
      ]),
      didFailFast: false,
    });
  });

  test("prepares a summarized implementation report using all the dialect reports", () => {
    const testImplementation = miniature("always_invalid");
    const cases = Object.values(testCases).map((each) => JSON.stringify(each));
    const allReportsData = new Map<Dialect, ReportData>();

    for (const dialect of Dialect.known()) {
      const lines = run(
        "bowtie",
        ["run", "-i", testImplementation.id, "-D", dialect.shortName],
        cases.join("\n") + "\n",
      );
      const report = fromSerialized(lines);
      allReportsData.set(dialect, report);
    }

    const dialectsCompliance = prepareDialectsComplianceReportFor(
      testImplementation.id,
      allReportsData,
    );

    expect(dialectsCompliance).toStrictEqual(
      new Map([
        [
          Dialect.withName("draft2020-12"),
          { erroredTests: 0, skippedTests: 0, failedTests: 4 },
        ],
        [
          Dialect.withName("draft2019-09"),
          { erroredTests: 0, skippedTests: 0, failedTests: 4 },
        ],
        [
          Dialect.withName("draft7"),
          { erroredTests: 0, skippedTests: 0, failedTests: 4 },
        ],
        [
          Dialect.withName("draft6"),
          { erroredTests: 0, skippedTests: 0, failedTests: 4 },
        ],
        [
          Dialect.withName("draft4"),
          { erroredTests: 0, skippedTests: 0, failedTests: 4 },
        ],
        [
          Dialect.withName("draft3"),
          { erroredTests: 0, skippedTests: 0, failedTests: 4 },
        ],
      ]),
    );
  });
});
