import type Implementation from "../data/Implementation";
import {
  geometricMean,
  type BenchmarkGroupResult,
  type BenchmarkResult,
} from "../data/parseBenchmarkData";

/** Distinct benchmark types present in the results, in first-seen order. */
export function benchmarkTypes(groups: BenchmarkGroupResult[]): string[] {
  return [...new Set(groups.map((g) => g.benchmarkType))];
}

/** Distinct implementation languages, sorted. */
export function benchmarkLanguages(
  implementations: Map<string, Implementation>,
): string[] {
  return [...new Set([...implementations.values()].map((i) => i.language))].sort();
}

/** Human-friendly duration: µs / ms / s depending on magnitude. */
export function formatDuration(seconds: number): string {
  if (seconds * 1000 < 1) return `${Math.round(seconds * 1e6)}µs`;
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
  return `${seconds.toFixed(2)}s`;
}

const mean = (xs: number[]): number =>
  xs.length ? xs.reduce((s, x) => s + x, 0) / xs.length : 0;

/** Sample standard deviation (n-1). */
const std = (xs: number[]): number => {
  if (xs.length < 2) return 0;
  const m = mean(xs);
  return Math.sqrt(
    xs.reduce((s, x) => s + (x - m) ** 2, 0) / (xs.length - 1),
  );
};

export interface Ranking {
  id: string;
  geoMean: number;
}

/**
 * Overall ranking: the geometric mean of an implementation's per-test mean
 * durations across every benchmark, fastest first. Errored samples are
 * dropped. `scopedIds` limits which implementations are included.
 */
export function overallRanking(
  groups: BenchmarkGroupResult[],
  scopedIds: string[],
): Ranking[] {
  const scope = new Set(scopedIds);
  const perImpl = new Map<string, number[]>();
  for (const g of groups) {
    for (const b of g.benchmarkResults) {
      for (const t of b.testResults) {
        for (const r of t.implementationResults) {
          if (r.errored || !scope.has(r.implementationId)) continue;
          const acc = perImpl.get(r.implementationId) ?? [];
          acc.push(mean(r.values));
          perImpl.set(r.implementationId, acc);
        }
      }
    }
  }
  return [...perImpl.entries()]
    .map(([id, means]) => ({ id, geoMean: geometricMean(means) }))
    .sort((a, b) => a.geoMean - b.geoMean);
}

export interface BenchCell {
  mean: number;
  std: number;
  errored: boolean;
}

export interface BenchRow {
  id: string;
  cells: BenchCell[];
  geoMean: number;
}

export interface BenchTable {
  tests: string[];
  rows: BenchRow[];
}

/**
 * A single benchmark's table: implementations (rows) × varying-parameter tests
 * (columns), each cell the mean ± std of that sample. Rows are sorted by the
 * geometric mean of their non-errored means (fastest first). Implementation
 * results are assumed index-aligned across the benchmark's tests (as emitted).
 */
export function benchmarkTable(
  benchmark: BenchmarkResult,
  scopedIds: string[],
): BenchTable {
  const scope = new Set(scopedIds);
  const tests = benchmark.testResults.map((t) => t.description);
  const first = benchmark.testResults[0]?.implementationResults ?? [];

  const rows: BenchRow[] = first
    .map((_, idx) => {
      const id = first[idx].implementationId;
      const cells = benchmark.testResults.map((t) => {
        const r = t.implementationResults[idx];
        return { mean: mean(r.values), std: std(r.values), errored: r.errored };
      });
      const ok = cells.filter((c) => !c.errored).map((c) => c.mean);
      return { id, cells, geoMean: geometricMean(ok) };
    })
    .filter((row) => scope.has(row.id) && row.cells.some((c) => !c.errored))
    .sort((a, b) => a.geoMean - b.geoMean);

  return { tests, rows };
}
