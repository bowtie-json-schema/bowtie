import data from "../../../data/dialects.json";
import { fromSerialized } from "./parseReportData";
import { siteURL } from "./Site";

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
    firstPublicationDate: Date
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

  async fetchReport(baseURL: URL = siteURL) {
    const url = new URL(this.path + ".json", baseURL.href);
    const response = await fetch(url.href);
    return fromSerialized(await response.text());
  }

  static known(): Iterable<Dialect> {
    return Dialect.all.values();
  }

  static newest_to_oldest(): Dialect[] {
    return Array.from(Dialect.known()).sort(
      (d1: Dialect, d2: Dialect) =>
        d2.firstPublicationDate.valueOf() - d1.firstPublicationDate.valueOf()
    );
  }

  static forPath(path: string): Dialect {
    const dialect = Dialect.all.get(path);
    if (!dialect) {
      throw new DialectError(`A ${path} dialect does not exist.`);
    }
    return dialect;
  }

  static forURI(uri: string): Dialect {
    const dialect = Array.from(Dialect.all.entries()).find(
      ([, dialect]) => dialect.uri === uri
    );
    if (!dialect) {
      throw new DialectError(`A ${uri} dialect does not exist.`);
    }
    return dialect[1];
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
  new Dialect(
    each.shortName,
    each.prettyName,
    each.uri,
    new Date(each.firstPublicationDate)
  );
}
