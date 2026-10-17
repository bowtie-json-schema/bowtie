import { describe, expect, test } from "vitest";

import type { RealWorldData, SchemaResult } from "../data/realWorldBenchmarks";
import {
  MetricTable,
  bestWord,
  formatRatio,
  formatValue,
  geomean,
  headToHead,
  rank,
  ratio,
  ratioIntensity,
  ratioTicks,
  spread,
  summarise,
  thin,
} from "./realWorldModel";

/** Runs with the given warm figures; the other measures are 10 each, so parse + warm is warm + 10. */
function runs(...warm: number[]): SchemaResult {
  const ten = warm.map(() => 10);
  return { warm, cold: ten, compile: ten, parse: ten, memory: ten };
}

const data: RealWorldData = {
  version: 1,
  meta: { repo: "sourcemeta-research/jsonschema-benchmark", runs: 3 },
  impls: [
    { id: "a", name: "a", lang: "Rust", version: "1", bowtie: "rust-a" },
    { id: "b", name: "b", lang: "Go", version: "1", bowtie: null },
    { id: "c", name: "c", lang: "C", version: "1", bowtie: "c-c" },
  ],
  schemas: [
    { name: "one", dialect: "http://json-schema.org/draft-07/schema#" },
    { name: "two", dialect: "http://json-schema.org/draft-07/schema#" },
  ],
  results: {
    // a is fastest on one, b on two; c fails two
    a: { one: runs(100, 300, 200), two: runs(400, 400, 400) },
    b: { one: runs(400, 400, 400), two: runs(100, 100, 100) },
    c: { one: runs(800, 800, 800), two: null },
  },
};

const all = ["a", "b", "c"];

describe("MetricTable", () => {
  test("takes the median of the runs, with their range", () => {
    expect(new MetricTable(data, "warm").get("a", "one")).toStrictEqual({
      state: "ok",
      median: 200,
      min: 100,
      max: 300,
      runs: [100, 200, 300],
    });
  });

  test("adds the measures of a combined metric run by run", () => {
    const cell = new MetricTable(data, "warmParse").get("a", "one");
    expect(cell.state === "ok" && cell.median).toBe(210);
  });

  test("reports a failed run and a schema that was not run", () => {
    const table = new MetricTable(data, "warm");
    expect(table.get("c", "two")).toStrictEqual({ state: "failed" });
    expect(table.get("c", "three")).toStrictEqual({ state: "missing" });
  });

  test("takes the mean of the middle two of an even number of runs", () => {
    const even: RealWorldData = { ...data, results: { a: { one: runs(100, 200, 300, 900) } } };
    const cell = new MetricTable(even, "warm").get("a", "one");
    expect(cell.state === "ok" && cell.median).toBe(250);
  });
});

describe("ratios", () => {
  const table = new MetricTable(data, "warm");

  test("against the fastest selected implementation on each schema", () => {
    expect(ratio(table, "b", "one", "fastest", all)).toBe(2);
    expect(ratio(table, "a", "one", "fastest", all)).toBe(1);
  });

  test("against the fastest of a narrower selection", () => {
    expect(ratio(table, "c", "one", "fastest", ["b", "c"])).toBe(2);
  });

  test("against one implementation", () => {
    expect(ratio(table, "b", "two", "a", all)).toBe(0.25);
  });

  test("is not a number when either side has no result", () => {
    expect(ratio(table, "c", "two", "fastest", all)).toBeNaN();
    expect(ratio(table, "a", "two", "c", all)).toBeNaN();
  });
});

describe("summarise and rank", () => {
  const table = new MetricTable(data, "warm");

  test("averages the ratios geometrically and counts the schemas", () => {
    // a: 1 on one, 4 on two; b: 2 on one, 1 on two
    const a = summarise(table, data.schemas, "a", "fastest", all);
    expect(a.geomean).toBeCloseTo(2);
    expect([a.compared, a.failed, a.missing, a.fastestOn]).toStrictEqual([2, 0, 0, 1]);
    const c = summarise(table, data.schemas, "c", "fastest", all);
    expect(c.geomean).toBeCloseTo(4);
    expect([c.compared, c.failed]).toStrictEqual([1, 1]);
  });

  test("ranks the selection best first", () => {
    expect(rank(table, data.schemas, "fastest", all, (id) => id).map((s) => s.impl)).toStrictEqual(["b", "a", "c"]);
  });
});

test("headToHead compares the schemas both complete", () => {
  const result = headToHead(new MetricTable(data, "warm"), data.schemas, "a", "c");
  expect(result.points).toStrictEqual([{ schema: "one", ratio: 0.25, a: 200, b: 800 }]);
  expect([result.aWins, result.aFailed, result.bFailed]).toStrictEqual([1, 0, 1]);
  expect(result.geomean).toBeCloseTo(0.25);
});

test("spread is the slowest over the fastest of the selection", () => {
  expect(spread(new MetricTable(data, "warm"), "one", all)).toBe(4);
});

test("geomean of nothing is not a number", () => {
  expect(geomean([])).toBeNaN();
});

describe("formatting", () => {
  test("values in the largest unit below them", () => {
    expect(formatValue(950)).toBe("950 ns");
    expect(formatValue(20_700)).toBe("20.7 µs");
    expect(formatValue(1_234_000)).toBe("1.23 ms");
    expect(formatValue(2048, true)).toBe("2.00 MB");
  });

  test("ratios in words that say which way they go", () => {
    expect(formatRatio(0.5, "warm", "b")).toBe("2.00× faster");
    expect(formatRatio(3, "memory", "b")).toBe("3.00× larger");
    expect(formatRatio(1.07, "warm", "fastest")).toBe("1.07× the fastest");
    expect(formatRatio(1, "warm", "fastest")).toBe("fastest");
  });

  test("memory is compared by how little it uses", () => {
    expect(formatRatio(1.5, "memory", "fastest")).toBe("1.50× the lowest memory");
    expect(formatRatio(1, "memory", "fastest")).toBe("lowest memory");
    expect(bestWord("memory")).toBe("lowest memory");
    expect(bestWord("warmParse")).toBe("fastest");
  });
});

describe("scales", () => {
  test("ratio ticks are powers of two, at most eight", () => {
    expect(ratioTicks(1, 8)).toStrictEqual([1, 2, 4, 8]);
    expect(ratioTicks(1, 2 ** 20).length).toBeLessThanOrEqual(11);
  });

  test("thin keeps ticks a gap apart", () => {
    expect(thin([0, 10, 70, 80, 140], (v) => v)).toStrictEqual([0, 70, 140]);
  });

  test("intensity saturates at 16× against an implementation and 64× against the fastest", () => {
    expect(ratioIntensity(16, "a")).toBe(1);
    expect(ratioIntensity(1 / 32, "a")).toBe(-1);
    expect(ratioIntensity(8, "fastest")).toBe(0.5);
  });
});
