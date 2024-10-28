import { join } from "node:path";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import { describe, expect, test } from "vitest";

import Dialect from "./Dialect";
import Implementation from "./Implementation";
import { BenchmarkRunMetadata, fromJSON } from "./parseBenchmarkData";

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

const valid_sample_benchmark = {
  name: "sample_benchmark",
  description: "benchmark",
  schema: {
    type: "object",
  },
  tests: [
    {
      description: "test 1",
      instance: {
        a: "b",
      },
    },
    {
      description: "test 2",
      instance: {
        a: "b",
      },
    },
  ],
};

describe("parseBenchmarkReportData", () => {
  test(
    "parses benchmark reports",
    { timeout: 120000 }, // FIXME: Make this test faster.
    async () => {
      const benchmark_string: string = JSON.stringify(valid_sample_benchmark);
      let output: string;

      const id = "direct:null";
      const tempdir = await mkdtemp(join(tmpdir(), "bowtie-ui-tests-"));

      try {
        const benchmark = join(tempdir, "benchmark.json");
        await writeFile(benchmark, benchmark_string);

        output = bowtie(["perf", "-i", id, benchmark]);
      } finally {
        await rm(tempdir, { recursive: true });
      }
      const benchmarkReport = fromJSON(output);
      const reportMetadata = benchmarkReport.metadata;
      const reportResults = benchmarkReport.results;
      const implementationMetadata = reportMetadata.implementations.get(id)!;

      expect(benchmarkReport).toStrictEqual({
        metadata: new BenchmarkRunMetadata(
          Dialect.withName("draft2020-12"),
          new Map([
            [
              id,
              new Implementation(id, {
                name: "null",
                version: implementationMetadata.version,
                dialects: Array.from(Dialect.known()).map(
                  (dialect) => dialect.uri,
                ),
                documentation: implementationMetadata.documentation,
                homepage: implementationMetadata.homepage,
                issues: implementationMetadata.issues,
                source: implementationMetadata.source,
                os: implementationMetadata.os,
                os_version: implementationMetadata.os_version,
                language: "python",
                language_version: implementationMetadata.language_version,
                links: implementationMetadata.links,
              }),
            ],
          ]),
          reportMetadata.bowtieVersion,
          reportMetadata.started,
          reportMetadata.systemMetadata,
        ),
        results: [
          {
            name: "sample_benchmark",
            description: "benchmark",
            benchmarkResults: [
              {
                name: "sample_benchmark",
                description: "benchmark",
                testResults: [
                  {
                    description: "test 1",
                    implementationResults:
                      reportResults[0].benchmarkResults[0].testResults[0]
                        .implementationResults,
                  },
                  {
                    description: "test 2",
                    implementationResults:
                      reportResults[0].benchmarkResults[0].testResults[1]
                        .implementationResults,
                  },
                ],
              },
            ],
            benchmarkType: "from_input",
            varyingParameter: undefined,
          },
        ],
      });
    },
  );
});
