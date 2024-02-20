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
      .filename(this.path)
      .suffix("json")
      .href();

    let prevReportLines: string | null = null;
    await fetch(prevVersionUrl)
      .then(async (response) => {
        prevReportLines = await this.fetchResponseStream(response, 1);
      })
      .catch(() => {
        //  If the old report isnt available
        prevReportLines = null;
      });
    if (prevReportLines) {
      const prevReportMetaData = JSON.parse(prevReportLines) as RunInfo;
      return prevReportMetaData.implementations;
    }
    return null;
  }

  // Helper function to stream and fetch the first `num_lines`
  async fetchResponseStream(response: Response, num_lines: number) {
    if (!response?.ok || !response?.body) {
      //  If the old report isnt available
      return null;
    }
    const reader = response.body.getReader();
    let buffer = "";
    const readChunk = async (): Promise<string | null> => {
      return reader.read().then(({ value }) => {
        const chunks = new TextDecoder("utf-8").decode(value).split("\n");
        for (let chunk of chunks) {
          buffer += chunk;
          if (--num_lines == 0) return buffer;
          buffer += "\n";
        }
        return readChunk();
      });
    };
    return readChunk();
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
