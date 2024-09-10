import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import { prod, nthRoot } from "mathjs";
import Dialect from "./Dialect";
import Implementation, { RawImplementationData } from "./Implementation";

dayjs.extend(relativeTime);

/**
 * Parse a Benchmark Report from some JSON data.
 */
export const fromJSON = (json_data: string): BenchmarkReportData => {
  const json = JSON.parse(json_data) as Record<string, unknown>;
  return {
    metadata: parseBenchmarkMetadata(json.metadata as Record<string, unknown>),
    results: parseBenchmarkResults(json.results as Record<string, unknown>[]),
  };
};

const parseBenchmarkMetadata = (rawMetadata: Record<string, unknown>) => {
  const system_metadata = rawMetadata.system_metadata as Record<
    string,
    unknown
  >;

  const dialect = Dialect.forURI(rawMetadata.dialect as string);
  const started = new Date(rawMetadata.started as string);
  const implementations = new Map<string, Implementation>(
    Object.entries(
      rawMetadata.implementations as Record<string, RawImplementationData>,
    ).map(([id, info]) => [id, new Implementation(id, info)]),
  );

  const systemMetadata: BenchmarkSystemMetadata = {
    bootTime: new Date(system_metadata.boot_time as string),
    hostname: system_metadata.hostname as string,
    loops: system_metadata.loops as number,
    perfVersion: system_metadata.perf_version as string,
    platform: system_metadata.platform as string,
    unit: system_metadata.unit as string,
    cpuCount: (system_metadata.cpu_count as number) ?? undefined,
    cpuModel: (system_metadata.cpu_model as string) ?? undefined,
    cpuFreq: (system_metadata.cpu_freq as string) ?? undefined,
  };

  return new BenchmarkRunMetadata(
    dialect,
    implementations,
    rawMetadata.bowtie_version as string,
    started,
    systemMetadata,
  );
};

const parseBenchmarkResults = (rawResults: Record<string, unknown>[]) => {
  const benchmarkGroupResults: BenchmarkGroupResult[] = [];

  rawResults.forEach((benchmarkGroupResult) => {
    const benchmarkResults: BenchmarkResult[] = [];

    (
      benchmarkGroupResult.benchmark_results as Record<string, unknown>[]
    ).forEach((benchmarkResult) => {
      const testResults: TestResult[] = [];

      (benchmarkResult.test_results as Record<string, unknown>[]).forEach(
        (testResult) => {
          const implementationResults: ImplementationResult[] = [];

          (testResult.connectable_results as Record<string, unknown>[]).forEach(
            (implementationResult) => {
              implementationResults.push({
                implementationId: implementationResult.connectable_id as string,
                duration: implementationResult.duration as number,
                errored: implementationResult.errored as boolean,
                values: implementationResult.values as number[],
              });
            },
          );
          testResults.push({
            description: testResult.description as string,
            implementationResults: implementationResults,
          });
        },
      );

      benchmarkResults.push({
        name: benchmarkResult.name as string,
        description: benchmarkResult.description as string,
        testResults: testResults,
      });
    });

    benchmarkGroupResults.push({
      name: benchmarkGroupResult.name as string,
      description: benchmarkGroupResult.description as string,
      benchmarkResults: benchmarkResults,
      benchmarkType: benchmarkGroupResult.benchmark_type as string,
      varyingParameter:
        (benchmarkGroupResult.varying_parameter as string) || undefined,
    });
  });

  return benchmarkGroupResults;
};

export interface BenchmarkReportData {
  metadata: BenchmarkRunMetadata;
  results: BenchmarkGroupResult[];
}

/**
 * Metadata about a Benchmark Report which has been run.
 */
export class BenchmarkRunMetadata {
  readonly dialect: Dialect;
  readonly implementations: Map<string, Implementation>;
  readonly bowtieVersion: string;
  readonly started: Date;
  readonly systemMetadata: BenchmarkSystemMetadata;

  constructor(
    dialect: Dialect,
    implementations: Map<string, Implementation>,
    bowtieVersion: string,
    started: Date,
    systemMetadata: BenchmarkSystemMetadata,
  ) {
    this.dialect = dialect;
    this.implementations = implementations;
    this.bowtieVersion = bowtieVersion;
    this.started = started;
    this.systemMetadata = systemMetadata;
  }

  ago(): string {
    return dayjs(this.started).fromNow();
  }
}

export interface BenchmarkSystemMetadata {
  bootTime: Date;
  cpuCount?: number;
  cpuFreq?: string;
  cpuModel?: string;
  hostname?: string;
  loops: number;
  perfVersion: string;
  platform: string;
  unit: string;
}

export interface BenchmarkGroupResult {
  name: string;
  description: string;
  benchmarkResults: BenchmarkResult[];
  benchmarkType: string;
  varyingParameter?: string;
}

export interface BenchmarkResult {
  name: string;
  description: string;
  testResults: TestResult[];
}

export interface TestResult {
  description: string;
  implementationResults: ImplementationResult[];
}

export interface ImplementationResult {
  duration: number;
  errored: boolean;
  values: number[];
  implementationId: string;
}

export function geometricMean(values: number[]): number {
  if (values.length == 0) {
    return 1e9;
  }
  const prodOfMeans = prod(values);
  const geometricMean = nthRoot(prodOfMeans, values.length);
  return geometricMean as number;
}
