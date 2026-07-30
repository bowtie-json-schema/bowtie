import type { Case, CaseResult, ReportData } from "../data/parseReportData";

/**
 * A single implementation's outcome on a case or test, collapsed to the
 * "worst" observed state. Ordered by severity for ranking.
 */
export type Worst = "ok" | "skip" | "err" | "fail";

export const RANK: Record<Worst, number> = { ok: 0, skip: 1, err: 2, fail: 3 };

export const stateToWorst = (s: CaseResult["state"]): Worst =>
  s === "successful"
    ? "ok"
    : s === "skipped"
      ? "skip"
      : s === "errored"
        ? "err"
        : "fail";

export interface Counts {
  ok: number;
  fail: number;
  err: number;
  skip: number;
}

export const emptyCounts = (): Counts => ({ ok: 0, fail: 0, err: 0, skip: 0 });

/** The result a given implementation produced on a specific test of a case. */
export function resultFor(
  report: ReportData,
  implId: string,
  seq: number,
  testIdx: number,
): CaseResult {
  const results = report.implementationsResults.get(implId)?.caseResults.get(seq);
  return results?.[testIdx] ?? { state: "errored" };
}

/** The worst state an implementation reached across all tests of a case. */
export function worstFor(report: ReportData, implId: string, seq: number): Worst {
  const c = report.cases.get(seq)!;
  let worst: Worst = "ok";
  for (let t = 0; t < c.tests.length; t++) {
    const w = stateToWorst(resultFor(report, implId, seq, t).state);
    if (RANK[w] > RANK[worst]) worst = w;
  }
  return worst;
}

/**
 * Precompute every implementation's worst state per case, once, so the case
 * list's filtering/sorting stays cheap regardless of implementation count.
 */
export function computeWorst(
  report: ReportData,
): Map<number, Map<string, Worst>> {
  const out = new Map<number, Map<string, Worst>>();
  const implIds = [...report.runMetadata.implementations.keys()];
  for (const seq of report.cases.keys()) {
    const m = new Map<string, Worst>();
    for (const id of implIds) m.set(id, worstFor(report, id, seq));
    out.set(seq, m);
  }
  return out;
}

/** Tally the per-test outcomes across the given implementations. */
export function testCounts(
  report: ReportData,
  implIds: string[],
  seq: number,
  testIdx: number,
): Counts {
  const n = emptyCounts();
  for (const id of implIds) {
    n[stateToWorst(resultFor(report, id, seq, testIdx).state)]++;
  }
  return n;
}

export interface Failure {
  seq: number;
  caseDescription: string;
  testDescription: string;
  state: "failed" | "errored" | "skipped";
  message?: string;
  schema: Case["schema"];
  instance: unknown;
}

const FAILURE_ORDER = { failed: 0, errored: 1, skipped: 2 } as const;

/**
 * Every unsuccessful (case, test) an implementation produced in a report,
 * ordered failed → errored → skipped then by case sequence.
 */
export function failuresFor(report: ReportData, implId: string): Failure[] {
  const res = report.implementationsResults.get(implId);
  if (!res) return [];
  const out: Failure[] = [];
  for (const [seq, results] of res.caseResults) {
    const c = report.cases.get(seq);
    if (!c) continue;
    results.forEach((r, i) => {
      if (r.state === "successful") return;
      out.push({
        seq,
        caseDescription: c.description,
        testDescription: c.tests[i].description,
        state: r.state,
        message: r.message,
        schema: c.schema,
        instance: c.tests[i].instance,
      });
    });
  }
  return out.sort(
    (a, b) => FAILURE_ORDER[a.state] - FAILURE_ORDER[b.state] || a.seq - b.seq,
  );
}

/**
 * Grouping seam for issue #27 (case groups in the report format). Today the
 * report is flat, so this returns null and callers render ungrouped. When the
 * format carries a group/keyword, return it here and the case list groups for
 * free — no UI change required.
 */
export function caseGroup(_case: Case): string | null {
  return null;
}
