import data from "../../../data/dialects.json";
import URI from "urijs";
import { parseReportData, RunInfo, ReportData } from "./parseReportData";

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
    const curVersionUrl = baseURI
      .clone()
      .filename(this.path)
      .suffix("json")
      .href();
    const response = await fetch(curVersionUrl);
    const jsonl = await response.text();
    const curReportLines = jsonl
      .trim()
      .split(/\r?\n/)
      .map((line) => JSON.parse(line) as Record<string, unknown>);

    let curReport = parseReportData(curReportLines);

    const prevVersionUrl = baseURI
      .clone()
      .directory("previous")
      .filename(this.path)
      .suffix("json")
      .href();
    const prevReportLines = await this.fetchReportMetadata(prevVersionUrl);
    if (prevReportLines) {
      const prevReportMetaData = JSON.parse(prevReportLines) as RunInfo;
      curReport = this.compareReportToOld(curReport, prevReportMetaData);
    }
    return curReport;
  }

  async fetchReportMetadata(url: string) {
    return await fetch(url)
      .then((response) => {
        if (!response?.ok || !response?.body) {
          return null;
        }
        const reader = response.body.getReader();
        let buffer = "";
        const readChunk = async (): Promise<string | null> => {
          return reader.read().then(({ value }) => {
            const chunk = new TextDecoder("utf-8").decode(value);
            const newlineIndex = chunk.indexOf("\n");
            if (newlineIndex !== -1) {
              const dataUntilNewline =
                buffer + chunk.substring(0, newlineIndex + 1);
              return dataUntilNewline;
            } else {
              buffer += chunk;
            }
            return readChunk();
          });
        };
        return readChunk();
      })
      .catch(() => {
        return null;
      });
  }

  compareReportToOld(curReport: ReportData, prevReportMetaData: RunInfo) {
    curReport.implementations.forEach((value, key) => {
      value.isNew = key in prevReportMetaData.implementations ? false : true;
    });
    return curReport;
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
