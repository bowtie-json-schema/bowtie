import { describe, expect, test } from "vitest";

import Dialect from "./Dialect";
import { complianceBadgeURI, isFullyCompliant, parseComplianceBadge } from "./compliance";
import { RealWorldDataError, parseRealWorldData, realWorldDataURI } from "./realWorldBenchmarks";

const minimal = {
  version: 1,
  meta: { repo: "sourcemeta-research/jsonschema-benchmark", runs: 3 },
  impls: [],
  schemas: [],
  results: {},
};

describe("parseRealWorldData", () => {
  test("reads the version it supports", () => {
    expect(parseRealWorldData(JSON.stringify(minimal))).toStrictEqual(minimal);
  });

  test("refuses another version, saying which", () => {
    expect(() => parseRealWorldData(JSON.stringify({ ...minimal, version: 2 }))).toThrow(
      /format version 2; this page reads version 1/,
    );
  });

  test("refuses data without its parts", () => {
    const { results: _, ...partial } = minimal;
    expect(() => parseRealWorldData(JSON.stringify(partial))).toThrow(RealWorldDataError);
  });

  test("refuses text that is not JSON", () => {
    expect(() => parseRealWorldData("<html>")).toThrow(/not valid JSON/);
  });
});

describe("compliance badges", () => {
  test("read the percentage Bowtie truncates", () => {
    expect(parseComplianceBadge({ message: "100% Passing" })).toStrictEqual({ state: "tested", percent: 100 });
    expect(parseComplianceBadge({ message: "99% Passing" })).toStrictEqual({ state: "tested", percent: 99 });
  });

  test("an unreadable badge is unknown", () => {
    expect(parseComplianceBadge({ message: "passing" })).toStrictEqual({ state: "unknown" });
    expect(parseComplianceBadge(null)).toStrictEqual({ state: "unknown" });
  });

  test("only 100% is fully compliant", () => {
    expect(isFullyCompliant({ state: "tested", percent: 100 })).toBe(true);
    expect(isFullyCompliant({ state: "tested", percent: 99 })).toBe(false);
    expect(isFullyCompliant({ state: "unsupported" })).toBe(false);
    expect(isFullyCompliant(undefined)).toBe(false);
  });

  test("live beside the site's other badges", () => {
    expect(complianceBadgeURI("rust-boon", Dialect.withName("draft7")).href()).toMatch(
      /\/badges\/rust-boon\/compliance\/draft7\.json$/,
    );
  });
});

test("the data lives under the site's own path", () => {
  expect(realWorldDataURI().path()).toMatch(/\/jsonschema-benchmark\/data\.json$/);
});
