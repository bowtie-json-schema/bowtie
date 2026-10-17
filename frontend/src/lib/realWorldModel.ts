import type { Measure, RealWorldData, RealWorldSchema } from "../data/realWorldBenchmarks";

export type MetricKey = "warm" | "warmParse" | "cold" | "coldParse" | "compile" | "startup" | "parse" | "memory";

export interface Metric {
  label: string;
  /** used in sentences: "on warm validation" */
  long: string;
  /** the measures summed, run by run */
  parts: Measure[];
  /** memory is in KB and compared as smaller/larger rather than faster/slower */
  kb?: boolean;
}

export const METRICS: Record<MetricKey, Metric> = {
  warm: { label: "Warm", long: "warm validation", parts: ["warm"] },
  warmParse: { label: "Parse + warm", long: "parse and warm validation", parts: ["parse", "warm"] },
  cold: { label: "Cold", long: "cold validation", parts: ["cold"] },
  coldParse: { label: "Parse + cold", long: "parse and cold validation", parts: ["parse", "cold"] },
  compile: { label: "Compile", long: "schema compilation", parts: ["compile"] },
  startup: {
    label: "Compile + parse + cold",
    long: "compile, parse and cold validation",
    parts: ["compile", "parse", "cold"],
  },
  parse: { label: "Parse", long: "instance parsing", parts: ["parse"] },
  memory: { label: "Peak memory", long: "peak memory", parts: ["memory"], kb: true },
};

export type Cell =
  | { state: "ok"; median: number; min: number; max: number; runs: number[] }
  | { state: "failed" }
  | { state: "missing" };

/** Compare with one implementation, or with the fastest selected implementation on each schema. */
export type Baseline = "fastest" | string;

/** The median, range and runs of one metric for every implementation and schema. */
export class MetricTable {
  private readonly cells = new Map<string, Cell>();

  constructor(
    readonly data: RealWorldData,
    readonly metric: MetricKey,
  ) {}

  get(impl: string, schema: string): Cell {
    const key = `${impl}\u0000${schema}`;
    let cell = this.cells.get(key);
    if (!cell) {
      cell = measure(this.data, impl, schema, this.metric);
      this.cells.set(key, cell);
    }
    return cell;
  }
}

export function measure(data: RealWorldData, impl: string, schema: string, metric: MetricKey): Cell {
  const result = data.results[impl]?.[schema];
  if (result === undefined) return { state: "missing" };
  if (result === null) return { state: "failed" };
  const parts = METRICS[metric].parts;
  const runs = result[parts[0]]
    .map((_, i) => parts.reduce((sum, part) => sum + result[part][i], 0))
    .sort((x, y) => x - y);
  if (runs.length === 0) return { state: "missing" };
  const mid = runs.length >> 1;
  const median = runs.length % 2 ? runs[mid] : (runs[mid - 1] + runs[mid]) / 2;
  // A zero is how a run reports that it could not measure; the benchmark treats it as a failure.
  return median > 0 ? { state: "ok", median, min: runs[0], max: runs[runs.length - 1], runs } : { state: "failed" };
}

export function geomean(values: number[]): number {
  return values.length ? Math.exp(values.reduce((sum, v) => sum + Math.log(v), 0) / values.length) : NaN;
}

export function baseValue(table: MetricTable, schema: string, baseline: Baseline, selected: string[]): number {
  if (baseline !== "fastest") {
    const cell = table.get(baseline, schema);
    return cell.state === "ok" ? cell.median : NaN;
  }
  let best = Infinity;
  for (const id of selected) {
    const cell = table.get(id, schema);
    if (cell.state === "ok" && cell.median < best) best = cell.median;
  }
  return best === Infinity ? NaN : best;
}

export function ratio(table: MetricTable, impl: string, schema: string, baseline: Baseline, selected: string[]): number {
  const cell = table.get(impl, schema);
  const base = baseValue(table, schema, baseline, selected);
  return cell.state === "ok" && base > 0 ? cell.median / base : NaN;
}

export interface Summary {
  impl: string;
  /** geometric mean of the per-schema ratios */
  geomean: number;
  /** schemas compared */
  compared: number;
  failed: number;
  missing: number;
  /** schemas on which it is the fastest of the selection */
  fastestOn: number;
}

export function summarise(
  table: MetricTable,
  schemas: RealWorldSchema[],
  impl: string,
  baseline: Baseline,
  selected: string[],
): Summary {
  const ratios: number[] = [];
  let failed = 0;
  let missing = 0;
  let fastestOn = 0;
  for (const { name } of schemas) {
    const cell = table.get(impl, name);
    if (cell.state === "failed") failed++;
    else if (cell.state === "missing") missing++;
    const r = ratio(table, impl, name, baseline, selected);
    if (Number.isFinite(r)) ratios.push(r);
    if (cell.state === "ok") {
      const beaten = selected.some((other) => {
        const o = table.get(other, name);
        return other !== impl && o.state === "ok" && o.median < cell.median;
      });
      if (!beaten) fastestOn++;
    }
  }
  return { impl, geomean: geomean(ratios), compared: ratios.length, failed, missing, fastestOn };
}

/** The selection, best first; implementations with nothing to compare come last. */
export function rank(
  table: MetricTable,
  schemas: RealWorldSchema[],
  baseline: Baseline,
  selected: string[],
  nameOf: (id: string) => string,
): Summary[] {
  const order = (s: Summary) => (Number.isFinite(s.geomean) ? s.geomean : Infinity);
  return selected
    .map((impl) => summarise(table, schemas, impl, baseline, selected))
    .sort((a, b) => order(a) - order(b) || nameOf(a.impl).localeCompare(nameOf(b.impl)));
}

