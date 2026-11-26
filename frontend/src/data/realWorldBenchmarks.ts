import URI from "urijs";

import siteURI from "./Site";

/**
 * The results of sourcemeta's jsonschema-benchmark: real-world schemas and instance sets, validated by each
 * implementation in its own container. `report.yml` copies the benchmark's latest `data.json` into the site; its
 * format is the JSON Schema at
 * https://github.com/sourcemeta-research/jsonschema-benchmark/blob/main/site/data.schema.json.
 */
export const BENCHMARK_REPOSITORY = "https://github.com/sourcemeta-research/jsonschema-benchmark";

/** The format version this page reads; the benchmark raises it when readers must change. */
export const SUPPORTED_VERSION = 1;

export interface RealWorldImplementation {
  /** its directory under the benchmark's implementations/ */
  id: string;
  name: string;
  /** the language of its source files; empty when unknown */
  lang: string;
  version: string;
  /** its Bowtie implementation ID, or null when Bowtie does not test it */
  bowtie: string | null;
}

export interface RealWorldSchema {
  name: string;
  /** the schema's $schema, or null when it declares none */
  dialect: string | null;
  docs?: number;
  sizeKb?: number;
  avgDoc?: number;
}

export type Measure = "cold" | "warm" | "compile" | "parse" | "memory";

/** One figure per run for each measure, or null when any run failed to validate an instance. */
export type SchemaResult = Record<Measure, number[]> | null;

export interface RealWorldData {
  version: number;
  meta: {
    repo: string;
    runUrl?: string;
    commit?: string;
    date?: string;
    runner?: string;
    runs: number;
  };
  impls: RealWorldImplementation[];
  schemas: RealWorldSchema[];
  results: Record<string, Record<string, SchemaResult>>;
}

export class RealWorldDataError extends Error {}

export function parseRealWorldData(text: string): RealWorldData {
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    throw new RealWorldDataError("The benchmark results are not valid JSON.");
  }
  if (typeof data !== "object" || data === null) {
    throw new RealWorldDataError("The benchmark results are not a JSON object.");
  }
  const candidate = data as Partial<RealWorldData>;
  if (candidate.version !== SUPPORTED_VERSION) {
    throw new RealWorldDataError(
      `The benchmark results are in format version ${String(candidate.version)}; this page reads version ${SUPPORTED_VERSION}.`,
    );
  }
  if (
    !Array.isArray(candidate.impls) ||
    !Array.isArray(candidate.schemas) ||
    typeof candidate.results !== "object" ||
    candidate.results === null ||
    typeof candidate.meta !== "object"
  ) {
    throw new RealWorldDataError("The benchmark results are missing their implementations, schemas or results.");
  }
  return candidate as RealWorldData;
}

/**
 * Where the site serves the results. In development the site's data comes from bowtie.report, which does not have
 * them until this page ships, and the benchmark's bucket allows no other origins, so the dev server proxies them
 * (see vite.config.ts).
 */
export function realWorldDataURI(): URI {
  if (import.meta.env.MODE === "development") {
    // Resolved against the page, so that any base works: "/", "/bowtie/" or a relative "./".
    return new URI(`${import.meta.env.BASE_URL}jsonschema-benchmark/data.json`).absoluteTo(window.location.href);
  }
  // segment(string) appends; segment(array) would replace the site's base path.
  return siteURI.clone().filename("").segment("jsonschema-benchmark").segment("data.json");
}

export async function fetchRealWorldData(uri: URI = realWorldDataURI()): Promise<RealWorldData> {
  const response = await fetch(uri.href());
  if (!response.ok) {
    throw new RealWorldDataError(`The benchmark results could not be loaded (${response.status} from ${uri.href()}).`);
  }
  return parseRealWorldData(await response.text());
}
