import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";

import Dialect from "./Dialect";
import Implementation, { RawImplementationData } from "./Implementation";

dayjs.extend(relativeTime);

/**
 * Parse a report from some JSONL data.
 */
export const fromSerialized = (jsonl: string): ReportData => {
  const lines = jsonl.trim().split(/\r?\n/);
  return parseReportData(
    lines.map((line) => JSON.parse(line) as Record<string, unknown>),
  );
};

/**
 * Metadata about a report which has been run.
 */
export class RunMetadata {
  readonly dialect: Dialect;
  readonly implementations: Map<string, Implementation>;
  readonly bowtieVersion: string;
  readonly started: Date;
  readonly metadata: Record<string, unknown>;

  constructor(
    dialect: Dialect,
    implementations: Map<string, Implementation>,
    bowtieVersion: string,
    started: Date,
    metadata: Record<string, unknown>,
  ) {
    this.dialect = dialect;
    this.implementations = implementations;
    this.bowtieVersion = bowtieVersion;
    this.started = started;
    this.metadata = metadata;
  }

  ago(): string {
    return dayjs(this.started).fromNow();
  }

  static fromRecord(record: Header): RunMetadata {
    const implementations = new Map<string, Implementation>(
      Object.entries(record.implementations).map(([id, rawData]) => [
        id,
        Implementation.withId(id) ?? new Implementation(id, rawData),
      ]),
    );

    return new RunMetadata(
      Dialect.forURI(record.dialect),
      implementations,
      record.bowtie_version,
      new Date(record.started),
      record.metadata,
    );
  }
}

/**
 * Parse a report from some deserialized JSON objects.
 */
export const parseReportData = (
  lines: Record<string, unknown>[],
): ReportData => {
  const runMetadata = RunMetadata.fromRecord(lines[0] as unknown as Header);

  const implementationsResultsMap = new Map<string, ImplementationResults>();
  for (const id of runMetadata.implementations.keys()) {
    implementationsResultsMap.set(id, {
      caseResults: new Map(),
      totals: {
        skippedTests: 0,
        failedTests: 0,
        erroredTests: 0,
      },
    });
  }

  const caseMap = new Map<number, Case>();
  let didFailFast = false;
  for (const line of lines) {
    if (line.case) {
      caseMap.set(line.seq as number, line.case as Case);
    } else if (line.implementation) {
      const caseData = caseMap.get(line.seq as number)!;
      const implementationResults = implementationsResultsMap.get(
        line.implementation as string,
      )!;
      if (line.caught !== undefined) {
        const context = line.context as Record<string, unknown>;
        const errorMessage: string = (context?.message ??
          context?.stderr) as string;
        implementationResults.totals.erroredTests! += caseData.tests.length;
        implementationResults.caseResults.set(
          line.seq as number,
          new Array<CaseResult>(caseData.tests.length).fill({
            state: "errored",
            message: errorMessage,
          }),
        );
      } else if (line.skipped) {
        implementationResults.totals.skippedTests! += caseData.tests.length;
        implementationResults.caseResults.set(
          line.seq as number,
          new Array<CaseResult>(caseData.tests.length).fill({
            state: "skipped",
            message: line.message as string,
          }),
        );
      } else if (line.implementation) {
        const caseResults: CaseResult[] = (
          line.results as Record<string, unknown>[]
        ).map((res, idx) => {
          if (res.errored) {
            const context = res.context as Record<string, unknown>;
            const errorMessage = context?.message ?? context?.stderr;
            implementationResults.totals.erroredTests!++;
            return {
              state: "errored",
              message: errorMessage as string | undefined,
            };
          } else if (res.skipped) {
            implementationResults.totals.skippedTests!++;
            return {
              state: "skipped",
              message: res.message as string | undefined,
            };
          } else {
            const successful = res.valid === caseData.tests[idx].valid;
            if (successful) {
              return {
                state: "successful",
                valid: res.valid as boolean | undefined,
              };
            } else {
              implementationResults.totals.failedTests!++;
              return {
                state: "failed",
                valid: res.valid as boolean | undefined,
              };
            }
          }
        });
        implementationResults.caseResults.set(line.seq as number, caseResults);
      } else if (line.did_fail_fast !== undefined) {
        didFailFast = line.did_fail_fast as boolean;
      }
    }
  }

  return {
    runMetadata: runMetadata,
    cases: caseMap,
    implementationsResults: implementationsResultsMap,
    didFailFast: didFailFast,
  };
};

/**
 * Prepare a dialects compliance report for the passed
 * implementation id using all the dialect reports data
 * that was fetched.
 */
export const prepareDialectsComplianceReportFor = (
  implementationId: string,
  allDialectReports: Map<Dialect, ReportData>,
): ImplementationReport["dialectsCompliance"] => {
  const dialectsCompliance: ImplementationReport["dialectsCompliance"] =
    new Map();

  for (const [
    dialect,
    { implementationsResults },
  ] of allDialectReports.entries()) {
    const implementationResults = implementationsResults.get(implementationId);
    if (implementationResults) {
      dialectsCompliance.set(dialect, implementationResults.totals);
    }
  }

  return dialectsCompliance;
};

export const calculateTotals = (data: ReportData): Totals => {
  const totalTests = Array.from(data.cases.values()).reduce(
    (prev, curr) => prev + curr.tests.length,
    0,
  );
  return Array.from(data.implementationsResults.values()).reduce(
    (prev, curr) => ({
      totalTests,
      skippedTests: prev.skippedTests + curr.totals.skippedTests!,
      failedTests: prev.failedTests + curr.totals.failedTests!,
      erroredTests: prev.erroredTests + curr.totals.erroredTests!,
    }),
    {
      totalTests: totalTests,
      skippedTests: 0,
      failedTests: 0,
      erroredTests: 0,
    },
  );
};

interface Header {
  dialect: string;
  bowtie_version: string;
  metadata: Record<string, unknown>;
  implementations: Record<string, RawImplementationData>;
  started: number;
}

export interface Totals {
  totalTests: number;
  skippedTests: number;
  failedTests: number;
  erroredTests: number;
}

export interface ReportData {
  runMetadata: RunMetadata;
  cases: Map<number, Case>;
  implementationsResults: Map<string, ImplementationResults>;
  didFailFast: boolean;
}

export interface ImplementationResults {
  caseResults: Map<number, CaseResult[]>;
  totals: Partial<Totals>;
}

export interface CaseResult {
  state: "successful" | "failed" | "skipped" | "errored";
  valid?: boolean;
  message?: string;
}

export interface ImplementationReport {
  implementation: Implementation;
  dialectsCompliance: Map<Dialect, Partial<Totals>>;
}

export interface Case {
  description: string;
  comment?: string;
  schema: Record<string, unknown> | boolean;
  registry?: Record<string, unknown>;
  tests: [Test, ...Test[]];
}

export interface Test {
  description: string;
  comment?: string;
  instance: unknown;
  valid?: boolean;
}
