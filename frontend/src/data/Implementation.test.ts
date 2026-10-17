import { describe, expect, test } from "vitest";

import Dialect from "./Dialect";
import Implementation from "./Implementation";

describe("Implementation", () => {
  test("leaves out a prerelease dialect a harness opts into", () => {
    const implementation = new Implementation("python-prerelease-opt-in", {
      name: "prerelease-opt-in",
      language: "python",
      dialects: [
        "https://json-schema.org/v1",
        "https://json-schema.org/draft/2020-12/schema",
      ],
      homepage: "https://bowtie.report/",
      issues: "https://github.com/bowtie-json-schema/bowtie/issues",
      source: "https://github.com/bowtie-json-schema/bowtie",
    });

    expect(implementation.dialects).toStrictEqual([
      Dialect.withName("draft2020-12"),
    ]);
  });
});

describe("Dialect.isPrerelease", () => {
  test("is true for a dialect still being written", () => {
    expect(Dialect.isPrerelease("https://json-schema.org/v1")).toBe(true);
  });

  test("is false for a published dialect", () => {
    expect(
      Dialect.isPrerelease("https://json-schema.org/draft/2020-12/schema"),
    ).toBe(false);
  });

  test("is false for a dialect Bowtie does not know", () => {
    expect(Dialect.isPrerelease("https://example.com/not-a-dialect")).toBe(
      false,
    );
  });
});