export interface Comparison {
  schema: string;
  /** a's median over b's: below 1 means a is better */
  ratio: number;
  a: number;
  b: number;
}

export interface HeadToHead {
  points: Comparison[];
  /** schemas on which a is better */
  aWins: number;
  geomean: number;
  aFailed: number;
  bFailed: number;
}

export function headToHead(table: MetricTable, schemas: RealWorldSchema[], a: string, b: string): HeadToHead {
  const points: Comparison[] = [];
  let aFailed = 0;
  let bFailed = 0;
  for (const { name } of schemas) {
    const ca = table.get(a, name);
    const cb = table.get(b, name);
    if (ca.state !== "ok") aFailed++;
    if (cb.state !== "ok") bFailed++;
    if (ca.state === "ok" && cb.state === "ok") {
      points.push({ schema: name, ratio: ca.median / cb.median, a: ca.median, b: cb.median });
    }
  }
  points.sort((p, q) => p.ratio - q.ratio);
  return {
    points,
    aWins: points.filter((p) => p.ratio < 1).length,
    geomean: geomean(points.map((p) => p.ratio)),
    aFailed,
    bFailed,
  };
}

/** The largest per-schema ratio between the slowest and fastest of the selection, for ordering schemas by spread. */
export function spread(table: MetricTable, schema: string, selected: string[]): number {
  const medians = selected
    .map((id) => table.get(id, schema))
    .flatMap((cell) => (cell.state === "ok" ? [cell.median] : []));
  return medians.length > 1 ? Math.max(...medians) / Math.min(...medians) : 0;
}

/* ---------- formatting ---------- */

export function significant(x: number): string {
  return x >= 100 ? x.toFixed(0) : x >= 10 ? x.toFixed(1) : x.toFixed(2);
}

export function formatValue(value: number, kb = false): string {
  if (!Number.isFinite(value)) return "–";
  if (kb) {
    if (value < 1024) return `${significant(value)} KB`;
    if (value < 1048576) return `${significant(value / 1024)} MB`;
    return `${significant(value / 1048576)} GB`;
  }
  if (value < 1e3) return `${significant(value)} ns`;
  if (value < 1e6) return `${significant(value / 1e3)} µs`;
  if (value < 1e9) return `${significant(value / 1e6)} ms`;
  return `${significant(value / 1e9)} s`;
}

export const betterWord = (metric: MetricKey) => (METRICS[metric].kb ? "smaller" : "faster");
export const worseWord = (metric: MetricKey) => (METRICS[metric].kb ? "larger" : "slower");

/** "2.31× slower" against an implementation, or "2.31× the fastest" against the fastest on each schema. */
export function formatRatio(r: number, metric: MetricKey, baseline: Baseline): string {
  if (!Number.isFinite(r)) return "–";
  if (baseline === "fastest") return Math.abs(r - 1) < 0.005 ? "fastest" : `${significant(r)}× the fastest`;
  if (Math.abs(r - 1) < 0.005) return "level";
  return r < 1 ? `${significant(1 / r)}× ${betterWord(metric)}` : `${significant(r)}× ${worseWord(metric)}`;
}

/* ---------- scales ---------- */

/** Powers of two that cover [lo, hi], thinned so there are at most eight. */
export function ratioTicks(lo: number, hi: number): number[] {
  const k0 = Math.floor(Math.log2(lo));
  const k1 = Math.ceil(Math.log2(hi));
  let step = 1;
  while ((k1 - k0) / step > 8) step *= 2;
  const ticks: number[] = [];
  for (let k = Math.ceil(k0 / step) * step; k <= k1; k += step) ticks.push(2 ** k);
  return ticks;
}

export const ratioTickLabel = (t: number) => (t >= 1 ? `${significant(t)}×` : `1/${significant(1 / t)}`);

/** Powers of ten that cover [lo, hi], with 2 and 5 between them when the range is short. */
export function valueTicksLog(lo: number, hi: number): number[] {
  const ticks: number[] = [];
  const steps = Math.log10(hi / lo) < 2.5 ? [1, 2, 5] : [1];
  for (let e = Math.floor(Math.log10(lo)); e <= Math.ceil(Math.log10(hi)); e++) {
    for (const m of steps) {
      const v = m * 10 ** e;
      if (v >= lo * 0.999 && v <= hi * 1.001) ticks.push(v);
    }
  }
  return ticks;
}

export function valueTicksLinear(hi: number): number[] {
  const raw = hi / 5;
  const p = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * p).find((s) => s >= raw) ?? raw;
  const ticks: number[] = [];
  for (let v = 0; v <= hi * 1.0001; v += step) ticks.push(v);
  return ticks;
}

export function logScale(lo: number, hi: number, x0: number, x1: number) {
  const a = Math.log(lo);
  const b = Math.log(hi);
  return (v: number) => x0 + ((Math.log(v) - a) / (b - a)) * (x1 - x0);
}

/** Drops ticks that would sit closer than gap pixels to the last one kept, so labels never collide. */
export function thin(ticks: number[], x: (v: number) => number, gap = 64): number[] {
  const kept: number[] = [];
  for (const t of ticks) if (!kept.length || x(t) - x(kept[kept.length - 1]) >= gap) kept.push(t);
  return kept;
}

/**
 * How far a ratio sits from level, from -1 (16× better) through 0 to 1 (16× worse), on a log scale; against the
 * fastest on each schema, 64× saturates, as every ratio is at least 1.
 */
export function ratioIntensity(r: number, baseline: Baseline): number {
  const span = baseline === "fastest" ? 6 : 4;
  return Math.max(-1, Math.min(1, Math.log2(r) / span));
}
