import URI from "urijs";

import siteURI from "./Site";
import data from "../../../data/dialects.json";
import { fromSerialized, ReportData } from "./parseReportData";
import { fromJSON } from "./parseBenchmarkData";

/**
 * An individual dialect of JSON Schema.
 */
export default class Dialect {
  readonly shortName: string;
  readonly prettyName: string;
  readonly uri: string;
  readonly firstPublicationDate: Date;
  readonly routePath: string;
  readonly benchmarksRoutePath: string;

  private static all: Map<string, Dialect> = new Map<string, Dialect>();

  constructor(
    shortName: string,
    prettyName: string,
    uri: string,
    firstPublicationDate: Date,
  ) {
    if (Dialect.all.has(shortName)) {
      throw new DialectError(`A "${shortName}" dialect already exists.`);
    }
    Dialect.all.set(shortName, this);

    this.shortName = shortName;
    this.prettyName = prettyName;
    this.uri = uri;
    this.firstPublicationDate = firstPublicationDate;
    this.routePath = `/dialects/${shortName}`;
    this.benchmarksRoutePath = `/benchmarks/${shortName}`;
  }

  /** Sorting a dialect sorts by its publication date. */
  compare(other: Dialect): number {
    return (
      other.firstPublicationDate.getTime() - this.firstPublicationDate.getTime()
    );
  }

  async fetchReport(baseURI: URI = siteURI) {
    const url = baseURI.clone().filename(this.shortName).suffix("json").href();
    const response = await fetch(url);
    return fromSerialized(await response.text());
  }

  async fetchBenchmarkReport(baseURI: URI = siteURI) {
    const url = baseURI
      .clone()
      .directory("benchmarks")
      .filename(this.shortName)
      .suffix("json")
      .href();
    const response = await fetch(url);
    return fromJSON(await response.text());
  }

  static async fetchAllReports() {
    const allReports = new Map<Dialect, ReportData>();
    await Promise.all(
      Array.from(Dialect.known()).map(async (dialect) =>
        allReports.set(dialect, await dialect.fetchReport()),
      ),
    );
    return allReports;
  }

  static known(): Iterable<Dialect> {
    return Dialect.all.values();
  }

  static newestToOldest(): Dialect[] {
    return Array.from(Dialect.known()).sort((d1, d2) => d1.compare(d2));
  }

  static latest(): Dialect {
    return this.newestToOldest()[0];
  }

  static withName(shortName: string): Dialect {
    const dialect = Dialect.all.get(shortName);
    if (!dialect) {
      throw new DialectError(`A ${shortName} dialect does not exist.`);
    }
    return dialect;
  }

  static forURI(uri: string): Dialect {
    const dialect = Array.from(Dialect.all.values()).find(
      (dialect) => dialect.uri === uri,
    );
    if (!dialect) {
      throw new DialectError(`A ${uri} dialect does not exist.`);
    }
    return dialect;
  }
}

/**
 * Someone referred to a non-existent (unknown to Bowtie) dialect.
 */
class DialectError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DialectError";
    Object.setPrototypeOf(this, DialectError.prototype);
  }
}

for (const each of data) {
  // TODO: Replace Dialect.all so we aren't relying on side effects.
  new Dialect(
    each.shortName,
    each.prettyName,
    each.uri,
    new Date(each.firstPublicationDate),
  );
}
