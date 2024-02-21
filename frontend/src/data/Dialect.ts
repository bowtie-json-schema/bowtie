import data from "../../../data/dialects.json";
import URI from "urijs";
import { fromSerialized, RunInfo } from "./parseReportData";

/**
 * An individual dialect of JSON Schema.
 */
export default class Dialect {
  readonly path: string;
  readonly prettyName: string;
  readonly uri: string;
  readonly firstPublicationDate: Date;

  private static all: Map<string, Dialect> = new Map<string, Dialect>();

  constructor(
    path: string,
    prettyName: string,
    uri: string,
    firstPublicationDate: Date,
  ) {
    if (Dialect.all.has(path)) {
      throw new DialectError(`A "${path}" dialect already exists.`);
    }
    Dialect.all.set(path, this);

    this.path = path;
    this.prettyName = prettyName;
    this.uri = uri;
    this.firstPublicationDate = firstPublicationDate;
  }

  async fetchReport(baseURI: URI) {
    const url = baseURI.clone().filename(this.path).suffix("json").href();
    const response = await fetch(url);
    return fromSerialized(await response.text());
  }

  async fetchPrevReportImplementations(baseURI: URI) {
    const prevVersionUrl = baseURI
      .clone()
      .directory("previous")
      .filename(this.path)
      .suffix("json")
      .href();
    const response = await fetch(prevVersionUrl);
    const jsonl = await response.text();
    const prevReportFirstLine = jsonl.trim().split(/\r?\n/)[0];
    const prevReportMetaData = JSON.parse(prevReportFirstLine) as RunInfo;
    return prevReportMetaData.implementations;
  }

  static known(): Iterable<Dialect> {
    return Dialect.all.values();
  }

  static newest_to_oldest(): Dialect[] {
    return Array.from(Dialect.known()).sort(
      (d1: Dialect, d2: Dialect) =>
        d2.firstPublicationDate.valueOf() - d1.firstPublicationDate.valueOf(),
    );
  }

  static forPath(path: string): Dialect {
    const dialect = Dialect.all.get(path);
    if (!dialect) {
      throw new DialectError(`A ${path} dialect does not exist.`);
    }
    return dialect;
  }
}

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
