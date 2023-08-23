export const parseReportData = (lines: any[]): ReportData => {
  const runInfoData = lines[0] as RunInfo;
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
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];

    if (line.case) {
      caseMap.set(line.seq, line.case as Case);
    } else if (line.implementation) {
      const caseData = caseMap.get(line.seq)!;
      const implementationData = implementationMap.get(line.implementation)!;
      if (line.caught !== undefined) {
        const errorMessage = line.context?.message ?? line.context?.stderr;
        implementationData.erroredCases++;
        implementationData.erroredTests += caseData.tests.length;
        implementationData.cases.set(
          line.seq,
          new Array(caseData.tests.length).fill({
            state: "errored",
            message: errorMessage,
          }),
        );
      } else if (line.skipped) {
        implementationData.skippedTests += caseData.tests.length;
        implementationData.cases.set(
          line.seq,
          new Array(caseData.tests.length).fill({
            state: "skipped",
            message: line.message,
          }),
        );
      } else if (line.implementation) {
        const caseResults = (line.results as any[]).map<CaseResult>(
          (res, idx) => {
            if (res.errored) {
              const errorMessage = res.context?.message ?? res.context?.stderr;
              implementationData.erroredTests++;
              return { state: "errored", message: errorMessage };
            } else if (res.skipped) {
              implementationData.skippedTests++;
              return { state: "skipped", message: res.message };
            } else {
              const successful = res.valid === caseData.tests[idx].valid;
              if (successful) {
                return { state: "successful", valid: res.valid };
              } else {
                implementationData.failedTests++;
                return { state: "failed", valid: res.valid };
              }
            }
          },
        );
        implementationData.cases.set(line.seq, caseResults);
      } else if (line.did_fail_fast !== undefined) {
        didFailFast = line.did_fail_fast;
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

export const parseImplementationData = (loaderData: {
  [key: string]: ReportData;
}) => {
  let allImplementations: { [key: string]: ImplementationMetadata } = {};
  let dialectCompliance: { [key: string]: { [key: string]: Partial<Totals> } } =
    {};

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
        if (!allImplementations[implementation].hasOwnProperty("results")) {
          allImplementations[implementation]["results"] = {};
        }
        allImplementations[implementation]["results"][key] =
          value[implementation];
      }
    });
  });
  return allImplementations;
};

const calculateImplementationTotal = (
  implementations: Map<string, ImplementationData>,
) => {
  let implementationResult: { [key: string]: Partial<Totals> } = {};

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
  implementations: Record<string, ImplementationMetadata>;
  metadata: any;
}

export interface ImplementationData {
  id: string;
  metadata: ImplementationMetadata;
  cases: Map<number, CaseResult[]>;
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

export interface ImplementationMetadata {
  language: string;
  name: string;
  version?: string;
  dialects: string[];
  homepage: string;
  issues: string;
  image: string;
  links?: {
    description?: string;
    url?: string;
    [k: string]: unknown;
  }[];
  os?: string;
  os_version?: string;
  language_version?: string;
  results: { [key: string]: Partial<Totals> };

  [k: string]: unknown;
}

export interface Case {
  description: string;
  comment?: string;
  schema: {
    [k: string]: unknown;
  };
  registry?: {
    [k: string]: unknown;
  };
  tests: [Test, ...Test[]];
}

export interface Test {
  description: string;
  comment?: string;
  instance: any;
  valid?: boolean;
}
