export const parseReportWithDiff = (
  lines: Record<string, unknown>[],
  prev_lines: Record<string, unknown>[],
): ReportData => {
  let curParsedReport = parseReportData(lines);
  let prevParsedReport = parseReportData(prev_lines);
  curParsedReport.implementations.forEach((value, key) => {
    value.isNew = !prevParsedReport.implementations.has(key);
  });
  return curParsedReport;
};

export const parseReportData = (
  lines: Record<string, unknown>[],
): ReportData => {
  const runInfoData = lines[0] as unknown as RunInfo;
  const implementationEntries = Object.entries(runInfoData.implementations);

  implementationEntries.sort(([id1], [id2]) => id1.localeCompare(id2));
  const caseMap = new Map() as Map<number, Case>;
  const implementationMap = new Map() as Map<string, ImplementationData>;
  implementationEntries.forEach(([id, metadata]) =>
    implementationMap.set(id, {
      id,
      metadata,
      cases: new Map(),
      erroredCases: 0,
      skippedTests: 0,
      failedTests: 0,
      erroredTests: 0,
    }),
  );

  let didFailFast = false;
  for (const line of lines) {
    if (line.case) {
      caseMap.set(line.seq as number, line.case as Case);
    } else if (line.implementation) {
      const caseData = caseMap.get(line.seq as number)!;
      const implementationData = implementationMap.get(
        line.implementation as string,
      )!;
      if (line.caught !== undefined) {
        const context = line.context as Record<string, unknown>;
        const errorMessage: string = (context?.message ??
          context?.stderr) as string;
        implementationData.erroredCases++;
        implementationData.erroredTests += caseData.tests.length;
        implementationData.cases.set(
          line.seq as number,
          new Array<CaseResult>(caseData.tests.length).fill({
            state: "errored",
            message: errorMessage,
          }),
        );
      } else if (line.skipped) {
        implementationData.skippedTests += caseData.tests.length;
        implementationData.cases.set(
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
            implementationData.erroredTests++;
            return {
              state: "errored",
              message: errorMessage as string | undefined,
            };
          } else if (res.skipped) {
            implementationData.skippedTests++;
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
              implementationData.failedTests++;
              return {
                state: "failed",
                valid: res.valid as boolean | undefined,
              };
            }
          }
        });
        implementationData.cases.set(line.seq as number, caseResults);
      } else if (line.did_fail_fast !== undefined) {
        didFailFast = line.did_fail_fast as boolean;
      }
    }
  }

  return {
    runInfo: runInfoData,
    cases: caseMap,
    implementations: implementationMap,
    didFailFast: didFailFast,
  };
};

export const parseImplementationData = (
  loaderData: Record<string, ReportData>,
) => {
  let allImplementations: Record<string, Implementation> = {};
  const dialectCompliance: Record<string, Record<string, Partial<Totals>>> = {};

  for (const [key, value] of Object.entries(loaderData)) {
    dialectCompliance[key] = calculateImplementationTotal(
      value.implementations,
    );
    allImplementations = {
      ...allImplementations,
      ...value.runInfo.implementations,
    };
  }

  Object.keys(allImplementations).map((implementation) => {
    Object.entries(dialectCompliance).map(([key, value]) => {
      if (value[implementation]) {
        if (
          !Object.prototype.hasOwnProperty.call(
            allImplementations[implementation],
            "results",
          )
        ) {
          allImplementations[implementation].results = {};
        }
        allImplementations[implementation].results[key] = value[implementation];
      }
    });
  });
  return allImplementations;
};

const calculateImplementationTotal = (
  implementations: Map<string, ImplementationData>,
) => {
  const implementationResult: Record<string, Partial<Totals>> = {};

  Array.from(implementations.entries()).forEach(([key, value]) => {
    implementationResult[key] = {
      erroredTests: value.erroredTests,
      skippedTests: value.skippedTests,
      failedTests: value.failedTests,
    };
  });

  return implementationResult;
};

export const calculateTotals = (data: ReportData): Totals => {
  const totalTests = Array.from(data.cases.values()).reduce(
    (prev, curr) => prev + curr.tests.length,
    0,
  );
  return Array.from(data.implementations.values()).reduce(
    (prev, curr) => ({
      totalTests,
      erroredCases: prev.erroredCases + curr.erroredCases,
      skippedTests: prev.skippedTests + curr.skippedTests,
      failedTests: prev.failedTests + curr.failedTests,
      erroredTests: prev.erroredTests + curr.erroredTests,
    }),
    {
      totalTests: totalTests,
      erroredCases: 0,
      skippedTests: 0,
      failedTests: 0,
      erroredTests: 0,
    },
  );
};

export interface Totals {
  totalTests: number;
  erroredCases: number;
  skippedTests: number;
  failedTests: number;
  erroredTests: number;
}

export interface ReportData {
  runInfo: RunInfo;
  cases: Map<number, Case>;
  implementations: Map<string, ImplementationData>;
  didFailFast: boolean;
}

export interface RunInfo {
  started: string;
  bowtie_version: string;
  dialect: string;
  implementations: Record<string, Implementation>;
  metadata: Record<string, unknown>;
}

export interface ImplementationData {
  id: string;
  metadata: Implementation;
  cases: Map<number, CaseResult[]>;
  isNew?: Boolean;
  erroredCases: number;
  skippedTests: number;
  failedTests: number;
  erroredTests: number;
}

export interface CaseResult {
  state: "successful" | "failed" | "skipped" | "errored";
  valid?: boolean;
  message?: string;
}

export interface Implementation {
  language: string;
  name: string;
  version?: string;
  dialects: string[];
  homepage: string;
  documentation?: string;
  issues: string;
  source: string;
  image: string;
  links?: {
    description?: string;
    url?: string;
    [k: string]: unknown;
  }[];
  os?: string;
  os_version?: string;
  language_version?: string;
  results: Record<string, Partial<Totals>>;

  [k: string]: unknown;
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
