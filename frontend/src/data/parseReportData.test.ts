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
  prepareImplementationReport,
} from "./parseReportData";

function miniature(name: string) {
  // Should match what's used in our backend integration tests obviously.
  return `direct:bowtie.tests.miniatures:${name}`;
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

    const id = miniature("always_invalid");
    const tempdir = await mkdtemp(join(tmpdir(), "bowtie-ui-tests-"));

    try {
      const schema = join(tempdir, "schema.json");
      await writeFile(schema, "{}");

      const instance = join(tempdir, "instance.json");
      await writeFile(instance, "37");

      lines = bowtie(["validate", "-i", id, schema, instance]);
    } finally {
      await rm(tempdir, { recursive: true });
    }

    const report = fromSerialized(lines);

    const metadata = report.runMetadata.implementations.get(id)!;
    const testCase = report.cases.get(1);

    expect(report).toStrictEqual({
      runMetadata: new RunMetadata(
        Dialect.withName("draft2020-12"),
        new Map([
          [
            id,
            new Implementation(id, {
              name: "always_invalid",
              version: metadata.version,
              dialects: Array.from(Dialect.known()).map(
                (dialect) => dialect.uri,
              ),
              homepage: metadata.homepage,
              issues: metadata.issues,
              source: metadata.source,
              os: metadata.os,
              os_version: metadata.os_version,
              language: "python",
              language_version: metadata.language_version,
              links: metadata.links,
            }),
          ],
        ]),
        report.runMetadata.bowtieVersion,
        report.runMetadata.started,
        {},
      ),
      implementationsResults: new Map([
        [
          id,
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
    const id = miniature("always_invalid");
    const cases = Object.values(testCases).map((each) => JSON.stringify(each));

    const lines = bowtie(["run", "-i", id, "-D", "7"], cases.join("\n") + "\n");

    const report = fromSerialized(lines);

    const metadata = report.runMetadata.implementations.get(id)!;

    expect(report).toStrictEqual({
      runMetadata: new RunMetadata(
        Dialect.withName("draft7"),
        new Map([
          [
            id,
            new Implementation(id, {
              name: "always_invalid",
              version: metadata.version,
              dialects: Array.from(Dialect.known()).map(
                (dialect) => dialect.uri,
              ),
              homepage: metadata.homepage,
              issues: metadata.issues,
              source: metadata.source,
              os: metadata.os,
              os_version: metadata.os_version,
              language: "python",
              language_version: metadata.language_version,
              links: metadata.links,
            }),
          ],
        ]),
        report.runMetadata.bowtieVersion,
        report.runMetadata.started,
        {},
      ),
      implementationsResults: new Map([
        [
          id,
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
    const id = miniature("always_invalid");
    const cases = Object.values(testCases).map((each) => JSON.stringify(each));
    const allReportsData = new Map<Dialect, ReportData>();

    for (const dialect of Dialect.known()) {
      const lines = bowtie(
        ["run", "-i", id, "-D", dialect.shortName],
        cases.join("\n") + "\n",
      );
      const report = fromSerialized(lines);
      allReportsData.set(dialect, report);
    }

    const implementationReport = prepareImplementationReport(
      id,
      allReportsData,
    );

    const metadata = implementationReport!.implementation;

    expect(implementationReport).toStrictEqual({
      implementation: new Implementation(id, {
        name: "always_invalid",
        version: metadata.version,
        dialects: Array.from(Dialect.known()).map((dialect) => dialect.uri),
        homepage: metadata.homepage,
        issues: metadata.issues,
        source: metadata.source,
        os: metadata.os,
        os_version: metadata.os_version,
        language: "python",
        language_version: metadata.language_version,
        links: metadata.links,
      }),
      dialectCompliance: new Map([
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
    });
  });
});
